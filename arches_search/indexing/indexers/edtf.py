from arches.app.datatypes.datatypes import DataTypeFactory
from arches_search.models.models import DateSearch, DateRangeSearch

from arches_search.indexing.base import BaseIndexing


class EDTFIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("edtf")

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        document = {"dates": [], "date_ranges": []}
        self.datatype.append_to_document(document, tile.data[nodeid], nodeid, tile)
        search_items = []
        for date in document["dates"]:
            date_search = DateSearch(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                value=date["date"],
            )
            search_items.append(date_search)

        for date_range in document["date_ranges"]:
            date_range_search = DateRangeSearch(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                start_value=date_range["date_range"]["lte"],
                end_value=date_range["date_range"]["gte"],
            )
            search_items.append(date_range_search)

        return search_items
