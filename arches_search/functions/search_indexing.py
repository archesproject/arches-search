from arches.app.functions.base import BaseFunction
from arches.app.models.tile import Tile
from arches_search.indexing.index_from_tile import index_from_tile


class SearchIndexingFunction(BaseFunction):
    # occurrs after Tile.save
    def post_save(self, *args, **kwargs):
        tile: Tile = args[0]
        index_records = index_from_tile(tile)
        for record in index_records:
            record.save()
