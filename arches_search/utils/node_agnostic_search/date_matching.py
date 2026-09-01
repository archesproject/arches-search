from django.db.models import Q

from arches.app.models.models import ResourceInstance
from arches_search.models.models import DateRangeSearch, DateSearch
from arches_search.utils.node_agnostic_search.relationship_traversal import (
    expand_matches_via_relationships,
)


def get_related_resources_by_date_range(date_from, date_to, target_graphid, max_hops):
    """
    Matches DateSearch rows within [date_from, date_to] or overlapping DateRangeSearch
    rows. DateSearch.value/DateRangeSearch.start_value+end_value store a sortable
    integer encoding, not raw date strings — reuses DateSearch.normalize_operands
    (the same conversion the compiled DATE/EDTF facets use) instead of re-deriving it.
    """
    normalized_operands, _ = DateSearch.normalize_operands(
        [
            {"type": "LITERAL", "value": date_from},
            {"type": "LITERAL", "value": date_to},
        ],
        datatype_name="date",
    )
    normalized_from = normalized_operands[0]["value"]
    normalized_to = normalized_operands[1]["value"]

    date_matches = DateSearch.objects.filter(
        value__range=(normalized_from, normalized_to)
    ).values("resourceinstanceid")
    date_range_matches = DateRangeSearch.objects.filter(
        start_value__lte=normalized_to, end_value__gte=normalized_from
    ).values("resourceinstanceid")

    direct_match_ids = ResourceInstance.objects.filter(
        Q(resourceinstanceid__in=date_matches)
        | Q(resourceinstanceid__in=date_range_matches)
    ).values("resourceinstanceid")
    return expand_matches_via_relationships(direct_match_ids, target_graphid, max_hops)
