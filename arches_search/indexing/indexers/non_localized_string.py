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
        for string_object in document["strings"]:
            term_search = TermSearch.objects.create(
                node_alias=node.alias,
                tileid=tile.tileid,
                resourceinstanceid=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_alias=node.graph.slug,
                value=string_object["string"],
            )
            term_search.save()
            term_search.search_vector = SearchVector("value", config="simple")
            TermSearch.objects.filter(pk=term_search.pk).update(
                search_vector=term_search.search_vector
            )
