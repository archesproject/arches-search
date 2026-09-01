import functools
import operator

from django.db.models import Q

from arches.app.models.models import ResourceInstance, ResourceXResource

MAX_ALLOWED_HOPS = 2


def expand_matches_via_relationships(direct_match_resource_ids, target_graphid, max_hops):
    """
    Returns target_graphid resources that are themselves in direct_match_resource_ids
    (any graph), or reachable from one within max_hops via resource_x_resource.
    """
    if not 0 <= max_hops <= MAX_ALLOWED_HOPS:
        raise ValueError(f"max_hops must be between 0 and {MAX_ALLOWED_HOPS}")

    target_graph_match_sets = [
        ResourceInstance.objects.filter(
            resourceinstanceid__in=direct_match_resource_ids, graph_id=target_graphid
        ).values("resourceinstanceid")
    ]
    traversal_frontier = (
        ResourceInstance.objects.filter(resourceinstanceid__in=direct_match_resource_ids)
        .exclude(graph_id=target_graphid)
        .values("resourceinstanceid")
    )

    for hop_number in range(max_hops):
        target_graph_match_sets.append(
            ResourceXResource.objects.filter(
                to_resource__in=traversal_frontier, from_resource_graph_id=target_graphid
            ).values("from_resource_id")
        )
        target_graph_match_sets.append(
            ResourceXResource.objects.filter(
                from_resource__in=traversal_frontier, to_resource_graph_id=target_graphid
            ).values("to_resource_id")
        )
        if hop_number < max_hops - 1:
            next_frontier_from = (
                ResourceXResource.objects.filter(to_resource__in=traversal_frontier)
                .exclude(from_resource_graph_id=target_graphid)
                .values("from_resource_id")
            )
            next_frontier_to = (
                ResourceXResource.objects.filter(from_resource__in=traversal_frontier)
                .exclude(to_resource_graph_id=target_graphid)
                .values("to_resource_id")
            )
            traversal_frontier = ResourceInstance.objects.filter(
                Q(resourceinstanceid__in=next_frontier_from)
                | Q(resourceinstanceid__in=next_frontier_to)
            ).values("resourceinstanceid")

    return ResourceInstance.objects.filter(
        functools.reduce(
            operator.or_,
            (Q(resourceinstanceid__in=match_set) for match_set in target_graph_match_sets),
        )
    )
