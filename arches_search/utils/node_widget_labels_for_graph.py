from django.db import models

from arches.app.models import models as arches_models


def get_nodes_with_widget_labels_for_graph(graph_id):
    node_rows = list(
        arches_models.Node.objects.filter(graph_id=graph_id).values(
            "nodeid", "nodegroup_id", "name", "sortorder", "datatype", "issearchable"
        )
    )
    if not node_rows:
        return []

    nodegroup_id_by_node_id = {}
    node_name_by_node_id = {}
    node_sortorder_by_node_id = {}
    searchable_node_ids = set()
    for node_row in node_rows:
        node_id = node_row["nodeid"]
        nodegroup_id_by_node_id[node_id] = node_row["nodegroup_id"]
        node_name_by_node_id[node_id] = str(node_row["name"])
        node_sortorder_by_node_id[node_id] = node_row["sortorder"] or 0
        if node_row.get("issearchable") is True:
            searchable_node_ids.add(node_id)

    nodegroup_ids_in_graph = {
        nodegroup_id
        for nodegroup_id in nodegroup_id_by_node_id.values()
        if nodegroup_id is not None
    }

    card_title_by_nodegroup_id, card_sortorder_by_nodegroup_id = _fetch_card_metadata(
        nodegroup_ids_in_graph
    )
    parent_nodegroup_id_by_nodegroup_id, cardinality_by_nodegroup_id = (
        _fetch_nodegroup_metadata(nodegroup_ids_in_graph)
    )
    graph_name = str(
        arches_models.GraphModel.objects.filter(graphid=graph_id)
        .values_list("name", flat=True)
        .first()
    )
    searchable_roots_with_widget_label = _fetch_searchable_roots_with_widget_label(
        searchable_node_ids, nodegroup_ids_in_graph
    )

    nodegroups_to_include = _collect_nodegroups_to_include(
        searchable_node_ids,
        nodegroup_id_by_node_id,
        parent_nodegroup_id_by_nodegroup_id,
    )
    identity_nodegroup_ids = {
        nodegroup_id
        for nodegroup_id in nodegroups_to_include
        if parent_nodegroup_id_by_nodegroup_id.get(nodegroup_id) is None
        and str(
            card_title_by_nodegroup_id.get(nodegroup_id)
            or node_name_by_node_id.get(nodegroup_id, "")
        )
        == graph_name
    }
    card_representative_id_by_nodegroup_id = _build_card_representative_ids(
        nodegroups_to_include,
        searchable_node_ids,
        searchable_roots_with_widget_label,
        identity_nodegroup_ids,
    )

    serialized_nodes = []

    for nodegroup_id in nodegroups_to_include - searchable_node_ids:
        if nodegroup_id not in card_representative_id_by_nodegroup_id:
            continue  # Identity card suppressed — children appear at tree root
        parent_nodegroup_id = parent_nodegroup_id_by_nodegroup_id.get(nodegroup_id)
        card_label = card_title_by_nodegroup_id.get(
            nodegroup_id
        ) or node_name_by_node_id.get(nodegroup_id, "")
        nodegroup_cardinality = (
            str(cardinality_by_nodegroup_id.get(nodegroup_id) or "").strip().lower()
        )
        serialized_nodes.append(
            {
                "id": card_representative_id_by_nodegroup_id[nodegroup_id],
                "alias": "",
                "name": card_label,
                "description": "",
                "datatype": "semantic",
                "graph_id": str(graph_id),
                "sortorder": card_sortorder_by_nodegroup_id.get(
                    nodegroup_id, node_sortorder_by_node_id.get(nodegroup_id, 0)
                ),
                "config": None,
                "card_x_node_x_widget_label": card_label,
                "semantic_parent_id": card_representative_id_by_nodegroup_id.get(
                    parent_nodegroup_id
                ),
                "nodegroup_has_cardinality_n": nodegroup_cardinality == "n",
                "selectable": False,
            }
        )

    nodes_queryset = (
        arches_models.Node.objects.filter(
            graph_id=graph_id, nodeid__in=searchable_node_ids
        )
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

    for node in nodes_queryset:
        if node.nodegroup_id is None:
            continue

        nodegroup = getattr(node, "nodegroup", None)
        nodegroup_cardinality = (
            str(nodegroup.cardinality).strip().lower()
            if nodegroup and nodegroup.cardinality is not None
            else None
        )
        nodegroup_has_cardinality_n = nodegroup_cardinality == "n"
        node_is_nodegroup_root = node.nodeid == node.nodegroup_id

        card_node_widget_rows = list(node.cardxnodexwidget_set.all())
        primary_card_node_widget = (
            card_node_widget_rows[0] if card_node_widget_rows else None
        )
        primary_widget_label = (
            str(primary_card_node_widget.label).strip()
            if primary_card_node_widget and primary_card_node_widget.label
            else ""
        )

        if node_is_nodegroup_root and node.nodegroup_id in identity_nodegroup_ids:
            continue

        if node_is_nodegroup_root and primary_widget_label:
            card_group_id = f"card-group:{node.nodeid}"
            card_group_label = card_title_by_nodegroup_id.get(node.nodegroup_id) or str(
                node.name
            )
            parent_nodegroup_id = parent_nodegroup_id_by_nodegroup_id.get(
                node.nodegroup_id
            )
            serialized_nodes.append(
                {
                    "id": card_group_id,
                    "alias": node.alias,
                    "name": str(node.name),
                    "description": str(node.description or ""),
                    "datatype": node.datatype,
                    "graph_id": str(node.graph_id),
                    "sortorder": card_sortorder_by_nodegroup_id.get(
                        node.nodegroup_id, node.sortorder
                    ),
                    "config": None,
                    "card_x_node_x_widget_label": card_group_label,
                    "semantic_parent_id": card_representative_id_by_nodegroup_id.get(
                        parent_nodegroup_id
                    ),
                    "nodegroup_has_cardinality_n": nodegroup_has_cardinality_n,
                    "selectable": False,
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
                    "semantic_parent_id": card_group_id,
                    "nodegroup_has_cardinality_n": nodegroup_has_cardinality_n,
                }
            )
            continue

        if node_is_nodegroup_root:
            node_display_label = card_title_by_nodegroup_id.get(
                node.nodegroup_id
            ) or str(node.name)
            parent_nodegroup_id = parent_nodegroup_id_by_nodegroup_id.get(
                node.nodegroup_id
            )
            semantic_parent_id = card_representative_id_by_nodegroup_id.get(
                parent_nodegroup_id
            )
            node_sortorder = card_sortorder_by_nodegroup_id.get(
                node.nodegroup_id, node.sortorder
            )
        else:
            node_display_label = primary_widget_label or str(node.name)
            semantic_parent_id = card_representative_id_by_nodegroup_id.get(
                node.nodegroup_id
            )
            node_sortorder = (
                primary_card_node_widget.sortorder
                if primary_card_node_widget
                else node.sortorder
            )

        serialized_nodes.append(
            {
                "id": str(node.nodeid),
                "alias": node.alias,
                "name": str(node.name),
                "description": str(node.description or ""),
                "datatype": node.datatype,
                "graph_id": str(node.graph_id),
                "sortorder": node_sortorder,
                "config": node.config,
                "card_x_node_x_widget_label": node_display_label,
                "semantic_parent_id": semantic_parent_id,
                "nodegroup_has_cardinality_n": nodegroup_has_cardinality_n,
            }
        )

    return serialized_nodes


def _fetch_card_metadata(nodegroup_ids):
    rows = list(
        arches_models.Card.objects.filter(nodegroup_id__in=nodegroup_ids)
        .order_by("nodegroup_id", "sortorder")
        .distinct("nodegroup_id")
        .values("nodegroup_id", "name", "sortorder")
    )
    return (
        {row["nodegroup_id"]: str(row["name"]) for row in rows},
        {row["nodegroup_id"]: row["sortorder"] for row in rows},
    )


def _fetch_nodegroup_metadata(nodegroup_ids):
    rows = list(
        arches_models.NodeGroup.objects.filter(nodegroupid__in=nodegroup_ids).values(
            "nodegroupid", "parentnodegroup_id", "cardinality"
        )
    )
    return (
        {row["nodegroupid"]: row["parentnodegroup_id"] for row in rows},
        {row["nodegroupid"]: row["cardinality"] for row in rows},
    )


def _fetch_searchable_roots_with_widget_label(
    searchable_node_ids, nodegroup_ids_in_graph
):
    searchable_root_node_ids = searchable_node_ids & nodegroup_ids_in_graph
    return {
        str(node_id)
        for node_id, label in arches_models.CardXNodeXWidget.objects.filter(
            node_id__in=searchable_root_node_ids
        )
        .order_by("node_id", "sortorder")
        .distinct("node_id")
        .values_list("node_id", "label")
        if label and str(label).strip()
    }


def _collect_nodegroups_to_include(
    searchable_node_ids, nodegroup_id_by_node_id, parent_nodegroup_id_by_nodegroup_id
):
    nodegroups_with_searchable_nodes = {
        nodegroup_id_by_node_id[node_id]
        for node_id in searchable_node_ids
        if nodegroup_id_by_node_id.get(node_id) is not None
    }
    nodegroups_to_include = set(nodegroups_with_searchable_nodes)
    for nodegroup_id in nodegroups_with_searchable_nodes:
        ancestor_nodegroup_id = parent_nodegroup_id_by_nodegroup_id.get(nodegroup_id)
        while (
            ancestor_nodegroup_id is not None
            and ancestor_nodegroup_id not in nodegroups_to_include
        ):
            nodegroups_to_include.add(ancestor_nodegroup_id)
            ancestor_nodegroup_id = parent_nodegroup_id_by_nodegroup_id.get(
                ancestor_nodegroup_id
            )
    return nodegroups_to_include


def _build_card_representative_ids(
    nodegroups_to_include,
    searchable_node_ids,
    searchable_roots_with_widget_label,
    identity_nodegroup_ids,
):
    card_representative_id_by_nodegroup_id = {}
    for nodegroup_id in nodegroups_to_include:
        nodegroup_root_is_searchable = nodegroup_id in searchable_node_ids
        if nodegroup_id in identity_nodegroup_ids:
            if nodegroup_root_is_searchable:
                card_representative_id_by_nodegroup_id[nodegroup_id] = str(nodegroup_id)
            continue
        if (
            nodegroup_root_is_searchable
            and str(nodegroup_id) not in searchable_roots_with_widget_label
        ):
            card_representative_id_by_nodegroup_id[nodegroup_id] = str(nodegroup_id)
        else:
            card_representative_id_by_nodegroup_id[nodegroup_id] = (
                f"card-group:{nodegroup_id}"
            )
    return card_representative_id_by_nodegroup_id
