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
    def get_nodegroup(nodegroup_id):
        return Node.objects.filter(nodegroup_id=nodegroup_id).select_related("graph")

    if nodegroup_cache is None:
        nodes = get_nodegroup(tile.nodegroup_id)
    elif tile.nodegroup_id in nodegroup_cache:
        nodes = nodegroup_cache[tile.nodegroup_id]
    else:
        nodegroup_cache[tile.nodegroup_id] = get_nodegroup(tile.nodegroup_id)
        nodes = nodegroup_cache[tile.nodegroup_id]

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
    for node in nodes:
        if (
            node.graph.slug == "arches_system_settings"
            or str(node.graph.graphid) == "ff623370-fa12-11e6-b98b-6c4008b05c4c"
        ):
            break
        nodeid = str(node.nodeid)
        if nodeid in tile.data.keys():
            if tile.data[nodeid] is None:
                continue

            indexer = factory.get_indexing_class(node.datatype)
            indexer.index(tile, node)
