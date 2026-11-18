from django.contrib.postgres.search import SearchQuery
from django.db.models import BooleanField, Exists, F, Func, OuterRef, Q, Value

from arches.app.models.models import ResourceInstance
from arches_search.models.models import TermSearch, UUIDSearch
from arches_search.utils.term_search.relationship_expansion import (
    expand_matches_via_relationships,
)
from arches_search.utils.vocabulary_hierarchy import NARROWER_OR_SELF, expand_branch

ROW_DATATYPES_BY_TERM_DATATYPE = {
    "reference": ["reference"],
    "concept": ["concept", "concept-list"],
}


def _contains_ignoring_case(term_text):
    """
    `value ILIKE '%term%'`. Unlike icontains (UPPER(value) LIKE UPPER(...)), this is
    served by the gin_trgm_ops index on TermSearch.value and can be BitmapOr'd
    with the search_vector match.
    """
    escaped_term = (
        term_text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )
    return Func(
        F("value"),
        Value(f"%{escaped_term}%"),
        arg_joiner=" ILIKE ",
        template="(%(expressions)s)",
        output_field=BooleanField(),
    )


def build_term_match_filter(term_text):
    """
    Q object matching TermSearch rows whose value either full-text-matches
    term_text (stemmed, whole-lexeme) or contains it as a substring
    (backed by the existing gin_trgm_ops index on TermSearch.value).
    """
    full_text_query = SearchQuery(term_text, search_type="plain", config="english")
    return Q(search_vector=full_text_query) | Q(_contains_ignoring_case(term_text))


def _direct_match_rows(term):
    if isinstance(term, str):
        return TermSearch.objects.filter(build_term_match_filter(term))
    datatype = term.get("datatype")
    row_datatypes = ROW_DATATYPES_BY_TERM_DATATYPE.get(datatype, [datatype])
    if term.get("id"):
        return UUIDSearch.objects.filter(
            datatype__in=row_datatypes,
            value__in=expand_branch(datatype, NARROWER_OR_SELF, [term["id"]]),
        )
    rows = TermSearch.objects.filter(build_term_match_filter(term["text"]))
    if datatype is None:
        return rows
    return rows.filter(datatype__in=row_datatypes)


def get_related_resources_by_terms(terms, target_graphid, readable_nodes, max_hops=2):
    """
    Matches ALL of the given terms. Each term is independently expanded via
    relationship_traversal, then intersected across terms — collapsing all terms into
    one shared seed set before expanding would let different terms qualify a resource
    via different, unrelated hop paths.

    Values of nodes the user cannot read never match.
    """
    result = None
    for term in terms:
        direct_match_ids = readable_nodes.exclude_unreadable_rows(
            _direct_match_rows(term)
        ).values("resourceinstanceid")
        term_matches = expand_matches_via_relationships(
            direct_match_ids, target_graphid, max_hops, readable_nodes
        )
        if isinstance(term, dict) and term.get("inverted"):
            candidate_resources = result
            if candidate_resources is None:
                candidate_resources = ResourceInstance.objects.filter(
                    graph_id=target_graphid
                )
            result = candidate_resources.filter(
                ~Exists(term_matches.filter(resourceinstanceid=OuterRef("pk")))
            )
        else:
            result = (
                term_matches
                if result is None
                else result.filter(resourceinstanceid__in=term_matches)
            )

    if result is None:
        return ResourceInstance.objects.none()
    return result
