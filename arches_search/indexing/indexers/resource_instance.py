from django.contrib.postgres.search import SearchVector
from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches_search.models.models import TermSearch, UUIDSearch

from arches_search.indexing.base import BaseIndexing


class ResourceInstanceIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance(
            "resource-instance"
        )

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        document = {"strings": [], "ids": []}
        self.datatype.append_to_document(document, tile.data[nodeid], node, tile)
        search_items = []
        for string in document["strings"]:
            string_search = TermSearch(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                value=string["string"],
            )
            search_items.append(string_search)

        for related_resource_id in document["ids"]:
            uuid_search = UUIDSearch(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                value=related_resource_id["id"],
            )
            search_items.append(uuid_search)
        return search_items
