"""
Shape checks for the search payload, run before anything compiles.

Each advanced search payload validates itself as it compiles, where the
registries are available; what is checked here is the shape of the keys around
them.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches_search.utils.term_search.relationship_expansion import MAX_ALLOWED_HOPS

MAX_PAGE_SIZE = 200


def _positive_integer(value) -> bool:
    # bool is an int subclass, and True would otherwise pass as page 1.
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def validate_paging(page, page_size) -> None:
    """
    Checked here so bad paging is a 400. Left to Paginator, a non-integer page
    raises PageNotAnInteger and page_size 0 raises ZeroDivisionError -- neither
    is a ValidationError, so both would surface as a 500.
    """
    if not _positive_integer(page):
        raise ValidationError(_("page must be a positive integer."))

    if not _positive_integer(page_size) or page_size > MAX_PAGE_SIZE:
        raise ValidationError(
            _("page_size must be an integer between 1 and %(max)s.")
            % {"max": MAX_PAGE_SIZE}
        )


def validate_term_search(term_search):
    """
    One object, not a list of typed entries.

    The geometry and date filters that used to sit beside this are advanced
    search clauses now, so there is nothing left to discriminate between.
    """
    if term_search is None:
        return

    if not isinstance(term_search, dict):
        raise ValidationError(_("term_search must be an object."))

    terms = term_search.get("terms")
    if not isinstance(terms, list) or not all(
        isinstance(term, str) and term for term in terms
    ):
        raise ValidationError(
            _("term_search terms must be a list of non-empty strings.")
        )

    max_hops = term_search.get("max_hops", 0)
    if (
        not isinstance(max_hops, int)
        or isinstance(max_hops, bool)
        or not (0 <= max_hops <= MAX_ALLOWED_HOPS)
    ):
        raise ValidationError(
            _("term_search max_hops must be an integer between 0 and %(max)s.")
            % {"max": MAX_ALLOWED_HOPS}
        )


def validate_advanced_search_queries(advanced_search_queries):
    """
    Check the shape of the list itself; each entry is validated as it compiles.

    Two entries for one graph would mean one of them is silently ignored, so
    that is rejected rather than resolved by ordering.
    """
    if advanced_search_queries is None:
        return

    if not isinstance(advanced_search_queries, list):
        raise ValidationError(
            _("advanced_search_queries must be a list of advanced search payloads.")
        )

    seen_graph_slugs = set()
    for index, graph_payload in enumerate(advanced_search_queries):
        if not isinstance(graph_payload, dict):
            raise ValidationError(
                _("advanced_search_queries[%(index)s] must be an object."),
                params={"index": index},
            )

        graph_slug = graph_payload.get("graph_slug")
        if graph_slug in seen_graph_slugs:
            raise ValidationError(
                _(
                    "advanced_search_queries has more than one entry for graph "
                    "%(graph_slug)s; each graph may be addressed once."
                ),
                params={"graph_slug": graph_slug},
            )
        seen_graph_slugs.add(graph_slug)


def validate_search_payload(search_payload) -> None:
    """
    Every check that applies to the filtering half of a request.

    Grouped so the endpoints that compile a payload without running a whole
    search -- the export, the map tiles -- cannot drift out of step with the
    search endpoint on what they accept.
    """
    validate_term_search(search_payload.term_search)
    validate_advanced_search_queries(search_payload.advanced_search_queries)
