import uuid
from collections import defaultdict, deque

from django.db import models
from django.db.models import Count

from arches.app.models import models as arches_models
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase


class NodesWithWidgetLabelsForGraphAPI(APIBase):
    def get(self, request, graph_id):
        node_rows = list(
            arches_models.Node.objects.filter(graph_id=graph_id).values(
                "nodeid",
                "nodegroup_id",
                "name",
                "sortorder",
                "datatype",
            )
        )
        if not node_rows:
            return JSONResponse([])

        nodegroup_id_by_node_id = {}
        node_name_by_node_id = {}
        node_sortorder_by_node_id = {}

        for node_row in node_rows:
            node_id = node_row["nodeid"]
            nodegroup_id_by_node_id[node_id] = node_row["nodegroup_id"]
            node_name_by_node_id[node_id] = str(node_row["name"])
            node_sortorder_by_node_id[node_id] = node_row["sortorder"] or 0

        all_node_ids_in_graph = set(nodegroup_id_by_node_id.keys())
        nodegroup_ids_in_graph = {
            nodegroup_id
            for nodegroup_id in nodegroup_id_by_node_id.values()
            if nodegroup_id is not None
        }

        hidden_nodegroup_ids = set(
            arches_models.Card.objects.filter(
                nodegroup_id__in=nodegroup_ids_in_graph,
                visible=False,
            ).values_list("nodegroup_id", flat=True)
        )

        nodegroup_ids_with_any_card = set(
            arches_models.Card.objects.filter(
                nodegroup_id__in=nodegroup_ids_in_graph
            ).values_list("nodegroup_id", flat=True)
        )

        card_title_by_nodegroup_id = {}
        card_rows = (
            arches_models.Card.objects.filter(nodegroup_id__in=nodegroup_ids_in_graph)
            .order_by("nodegroup_id", "sortorder")
            .values("nodegroup_id", "name")
        )
        for card_row in card_rows:
            nodegroup_id = card_row["nodegroup_id"]
            if nodegroup_id not in card_title_by_nodegroup_id:
                card_title_by_nodegroup_id[nodegroup_id] = str(card_row["name"])

        nodegroup_root_node_ids = {
            node_row["nodeid"]
            for node_row in node_rows
            if node_row["nodegroup_id"] is not None
            and node_row["nodeid"] == node_row["nodegroup_id"]
        }

        nodegroup_root_node_ids_without_any_card = {
            nodegroup_root_node_id
            for nodegroup_root_node_id in nodegroup_root_node_ids
            if nodegroup_root_node_id not in nodegroup_ids_with_any_card
        }

        nodegroup_root_node_ids_with_visible_card = set(
            arches_models.Card.objects.filter(nodegroup_id__in=nodegroup_root_node_ids)
            .exclude(visible=False)
            .values_list("nodegroup_id", flat=True)
            .distinct()
        )

        hidden_node_ids_raw = set(
            arches_models.CardXNodeXWidget.objects.filter(
                node__graph_id=graph_id,
                visible=False,
            ).values_list("node_id", flat=True)
        )
        hidden_node_ids_for_exclusion = (
            hidden_node_ids_raw - nodegroup_root_node_ids_with_visible_card
        )

        parents_by_child_id = defaultdict(list)
        edge_pairs = arches_models.Edge.objects.filter(graph_id=graph_id).values_list(
            "domainnode_id",
            "rangenode_id",
        )
        for parent_node_id, child_node_id in edge_pairs:
            if not parent_node_id or not child_node_id:
                continue
            parents_by_child_id[child_node_id].append(parent_node_id)

        def is_node_filtered(candidate_node_id):
            if candidate_node_id in hidden_node_ids_for_exclusion:
                return True

            if candidate_node_id in nodegroup_root_node_ids_without_any_card:
                return True

            candidate_nodegroup_id = nodegroup_id_by_node_id.get(candidate_node_id)
            if (
                candidate_nodegroup_id is not None
                and candidate_nodegroup_id in hidden_nodegroup_ids
            ):
                return True

            return False

        def resolve_closest_unfiltered_parent_id(child_node_id):
            candidate_parent_node_ids = parents_by_child_id.get(child_node_id, [])
            if not candidate_parent_node_ids:
                return None

            unique_candidate_parent_node_ids = list(set(candidate_parent_node_ids))
            sorted_candidate_parent_node_ids = sorted(
                unique_candidate_parent_node_ids,
                key=lambda parent_node_id: (
                    node_sortorder_by_node_id.get(parent_node_id, 0),
                    node_name_by_node_id.get(parent_node_id, ""),
                    str(parent_node_id),
                ),
            )

            visited_node_ids = set()
            bfs_queue = deque(sorted_candidate_parent_node_ids)

            while bfs_queue:
                current_parent_node_id = bfs_queue.popleft()
                if current_parent_node_id in visited_node_ids:
                    continue
                visited_node_ids.add(current_parent_node_id)

                if not is_node_filtered(current_parent_node_id):
                    return current_parent_node_id

                next_parent_node_ids = parents_by_child_id.get(
                    current_parent_node_id, []
                )
                bfs_queue.extend(next_parent_node_ids)

            return None

        nodes_queryset = (
            arches_models.Node.objects.filter(graph_id=graph_id)
            .exclude(nodeid__in=hidden_node_ids_for_exclusion)
            .exclude(nodeid__in=nodegroup_root_node_ids_without_any_card)
            .exclude(nodegroup_id__in=hidden_nodegroup_ids)
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

        serialized_nodes = []

        for node in nodes_queryset:
            resolved_parent_node_id = resolve_closest_unfiltered_parent_id(node.nodeid)
            semantic_parent_id = (
                str(resolved_parent_node_id) if resolved_parent_node_id else None
            )

            nodegroup = getattr(node, "nodegroup", None)
            nodegroup_cardinality = (
                str(nodegroup.cardinality).strip().lower()
                if nodegroup and nodegroup.cardinality is not None
                else None
            )
            nodegroup_has_cardinality_n = nodegroup_cardinality == "n"

            node_is_nodegroup_root = (
                node.nodegroup_id is not None and node.nodeid == node.nodegroup_id
            )

            card_node_widget_rows = list(node.cardxnodexwidget_set.all())
            primary_card_node_widget = (
                card_node_widget_rows[0] if card_node_widget_rows else None
            )
            primary_widget_label = (
                str(primary_card_node_widget.label).strip()
                if primary_card_node_widget and primary_card_node_widget.label
                else ""
            )

            if node_is_nodegroup_root and primary_widget_label:
                card_group_id = uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"arches-card-group:{node.nodeid}",
                )
                card_group_label = card_title_by_nodegroup_id.get(
                    node.nodegroup_id
                ) or str(node.name)

                serialized_nodes.append(
                    {
                        "id": str(card_group_id),
                        "alias": node.alias,
                        "name": str(node.name),
                        "description": str(node.description or ""),
                        "datatype": node.datatype,
                        "graph_id": str(node.graph_id),
                        "sortorder": node.sortorder,
                        "config": None,
                        "card_x_node_x_widget_label": card_group_label,
                        "semantic_parent_id": semantic_parent_id,
                        "nodegroup_has_cardinality_n": nodegroup_has_cardinality_n,
                        "selectable": False,
                        "kind": "card-group",
                    }
                )

                serialized_nodes.append(
                    {
                        "id": str(node.nodeid),
                        "alias": node.alias,
                        "name": str(node.name),
                        "description": str(node.description or ""),
                        "datatype": node.datatype,
                        "graph_id": str(node.graph_id),
                        "sortorder": node.sortorder,
                        "config": node.config,
                        "card_x_node_x_widget_label": primary_widget_label,
                        "semantic_parent_id": str(card_group_id),
                        "nodegroup_has_cardinality_n": nodegroup_has_cardinality_n,
                        "kind": "node",
                    }
                )
                continue

            if node_is_nodegroup_root:
                node_display_label = card_title_by_nodegroup_id.get(
                    node.nodegroup_id
                ) or str(node.name)
            else:
                node_display_label = primary_widget_label or str(node.name)

            serialized_nodes.append(
                {
                    "id": str(node.nodeid),
                    "alias": node.alias,
                    "name": str(node.name),
                    "description": str(node.description or ""),
                    "datatype": node.datatype,
                    "graph_id": str(node.graph_id),
                    "sortorder": node.sortorder,
                    "config": node.config,
                    "card_x_node_x_widget_label": node_display_label,
                    "semantic_parent_id": semantic_parent_id,
                    "nodegroup_has_cardinality_n": nodegroup_has_cardinality_n,
                    "kind": "node",
                }
            )

        return JSONResponse(serialized_nodes)
