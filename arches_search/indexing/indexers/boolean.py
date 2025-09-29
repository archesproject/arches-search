from django.contrib.postgres.search import SearchVector
from arches.app.datatypes.datatypes import DataTypeFactory
from arches_search.models.models import BooleanSearch

from arches_search.indexing.base import BaseIndexing


class BooleanIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("boolean")

    def index(self, tile, node):
        nodeid = str(node.nodeid)
        boolean_value = tile.data.get(nodeid, None)
        if boolean_value is not None:
            boolean_search = BooleanSearch.objects.create(
                node_alias=node.alias,
                tileid=tile.tileid,
                resourceinstanceid=tile.resourceinstance_id,
                datatype=self.datatype.datatype_name,
                graph_alias=node.graph.slug,
                value=boolean_value,
            )
            boolean_search.save()
