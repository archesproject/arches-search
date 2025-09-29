from django.contrib.postgres.search import SearchVector
from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches_search.models.models import DateSearch

from arches_search.indexing.base import BaseIndexing


class DateIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance("date")

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        document = {"dates": [], "date_ranges": []}
        self.datatype.append_to_document(document, tile.data[nodeid], node, tile)
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
