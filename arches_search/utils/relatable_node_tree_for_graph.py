from collections import defaultdict

from django.db import models
from django.db.models import F
from django.db.models.functions import Cast

from arches.app.models import models as arches_models


def build_relatable_nodes_tree_response(target_graph_uuid):
    incoming_node_rows = _get_incoming_node_rows(target_graph_uuid)
    outgoing_node_rows, outgoing_related_graph_ids = (
        _get_outgoing_node_rows_and_related_graphs(target_graph_uuid)
    )

    relatable_node_rows = list(set(incoming_node_rows) | set(outgoing_node_rows))
    if not relatable_node_rows:
        return {
            "target_graph_id": str(target_graph_uuid),
            "relatable_graphs": [],
            "options": [],
        }

    relatable_node_graph_ids = sorted(
        {graph_uuid for _, graph_uuid in relatable_node_rows}
    )

    relatable_target_graph_ids = set()
    relatable_target_graph_ids.update(
        {graph_uuid for _, graph_uuid in incoming_node_rows}
    )
    relatable_target_graph_ids.update(outgoing_related_graph_ids)

    graph_ids_to_fetch = set(relatable_node_graph_ids) | set(relatable_target_graph_ids)

    graph_rows_by_id = {
        graph_row["graphid"]: graph_row
        for graph_row in arches_models.GraphModel.objects.filter(
            graphid__in=graph_ids_to_fetch
        ).values("graphid", "name", "slug")
    }

    parent_by_child_id_by_graph_id = _build_semantic_parent_maps(
        relatable_node_graph_ids
    )

    included_node_ids_by_graph_id = _collect_relatable_nodes_plus_ancestors(
        relatable_node_rows,
        parent_by_child_id_by_graph_id,
    )

    included_node_ids = set()
    for node_ids_for_graph in included_node_ids_by_graph_id.values():
        included_node_ids.update(node_ids_for_graph)

    node_rows_by_id, ordered_node_ids = _fetch_nodes_by_id_with_order(included_node_ids)
    widget_label_by_node_id = _fetch_primary_widget_labels(included_node_ids)

    options = _build_treeselect_options(
        relatable_node_graph_ids,
        graph_rows_by_id,
        included_node_ids_by_graph_id,
        node_rows_by_id,
        ordered_node_ids,
        widget_label_by_node_id,
        parent_by_child_id_by_graph_id,
    )

    relatable_graphs = [
        {
            "graph_id": str(graph_uuid),
            "slug": graph_rows_by_id[graph_uuid]["slug"],
            "name": graph_rows_by_id[graph_uuid]["name"],
        }
        for graph_uuid in relatable_target_graph_ids
        if graph_uuid in graph_rows_by_id
    ]
    relatable_graphs.sort(key=lambda row: str(row.get("name") or ""))

    return {
        "target_graph_id": str(target_graph_uuid),
        "relatable_graphs": relatable_graphs,
        "options": options,
    }


def _get_incoming_node_rows(target_graph_uuid):
    config_contains_target_graph = {"graphs": [{"graphid": str(target_graph_uuid)}]}

    return list(
        arches_models.Node.objects.filter(
            datatype__in=("resource-instance", "resource-instance-list"),
        )
        .annotate(config_jsonb=Cast(F("config"), output_field=models.JSONField()))
        .filter(config_jsonb__contains=config_contains_target_graph)
        .values_list("nodeid", "graph_id")
    )


def _get_outgoing_node_rows_and_related_graphs(target_graph_uuid):
    outgoing_nodes = list(
        arches_models.Node.objects.filter(
            graph_id=target_graph_uuid,
            datatype__in=("resource-instance", "resource-instance-list"),
        )
        .annotate(config_jsonb=Cast(F("config"), output_field=models.JSONField()))
        .values("nodeid", "graph_id", "config_jsonb")
    )

    node_rows = []
    related_graph_ids = set()

    for row in outgoing_nodes:
        node_rows.append((row["nodeid"], row["graph_id"]))

        config = row.get("config_jsonb") or {}
        graphs = config.get("graphs") or []

        for graph_entry in graphs:
            graph_id = graph_entry.get("graphid")
            if graph_id:
                related_graph_ids.add(graph_id)

    return node_rows, related_graph_ids


def _build_semantic_parent_maps(relatable_graph_ids):
    parent_by_child_id_by_graph_id = defaultdict(dict)

    edge_rows = arches_models.Edge.objects.filter(
        graph_id__in=relatable_graph_ids,
        rangenode_id__isnull=False,
        domainnode_id__isnull=False,
    ).values_list(
        "graph_id",
        "rangenode_id",
        "domainnode_id",
    )

    for graph_uuid, child_node_uuid, parent_node_uuid in edge_rows:
        if child_node_uuid not in parent_by_child_id_by_graph_id[graph_uuid]:
            parent_by_child_id_by_graph_id[graph_uuid][
                child_node_uuid
            ] = parent_node_uuid

    return parent_by_child_id_by_graph_id


