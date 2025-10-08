from django.contrib.postgres.search import SearchVector
from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches.app.models.models import Language
from arches_search.models.models import TermSearch, UUIDSearch

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
        for string in document["strings"]:
            string_search = TermSearch.objects.create(
                node_alias=node.alias,
                tileid=tile.tileid,
                resourceinstanceid=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_alias=node.graph.slug,
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
        
        for concept in document["domains"]:
            for id in [concept["conceptid"], concept["valueid"]]:
                uuid_search = UUIDSearch.objects.create(
                    node_alias=node.alias,
                    tileid=tile.tileid,
                    resourceinstanceid=tile.resourceinstance_id,
                    datatype=self.datatype.datatype_name,
                    graph_alias=node.graph.slug,
                    value=id,
                )
                uuid_search.save()

