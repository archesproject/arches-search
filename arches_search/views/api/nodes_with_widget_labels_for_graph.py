from django.db import models

from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase
from arches.app.models import models as arches_models


class NodesWithWidgetLabelsForGraphAPI(APIBase):
    def get(self, request, graph_id):
        edges = arches_models.Edge.objects.filter(graph_id=graph_id).select_related(
            "domainnode", "rangenode"
        )

        semantic_parent_map = {}
        for edge in edges:
            if edge.rangenode_id and edge.domainnode:
                semantic_parent_map[edge.rangenode_id] = edge.domainnode

        nodes = (
            arches_models.Node.objects.filter(graph_id=graph_id)
            .order_by("sortorder", "name")
            .select_related("nodegroup")
            .prefetch_related(
                models.Prefetch(
                    "cardxnodexwidget_set",
                    queryset=arches_models.CardXNodeXWidget.objects.select_related(
                        "card"
                    ).order_by("sortorder"),
                )
            )
        )

        node_items = []

        for node in nodes:
            semantic_parent = semantic_parent_map.get(node.nodeid)
            semantic_parent_id = (
                str(semantic_parent.nodeid) if semantic_parent else None
            )

            nodegroup = getattr(node, "nodegroup", None)
            nodegroup_cardinality = (
                str(nodegroup.cardinality).strip().lower()
                if nodegroup and nodegroup.cardinality is not None
                else None
            )
            nodegroup_has_cardinality_n = nodegroup_cardinality == "n"

            card_node_widget_rows = list(node.cardxnodexwidget_set.all())
            primary_card_node_widget = (
                card_node_widget_rows[0] if card_node_widget_rows else None
            )

            if primary_card_node_widget and primary_card_node_widget.label:
                widget_label = str(primary_card_node_widget.label)
            else:
                widget_label = str(node.name)

            node_items.append(
                {
                    "id": str(node.nodeid),
                    "alias": node.alias,
                    "name": str(node.name),
                    "description": str(node.description or ""),
                    "datatype": node.datatype,
                    "graph_id": str(node.graph_id),
                    "sortorder": node.sortorder,
                    "config": node.config,
                    "card_x_node_x_widget_label": widget_label,
                    "semantic_parent_id": semantic_parent_id,
                    "nodegroup_has_cardinality_n": nodegroup_has_cardinality_n,
                }
            )

        return JSONResponse(node_items)
