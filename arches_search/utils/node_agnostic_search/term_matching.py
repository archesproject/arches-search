from django.contrib.postgres.search import SearchQuery
from django.db.models import Q

from arches.app.models.models import ResourceInstance
from arches_search.models.models import TermSearch
from arches_search.utils.node_agnostic_search.relationship_traversal import (
    expand_matches_via_relationships,
)


def build_term_match_filter(term_text, datatype=None):
    """
    Q object matching TermSearch rows whose value either full-text-matches
    term_text (stemmed, whole-lexeme) or contains it as a substring
    (backed by the existing gin_trgm_ops index on TermSearch.value).
    Pass datatype to additionally restrict matches to that TermSearch.datatype.
    """
    full_text_query = SearchQuery(term_text, search_type="plain", config="english")
    match_filter = Q(search_vector=full_text_query) | Q(value__icontains=term_text)
    if datatype is not None:
        match_filter &= Q(datatype=datatype)
    return match_filter


def get_related_resources_by_text(
    search_terms, target_graphid, max_hops=2, datatype=None
):
    """
    Matches ALL of the given terms. Each term is independently expanded via
    relationship_traversal, then intersected across terms — collapsing all terms into
    one shared seed set before expanding would let different terms qualify a resource
    via different, unrelated hop paths. Pass datatype to restrict every term's direct
    matches to that TermSearch.datatype.
    """
    result = None
    for term in search_terms:
        direct_match_ids = TermSearch.objects.filter(
            build_term_match_filter(term, datatype=datatype)
        ).values("resourceinstanceid")
        term_matches = expand_matches_via_relationships(
            direct_match_ids, target_graphid, max_hops
        )
        result = (
            term_matches
            if result is None
            else result.filter(resourceinstanceid__in=term_matches)
        )

    if result is None:
        return ResourceInstance.objects.none()
    return result
