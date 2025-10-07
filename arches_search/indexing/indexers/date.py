from arches.app.utils.date_utils import ExtendedDateFormat
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
        date_value = tile.data[nodeid]
        date_components = date_value.split("-")
        if len(date_components[0]) == 4 and len(date_components) == 3:
            # date parsing with the edtf library is slow, so for known
            # formats (like date) we can speed it up with this
            self._short_circuit_date(document, date_components, nodeid, node, tile)
        else:
            self.datatype.append_to_document(document, tile.data[nodeid], node, tile)
        for date in document["dates"]:
            date_search = DateSearch.objects.create(
                node_alias=node.alias,
                tileid=tile.tileid,
                resourceinstanceid=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_slug=node.graph.slug,
                value=date["date"],
            )
            date_search.save()

    def _short_circuit_date(self, document, date_components, nodeid, node, tile):

        year = int(date_components[0])
        month = int(date_components[1])
        day = int(date_components[2])
        edtf = ExtendedDateFormat()
        date_int = edtf.to_sortable_date(year, month, day)

        document["dates"].append(
            {
                "date": date_int,
                "nodegroup_id": tile.nodegroup_id,
                "nodeid": nodeid,
                "provisional": tile.provisionaledits,
            }
        )
