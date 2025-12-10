from django.contrib.postgres.search import SearchVector
from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches.app.models.models import Language
from arches_search.models.models import TermSearch, UUIDSearch

from arches_search.indexing.base import BaseIndexing


class ReferenceIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance("reference")
        self.languages: dict[str, Language] = {}

    def _set_languages(self):
        if not self.languages:
            for l_obj in Language.objects.all():
                self.languages[l_obj.code] = l_obj

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        self._set_languages()
        document = {"strings": [], "references": []}
        self.datatype.append_to_document(document, tile.data[nodeid], node, tile)
        search_items = []
        for string in document["strings"]:
            string_search = TermSearch(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                language=node.config.lang,
                value=string["string"],
            )
            search_items.append(string_search)

        for reference in document["references"]:
            uuid_search = UUIDSearch(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                value=reference["id"],
            )
            search_items.append(uuid_search)

        return search_items
