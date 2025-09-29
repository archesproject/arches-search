from arches.app.functions.base import BaseFunction
from arches.app.models.tile import Tile
from arches.app.models.models import Node
from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches_search.indexing.indexing_factory import IndexingFactory
from arches_search.models.models import TermSearch, DateSearch, DateRangeSearch


def index_from_tile(tile):
    nodes = Node.objects.filter(nodegroup_id=tile.nodegroup_id).select_related("graph")
    TermSearch.objects.filter(tileid=tile.tileid).delete()
    DateSearch.objects.filter(tileid=tile.tileid).delete()
    DateRangeSearch.objects.filter(tileid=tile.tileid).delete()
    factory = IndexingFactory()
    for node in nodes:
        if node.graph.slug == "arches_system_settings":
            continue
        nodeid = str(node.nodeid)
        if nodeid in tile.data.keys():
            if tile.data[nodeid] is None:
                continue

            indexer = factory.get_indexing_class(node.datatype)
            indexer.index(tile, node)
