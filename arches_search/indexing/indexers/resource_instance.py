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
        for string in document["strings"]:
            string_search = TermSearch.objects.create(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                value=string["string"],
            )
            string_search.save()
            string_search.search_vector = SearchVector(
                "value",
                config="simple",
            )
            TermSearch.objects.filter(pk=string_search.pk).update(
                search_vector=string_search.search_vector
            )

        for related_resource_id in document["ids"]:
            uuid_search = UUIDSearch.objects.create(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                value=related_resource_id["id"],
            )
            uuid_search.save()
