from arches.app.functions.base import BaseFunction
from arches.app.models.tile import Tile
from arches_search.indexing.index_from_tile import index_from_tile


class SearchIndexingFunction(BaseFunction):
    # occurs after Tile.save
    def post_save(self, *args, **kwargs):
        tile: Tile = args[0]
        nodegroup_cache = kwargs.get("nodegroup_cache", {})
        index_records = index_from_tile(tile, nodegroup_cache=nodegroup_cache)
        for record in index_records:
            record.save()