def _collect_relatable_nodes_plus_ancestors(
    relatable_node_rows, parent_by_child_id_by_graph_id
):
    included_node_ids_by_graph_id = defaultdict(set)

    for node_uuid, graph_uuid in relatable_node_rows:
        included_node_ids_by_graph_id[graph_uuid].add(node_uuid)

        current_node_uuid = node_uuid
        visited_node_ids = set()

        while current_node_uuid not in visited_node_ids:
            visited_node_ids.add(current_node_uuid)

            parent_node_uuid = parent_by_child_id_by_graph_id.get(graph_uuid, {}).get(
                current_node_uuid
            )
            if parent_node_uuid is None:
                break

            included_node_ids_by_graph_id[graph_uuid].add(parent_node_uuid)
            current_node_uuid = parent_node_uuid

    return included_node_ids_by_graph_id


def _fetch_nodes_by_id_with_order(included_node_ids):
    node_rows_by_id = {}
    ordered_node_ids = []

    for node_row in (
        arches_models.Node.objects.filter(nodeid__in=included_node_ids)
        .order_by("sortorder", "name")
        .values(
            "nodeid",
            "graph_id",
            "alias",
            "name",
            "description",
            "datatype",
            "sortorder",
        )
    ):
        node_uuid = node_row["nodeid"]
        node_rows_by_id[node_uuid] = node_row
        ordered_node_ids.append(node_uuid)

    return node_rows_by_id, ordered_node_ids


def _fetch_primary_widget_labels(included_node_ids):
    widget_label_by_node_id = {}

    for node_uuid, widget_label in (
        arches_models.CardXNodeXWidget.objects.filter(node_id__in=included_node_ids)
        .order_by("node_id", "sortorder")
        .distinct("node_id")
        .values_list("node_id", "label")
    ):
        if widget_label:
            widget_label_by_node_id[node_uuid] = widget_label

    return widget_label_by_node_id


def _build_treeselect_options(
    relatable_graph_ids,
    graph_rows_by_id,
    included_node_ids_by_graph_id,
    node_rows_by_id,
    ordered_node_ids,
    widget_label_by_node_id,
    parent_by_child_id_by_graph_id,
):
    options = []

    for graph_uuid in relatable_graph_ids:
        graph_row = graph_rows_by_id.get(graph_uuid) or {}
        graph_label = graph_row.get("name") or str(graph_uuid)

        included_node_ids_for_graph = included_node_ids_by_graph_id.get(
            graph_uuid, set()
        )
        parent_by_child_id = parent_by_child_id_by_graph_id.get(graph_uuid, {})

        children_by_parent_id = defaultdict(list)
        root_node_ids = []

        for node_uuid in ordered_node_ids:
            if node_uuid not in included_node_ids_for_graph:
                continue

            node_row = node_rows_by_id[node_uuid]
            if node_row["graph_id"] != graph_uuid:
                continue

            parent_node_uuid = parent_by_child_id.get(node_uuid)
            if parent_node_uuid and parent_node_uuid in included_node_ids_for_graph:
                children_by_parent_id[parent_node_uuid].append(node_uuid)
            else:
                root_node_ids.append(node_uuid)

        def build_node_tree(node_uuid):
            node_row = node_rows_by_id[node_uuid]
            node_label = (
                widget_label_by_node_id.get(node_uuid) or node_row.get("name") or ""
            )

            child_node_ids = children_by_parent_id.get(node_uuid, [])
            return {
                "key": str(node_uuid),
                "label": node_label,
                "children": [
                    build_node_tree(child_uuid) for child_uuid in child_node_ids
                ],
                "data": {
                    "id": str(node_uuid),
                    "graph_id": str(node_row.get("graph_id") or graph_uuid),
                    "alias": node_row.get("alias"),
                    "name": node_row.get("name") or "",
                    "description": node_row.get("description") or "",
                    "datatype": node_row.get("datatype"),
                },
            }

        graph_children = [build_node_tree(node_uuid) for node_uuid in root_node_ids]

        options.append(
            {
                "key": f"graph:{graph_uuid}",
                "label": graph_label,
                "children": graph_children,
                "data": {
                    "graph_id": str(graph_uuid),
                    "slug": graph_row.get("slug"),
                    "name": graph_label,
                },
            }
        )

    options.sort(key=lambda graph_option: str(graph_option.get("label") or ""))
    return options
