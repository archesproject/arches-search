from django.utils.translation import get_language
from django.conf import settings

from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase
from arches.app.models import models as arches_models


class NodesWithWidgetLabelsForGraphAPI(APIBase):
    def get(self, request, graph_id):
        card_node_widget_rows = (
            arches_models.CardXNodeXWidget.objects.select_related("node")
            .filter(node__graph_id=graph_id)
            .order_by("node__name", "sortorder")
        )

        response_items = []
        for card_node_widget in card_node_widget_rows:
            node = card_node_widget.node
            node_dict = {
                "id": str(node.nodeid),
                "alias": node.alias,
                "name": node.name,
                "description": str(node.description or ""),
                "datatype": node.datatype,
                "graph_id": str(node.graph_id),
                "sortorder": node.sortorder,
                "config": node.config,
                "card_x_node_x_widget_label": str(card_node_widget.label or ""),
            }
            response_items.append(node_dict)

        return JSONResponse(response_items)
