from arches.app.models.models import ResourceInstance
from arches_search.models.models import GeometrySearch
from arches_search.utils.geo_utils import GeoUtils
from arches_search.utils.node_agnostic_search.relationship_traversal import (
    expand_matches_via_relationships,
)


def get_related_resources_by_geometry(feature_collection, target_graphid, max_hops):
    """
    feature_collection: a GeoJSON FeatureCollection, each feature optionally carrying
    properties.buffer_distance/buffer_units. Unioned into one geometry via GeoUtils
    (which also applies buffering) before intersecting — a FeatureCollection itself
    isn't a valid geom__intersects operand.
    """
    union_geometry = GeoUtils().map_filter_to_union(feature_collection)
    if union_geometry is None:
        return ResourceInstance.objects.none()

    direct_match_ids = GeometrySearch.objects.filter(
        geom__intersects=union_geometry
    ).values("resourceinstanceid")
    return expand_matches_via_relationships(direct_match_ids, target_graphid, max_hops)
