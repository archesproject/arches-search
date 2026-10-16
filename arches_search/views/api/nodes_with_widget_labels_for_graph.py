from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search.metadata.node_widget_labels_for_graph import (
    get_nodes_with_widget_labels_for_graph,
)
from arches_search.utils.readable_nodes import ReadableNodes


class NodesWithWidgetLabelsForGraphAPI(APIBase):
    def get(self, request, graph_id):
        return JSONResponse(
            get_nodes_with_widget_labels_for_graph(
                graph_id, ReadableNodes(request.user)
            )
        )
