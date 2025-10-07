from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models.models import Language
from arches_search.models.models import NumericSearch

from arches_search.indexing.base import BaseIndexing


class NumberIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.languages: dict[str, Language] = {}
        self.datatype = DataTypeFactory().get_instance("number")

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        document = {"numbers": [], "strings": []}
        self.datatype.append_to_document(document, tile.data[nodeid], node, tile)
        for number_object in document["numbers"]:
            numeric_search = NumericSearch.objects.create(
                node_alias=node.alias,
                tileid=tile.tileid,
                resourceinstanceid=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                value=number_object["number"],
            )
            numeric_search.save()
