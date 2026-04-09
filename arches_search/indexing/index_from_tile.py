from django.db.models import Q
from arches.app.models.models import Node
from arches_search.indexing.indexing_factory import IndexingFactory
from arches_search.models.models import (
    BooleanSearch,
    DateRangeSearch,
    DateSearch,
    FileListSearch,
    GeometrySearch,
    NumericSearch,
    TermSearch,
)

def _get_nodegroup(nodegroup_id):
    return Node.objects.filter(
        Q(nodegroup_id=nodegroup_id)
        & ~Q(graph__slug="arches_system_settings")
    ).select_related("graph")


def index_from_tile(
    tile, delete_existing=True, indexing_factory=None, nodegroup_cache=None
):
    if nodegroup_cache is None:
        nodegroup_cache = {}
    if tile.nodegroup_id not in nodegroup_cache:
        nodegroup_cache[tile.nodegroup_id] = _get_nodegroup(tile.nodegroup_id)
    nodes = nodegroup_cache[tile.nodegroup_id]

    if delete_existing:
        TermSearch.objects.filter(tileid=tile.tileid).delete()
        DateSearch.objects.filter(tileid=tile.tileid).delete()
        DateRangeSearch.objects.filter(tileid=tile.tileid).delete()
        BooleanSearch.objects.filter(tileid=tile.tileid).delete()
        NumericSearch.objects.filter(tileid=tile.tileid).delete()
        GeometrySearch.objects.filter(tileid=tile.tileid).delete()
        FileListSearch.objects.filter(tileid=tile.tileid).delete()

    if indexing_factory is None:
        factory = IndexingFactory()
    else:
        factory = indexing_factory

    if nodegroup_cache is None:
        nodes = Node.objects.filter(nodegroup_id=tile.nodegroup_id)
        nodegroup_cache = {tile.nodegroup_id: list(nodes)}

    result = []
    for node in nodes:
        nodeid = str(node.nodeid)
        if nodeid in tile.data:
            if tile.data[nodeid] is None:
                continue

            indexer = factory.get_indexing_class(node.datatype)
            res = indexer.index(tile, node)
            if res:
                result.extend(res)
    return result
