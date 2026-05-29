from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.node_widget_labels_for_graph import (
    get_nodes_with_widget_labels_for_graph,
)


class NodesWithWidgetLabelsForGraphAPI(APIBase):
    def get(self, request, graph_id):
        return JSONResponse(get_nodes_with_widget_labels_for_graph(graph_id))
