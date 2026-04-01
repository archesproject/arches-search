from pathlib import Path

from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches.app.models.models import Language
from arches_search.models.models import FileListSearch, TermSearch

from arches_search.indexing.base import BaseIndexing


class FileListIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance("file-list")
        self.languages: dict[str, Language] = {}

    def _set_languages(self):
        if not self.languages:
            for l_obj in Language.objects.all():
                self.languages[l_obj.code] = l_obj

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        self._set_languages()
        document = {"strings": []}
        self.datatype.append_to_document(document, tile.data[nodeid], nodeid, tile)
        search_items = []
        for string in document["strings"]:
            if string["string"] is not None:
                string_search = TermSearch(
                    node_alias=node.alias,
                    tileid_id=tile.tileid,
                    resourceinstanceid_id=tile.resourceinstance_id,
                    datatype=self.datatype.datatype_name,
                    language=string["language"] if "language" in string else "",
                    graph_slug=node.graph.slug,
                    value=string["string"],
                )
                search_items.append(string_search)

        file_items = tile.data.get(nodeid) or []
        if not isinstance(file_items, list):
            return search_items

        for file_item in file_items:
            if not isinstance(file_item, dict):
                continue

            file_name = file_item.get("name")
            extension = None
            if file_name:
                extension = Path(file_name).suffix.lstrip(".").lower() or None

            search_items.append(
                FileListSearch(
                    node_alias=node.alias,
                    tileid_id=tile.tileid,
                    resourceinstanceid_id=tile.resourceinstance_id,
                    datatype=self.datatype.datatype_name,
                    graph_slug=node.graph.slug,
                    value=file_name or None,
                    extension=extension,
                    file_size=file_item.get("size"),
                    modified_at=file_item.get("lastModified"),
                )
            )

        return search_items
