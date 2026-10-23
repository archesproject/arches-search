from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches_search.models.models import TermSearch, UUIDSearch

from arches_search.indexing.base import BaseIndexing


class ReferenceIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance("reference")

    def sort_row_filters(self) -> dict:
        """Sort by the preferred label, not by an alternate one."""
        return {"valuetype": "prefLabel"}

    def index(self, tile, node):
        """
        A row per label, carrying the language and valuetype it declares.

        Read from the tile rather than through append_to_document(), which
        flattens labels to bare strings and so loses both.
        """
        search_items = []

        for reference in tile.data[str(node.nodeid)]:
            for label in reference["labels"]:
                if label["value"] is not None:
                    search_items.append(
                        TermSearch(
                            node_alias=node.alias,
                            tileid_id=tile.tileid,
                            resourceinstanceid_id=tile.resourceinstance_id,
                            datatype=self.datatype.datatype_name,
                            graph_slug=node.graph.slug,
                            language=label["language_id"],
                            valuetype=label["valuetype_id"],
                            value=label["value"],
                        )
                    )

                if label["id"] is not None:
                    search_items.append(
                        UUIDSearch(
                            node_alias=node.alias,
                            tileid_id=tile.tileid,
                            resourceinstanceid_id=tile.resourceinstance_id,
                            datatype=self.datatype.datatype_name,
                            graph_slug=node.graph.slug,
                            value=label["id"],
                        )
                    )

        return search_items
