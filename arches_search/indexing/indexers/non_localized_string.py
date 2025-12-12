from django.contrib.postgres.search import SearchVector
from arches.app.datatypes.datatypes import DataTypeFactory
from arches_search.models.models import TermSearch

from arches_search.indexing.base import BaseIndexing


class NonLocalizedStringIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("non-localized-string")

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        document = {"strings": []}
        self.datatype.append_to_document(document, tile.data[nodeid], node, tile)
        search_items = []
        for string_object in document["strings"]:
            term_search = TermSearch(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                value=string_object["string"],
            )
            search_items.append(term_search)
        return search_items
