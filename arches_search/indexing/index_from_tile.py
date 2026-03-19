from django.db.models import Q
from arches.app.models.models import Node
from arches_search.indexing.indexing_factory import IndexingFactory
from arches_search.models.models import (
    TermSearch,
    DateSearch,
    DateRangeSearch,
    BooleanSearch,
    NumericSearch,
)


def index_from_tile(
    tile, delete_existing=True, indexing_factory=None, nodegroup_cache=None
):

    if delete_existing:
        TermSearch.objects.filter(tileid=tile.tileid).delete()
        DateSearch.objects.filter(tileid=tile.tileid).delete()
        DateRangeSearch.objects.filter(tileid=tile.tileid).delete()
        BooleanSearch.objects.filter(tileid=tile.tileid).delete()
        NumericSearch.objects.filter(tileid=tile.tileid).delete()

    if indexing_factory is None:
        factory = IndexingFactory()
    else:
        factory = indexing_factory
    result = []
    for node in nodegroup_cache[tile.nodegroup_id]:
        nodeid = str(node.nodeid)
        if nodeid in tile.data:
            if tile.data[nodeid] is None:
                continue

            indexer = factory.get_indexing_class(node.datatype)
            res = indexer.index(tile, node)
            if res:
                result.extend(res)
    return result
