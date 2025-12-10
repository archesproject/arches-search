from django.contrib.postgres.search import SearchVector
from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches.app.models.models import Language
from arches_search.models.models import DateRangeSearch, TermSearch, UUIDSearch

from arches_search.indexing.base import BaseIndexing


class ConceptIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance("concept")
        self.languages: dict[str, Language] = {}

    def _set_languages(self):
        if not self.languages:
            for l_obj in Language.objects.all():
                self.languages[l_obj.code] = l_obj

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        document = {"domains": [], "strings": [], "date_ranges": []}
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

        for concept in document["domains"]:
            for id in [concept["conceptid"], concept["valueid"]]:
                uuid_search = UUIDSearch(
                    node_alias=node.alias,
                    tileid=tile.tileid,
                    resourceinstanceid=tile.resourceinstance_id,
                    datatype=self.datatype.datatype_name,
                    graph_slug=node.graph.slug,
                    value=id,
                )
                search_items.append(uuid_search)

        for concept in document["date_ranges"]:
            date_range_search = DateRangeSearch(
                node_alias=node.alias,
                tileid=tile.tileid,
                resourceinstanceid=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                start_value=concept["date_range"]["gte"],
                end_value=concept["date_range"]["lte"],
            )
            search_items.append(date_range_search)

        return search_items
