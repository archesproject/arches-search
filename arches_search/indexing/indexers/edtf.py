from django.contrib.postgres.search import SearchVector
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
        for date in document["dates"]:
            date_search = DateSearch.objects.create(
                node_alias=node.alias,
                tileid=tile.tileid,
                resourceinstanceid=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_alias=node.graph.slug,
                value=date["date"],
            )
            date_search.save()

        for date_range in document["date_ranges"]:
            date_range_search = DateRangeSearch.objects.create(
                node_alias=node.alias,
                tileid=tile.tileid,
                resourceinstanceid=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_alias=node.graph.slug,
                start_date=date_range["date_range"]["lte"],
                end_date=date_range["date_range"]["gte"],
            )
            date_range_search.save()
