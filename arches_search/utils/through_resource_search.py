from django.contrib.postgres.search import SearchQuery
from django.db.models import Q

from arches.app.models.models import (
    ResourceInstance,
    ResourceXResource,
)

from arches_search.models.models import TermSearch


def get_related_resources_by_text(search_terms, target_graphid):
    """
    Returns a queryset of (resourceinstanceid,) tuples for resources of
    target_graphid that match ALL of the given search terms, following
    up to 2 hops through resource_x_resource from text-matching resources.
    """
    result = None

    for term in search_terms:
        sq = SearchQuery(term, search_type="plain")

        # Resources matching this search term (any graph)
        initial_match_ids = TermSearch.objects.filter(search_vector=sq).values(
            "resourceinstanceid"
        )

        # Non-target-graph resources among the initial matches
        non_matching_initial = (
            ResourceInstance.objects.filter(resourceinstanceid__in=initial_match_ids)
            .exclude(graph_id=target_graphid)
            .values("resourceinstanceid")
        )

        # First-level: target-graph resources 1 hop from non-matching initial
        fl_targets_from = ResourceXResource.objects.filter(
            to_resource__in=non_matching_initial,
            from_resource_graph_id=target_graphid,
        ).values("from_resource_id")

        fl_targets_to = ResourceXResource.objects.filter(
            from_resource__in=non_matching_initial,
            to_resource_graph_id=target_graphid,
        ).values("to_resource_id")

        # Non-matching first-level resources (to traverse for second level)
        non_matching_fl_from = (
            ResourceXResource.objects.filter(
                to_resource__in=non_matching_initial,
            )
            .exclude(from_resource_graph_id=target_graphid)
            .values("from_resource_id")
        )

        non_matching_fl_to = (
            ResourceXResource.objects.filter(
                from_resource__in=non_matching_initial,
            )
            .exclude(to_resource_graph_id=target_graphid)
            .values("to_resource_id")
        )

        # Second-level: target-graph resources 2 hops away, through non-matching
        # first-level resources (both traversal directions × both entry directions)
        sl_targets_a = ResourceXResource.objects.filter(
            to_resource__in=non_matching_fl_from,
            from_resource_graph_id=target_graphid,
        ).values("from_resource_id")

        sl_targets_b = ResourceXResource.objects.filter(
            from_resource__in=non_matching_fl_from,
            to_resource_graph_id=target_graphid,
        ).values("to_resource_id")

        sl_targets_c = ResourceXResource.objects.filter(
            to_resource__in=non_matching_fl_to,
            from_resource_graph_id=target_graphid,
        ).values("from_resource_id")

        sl_targets_d = ResourceXResource.objects.filter(
            from_resource__in=non_matching_fl_to,
            to_resource_graph_id=target_graphid,
        ).values("to_resource_id")

        # All target-graph resources matching this term (direct + 1-hop + 2-hop)
        term_matches = ResourceInstance.objects.filter(
            Q(resourceinstanceid__in=initial_match_ids, graph_id=target_graphid)
            | Q(resourceinstanceid__in=fl_targets_from)
            | Q(resourceinstanceid__in=fl_targets_to)
            | Q(resourceinstanceid__in=sl_targets_a)
            | Q(resourceinstanceid__in=sl_targets_b)
            | Q(resourceinstanceid__in=sl_targets_c)
            | Q(resourceinstanceid__in=sl_targets_d)
        )

        # AND semantics: intersect results across all terms
        if result is None:
            result = term_matches
        else:
            result = result.filter(resourceinstanceid__in=term_matches)

    if result is None:
        return ResourceInstance.objects.none()

    return result
