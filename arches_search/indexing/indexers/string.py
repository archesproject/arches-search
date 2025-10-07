from django.db.models import Value
from django.contrib.postgres.search import SearchVector
from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models.models import Language
from arches_search.models.models import TermSearch

from arches_search.indexing.base import BaseIndexing


class StringIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.languages: dict[str, Language] = {}
        self.datatype = DataTypeFactory().get_instance("string")

    def _set_languages(self):
        if not self.languages:
            for l_obj in Language.objects.all():
                self.languages[l_obj.code] = l_obj

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        self._set_languages()
        document = {"strings": []}
        self.datatype.append_to_document(document, tile.data[nodeid], node, tile)
        for string_object in document["strings"]:
            term_search = TermSearch.objects.create(
                node_alias=node.alias,
                tileid=tile.tileid,
                resourceinstanceid=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                language=string_object["language"],
                graph_slug=node.graph.slug,
                value=string_object["string"],
            )
            term_search.search_vector = SearchVector(
                Value(string_object["string"]),
                config=self.languages[string_object["language"]].name.lower(),
            )
            term_search.save()
