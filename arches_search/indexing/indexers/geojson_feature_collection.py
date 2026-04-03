import json

from django.contrib.gis.geos import GEOSGeometry
from arches.app.datatypes.datatypes import DataTypeFactory
from arches_search.models.models import GeometrySearch
from arches_search.indexing.base import BaseIndexing


class GeoJSONFeatureCollectionIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("geojson-feature-collection")

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        feature_collection = tile.data.get(nodeid)
        if not feature_collection:
            return []

        search_items = []
        for feature in feature_collection.get("features", []):
            geometry = feature.get("geometry")
            if geometry is None:
                continue
            try:
                geom = GEOSGeometry(json.dumps(geometry), srid=4326)
            except Exception:
                continue
            search_items.append(
                GeometrySearch(
                    node_alias=node.alias,
                    tileid_id=tile.tileid,
                    resourceinstanceid_id=tile.resourceinstance_id,
                    datatype=self.datatype.datatype_name,
                    graph_slug=node.graph.slug,
                    geom=geom,
                )
            )

        return search_items
