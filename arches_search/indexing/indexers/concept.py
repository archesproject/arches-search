from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches_search.models.models import DateRangeSearch, TermSearch, UUIDSearch

from arches_search.indexing.base import BaseIndexing


class ConceptIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance("concept")

    def sort_row_filters(self) -> dict:
        """Sort by the preferred label, not by an alternate one."""
        return {"valuetype": "prefLabel"}

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        document = {"domains": [], "strings": [], "date_ranges": []}
        self.datatype.append_to_document(document, tile.data[nodeid], node, tile)
        search_items = []

        for valueid in self.datatype.get_nodevalues(tile.data[nodeid]):
            concept_value = self.datatype.get_value(valueid)
            string_search = TermSearch(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                language=concept_value.language_id or "",
                valuetype=concept_value.valuetype_id,
                value=concept_value.value,
            )
            search_items.append(string_search)

        for concept in document["domains"]:
            for id in [concept["conceptid"], concept["valueid"]]:
                if id is not None:
                    uuid_search = UUIDSearch(
                        node_alias=node.alias,
                        tileid_id=tile.tileid,
                        resourceinstanceid_id=tile.resourceinstance_id,
                        datatype=self.datatype.datatype_name,
                        graph_slug=node.graph.slug,
                        value=id,
                    )
                    search_items.append(uuid_search)

        for concept in document["date_ranges"]:
            if (
                concept["date_range"]["gte"] is not None
                and concept["date_range"]["lte"] is not None
            ):
                date_range_search = DateRangeSearch(
                    node_alias=node.alias,
                    tileid_id=tile.tileid,
                    resourceinstanceid_id=tile.resourceinstance_id,
                    datatype=self.datatype.datatype_name,
                    graph_slug=node.graph.slug,
                    start_value=concept["date_range"]["gte"],
                    end_value=concept["date_range"]["lte"],
                )
                search_items.append(date_range_search)

        return search_items
