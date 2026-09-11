from collections import defaultdict

from django.db import models
from django.db.models import F
from django.db.models.functions import Cast
from django.utils.translation import gettext as _

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

    relatable_node_graph_ids_all = {graph_id for _, graph_id in relatable_node_rows}
    relatable_target_graph_ids_all = {
        graph_id for _, graph_id in incoming_node_rows
    } | set(outgoing_related_graph_ids)
    graph_ids_to_fetch = relatable_node_graph_ids_all | relatable_target_graph_ids_all

    graph_rows_by_id = {
        str(graph_row["graphid"]): graph_row
        for graph_row in arches_models.GraphModel.objects.filter(
            graphid__in=graph_ids_to_fetch,
            isresource=True,
            is_active=True,
        ).values("graphid", "name", "slug")
    }

    if not graph_rows_by_id:
        return {
            "target_graph_id": str(target_graph_uuid),
            "relatable_graphs": [],
            "options": [],
        }

    active_resource_graph_ids = set(graph_rows_by_id.keys())

    relatable_node_rows = [
        (node_id, graph_id)
        for node_id, graph_id in relatable_node_rows
        if graph_id in active_resource_graph_ids
    ]
    relatable_node_graph_ids = sorted({graph_id for _, graph_id in relatable_node_rows})

    relatable_target_graph_ids = {
        graph_id
        for graph_id in relatable_target_graph_ids_all
        if graph_id in active_resource_graph_ids
    }

    relatable_graph_ids_for_options = sorted(
        set(relatable_node_graph_ids) | relatable_target_graph_ids
    )

    parent_by_child_id_by_graph_id = _build_semantic_parent_maps(
        relatable_node_graph_ids
    )

    included_node_ids_by_graph_id = _collect_relatable_nodes_plus_ancestors(
        relatable_node_rows,
        parent_by_child_id_by_graph_id,
    )

    included_node_ids = (
        set().union(*included_node_ids_by_graph_id.values())
        if included_node_ids_by_graph_id
        else set()
    )

    node_rows_by_id, ordered_node_ids = _fetch_nodes_by_id_with_order(included_node_ids)
    widget_label_by_node_id = _fetch_primary_widget_labels(included_node_ids)

    options = _build_treeselect_options(
        relatable_graph_ids_for_options,
        graph_rows_by_id,
        included_node_ids_by_graph_id,
        node_rows_by_id,
        ordered_node_ids,
        widget_label_by_node_id,
        parent_by_child_id_by_graph_id,
        anchor_graph_id=str(target_graph_uuid),
    )

    relatable_graphs = [
        {
            "graph_id": graph_id,
            "slug": graph_rows_by_id[graph_id].get("slug"),
            "name": graph_rows_by_id[graph_id].get("name") or "",
        }
        for graph_id in relatable_target_graph_ids
        if graph_id in graph_rows_by_id
    ]
    relatable_graphs.sort(key=lambda row: str(row.get("name") or ""))

    return {
        "target_graph_id": str(target_graph_uuid),
        "relatable_graphs": relatable_graphs,
        "options": options,
    }


def build_relatable_nodes_tree_for_graph_pair(graph_a_uuid, graph_b_uuid):
    graph_rows_by_id = {
        str(graph_row["graphid"]): graph_row
        for graph_row in arches_models.GraphModel.objects.filter(
            graphid__in=(graph_a_uuid, graph_b_uuid),
            isresource=True,
            is_active=True,
        ).values("graphid", "name", "slug")
    }

    if not graph_rows_by_id:
        return {"options": []}

    relatable_graph_ids = sorted(graph_rows_by_id.keys())

    relatable_node_rows = [
        (node_id, graph_id)
        for node_id, graph_id in _get_pairwise_linking_node_rows(
            graph_a_uuid, graph_b_uuid
        )
        if graph_id in graph_rows_by_id
    ]

    parent_by_child_id_by_graph_id = _build_semantic_parent_maps(relatable_graph_ids)

    included_node_ids_by_graph_id = _collect_relatable_nodes_plus_ancestors(
        relatable_node_rows,
        parent_by_child_id_by_graph_id,
    )

    included_node_ids = (
        set().union(*included_node_ids_by_graph_id.values())
        if included_node_ids_by_graph_id
        else set()
    )

    node_rows_by_id, ordered_node_ids = _fetch_nodes_by_id_with_order(included_node_ids)
    widget_label_by_node_id = _fetch_primary_widget_labels(included_node_ids)

    options = _build_treeselect_options(
        relatable_graph_ids,
        graph_rows_by_id,
        included_node_ids_by_graph_id,
        node_rows_by_id,
        ordered_node_ids,
        widget_label_by_node_id,
        parent_by_child_id_by_graph_id,
        anchor_graph_id=str(graph_a_uuid),
    )

    if str(graph_a_uuid) == str(graph_b_uuid) and options:
        options = _duplicate_self_relationship_options(options[0])

    return {"options": options}


def _duplicate_self_relationship_options(graph_option):
    return [
        _clone_option_tree_with_role(
            graph_option,
            role_suffix="forward",
            label_template=_("%(graph_label)s (outer)"),
            force_is_inverse=None,
        ),
        _clone_option_tree_with_role(
            graph_option,
            role_suffix="inverse",
            label_template=_("%(graph_label)s (inner)"),
            force_is_inverse=True,
        ),
    ]


def _clone_option_tree_with_role(
    graph_option, role_suffix, label_template, force_is_inverse
):
    return {
        "key": f"{graph_option['key']}::{role_suffix}",
        "label": label_template % {"graph_label": graph_option["label"]},
        "children": [
            _clone_node_tree_with_role(child, role_suffix, force_is_inverse)
            for child in graph_option["children"]
        ],
        "data": graph_option["data"],
    }


def _clone_node_tree_with_role(node_option, role_suffix, force_is_inverse):
    data = dict(node_option["data"])
    if force_is_inverse is not None:
        data["is_inverse"] = force_is_inverse

    return {
        "key": f"{node_option['key']}::{role_suffix}",
        "label": node_option["label"],
        "children": [
            _clone_node_tree_with_role(child, role_suffix, force_is_inverse)
            for child in node_option["children"]
        ],
        "data": data,
    }


def _get_pairwise_linking_node_rows(graph_a_uuid, graph_b_uuid):
    graph_a_id = str(graph_a_uuid)
    graph_b_id = str(graph_b_uuid)

    node_rows = (
        arches_models.Node.objects.filter(
            graph_id__in=(graph_a_uuid, graph_b_uuid),
            datatype__in=("resource-instance", "resource-instance-list"),
            graph__is_active=True,
        )
        .annotate(config_jsonb=Cast(F("config"), output_field=models.JSONField()))
        .values("nodeid", "graph_id", "config_jsonb")
    )

    linking_node_rows = []

    for node_row in node_rows:
        own_graph_id = str(node_row["graph_id"])
        other_graph_id = graph_b_id if own_graph_id == graph_a_id else graph_a_id

        config = node_row.get("config_jsonb") or {}
        referenced_graph_ids = {
            graph_entry.get("graphid")
            for graph_entry in config.get("graphs") or []
            if graph_entry.get("graphid")
        }

        if other_graph_id in referenced_graph_ids:
            linking_node_rows.append((node_row["nodeid"], own_graph_id))

    return linking_node_rows


def _get_incoming_node_rows(target_graph_uuid):
    config_contains_target_graph = {"graphs": [{"graphid": str(target_graph_uuid)}]}

    return [
        (node_id, str(graph_id))
        for node_id, graph_id in arches_models.Node.objects.filter(
            datatype__in=("resource-instance", "resource-instance-list"),
            graph__is_active=True,
        )
        .annotate(config_jsonb=Cast(F("config"), output_field=models.JSONField()))
        .filter(config_jsonb__contains=config_contains_target_graph)
        .values_list("nodeid", "graph_id")
    ]


def _get_outgoing_node_rows_and_related_graphs(target_graph_uuid):
    outgoing_nodes = list(
        arches_models.Node.objects.filter(
            graph_id=target_graph_uuid,
            graph__is_active=True,
            datatype__in=("resource-instance", "resource-instance-list"),
        )
        .annotate(config_jsonb=Cast(F("config"), output_field=models.JSONField()))
        .values("nodeid", "graph_id", "config_jsonb")
    )

    node_rows = []
    related_graph_ids = set()

    for outgoing_node_row in outgoing_nodes:
        node_rows.append(
            (outgoing_node_row["nodeid"], str(outgoing_node_row["graph_id"]))
        )

        config = outgoing_node_row.get("config_jsonb") or {}
        for graph_entry in config.get("graphs") or []:
            graph_id = graph_entry.get("graphid")
            if graph_id:
                related_graph_ids.add(str(graph_id))

    return node_rows, related_graph_ids


def _build_semantic_parent_maps(relatable_graph_ids):
    parent_by_child_id_by_graph_id = defaultdict(dict)

    for graph_id, child_node_id, parent_node_id in arches_models.Edge.objects.filter(
        graph_id__in=relatable_graph_ids,
        graph__is_active=True,
        rangenode_id__isnull=False,
        domainnode_id__isnull=False,
    ).values_list("graph_id", "rangenode_id", "domainnode_id"):
        graph_id_str = str(graph_id)
        if child_node_id not in parent_by_child_id_by_graph_id[graph_id_str]:
            parent_by_child_id_by_graph_id[graph_id_str][child_node_id] = parent_node_id

    return parent_by_child_id_by_graph_id


def _collect_relatable_nodes_plus_ancestors(
    relatable_node_rows, parent_by_child_id_by_graph_id
):
    included_node_ids_by_graph_id = defaultdict(set)

    for node_id, graph_id in relatable_node_rows:
        included_node_ids_by_graph_id[graph_id].add(node_id)

        current_node_id = node_id
        visited_node_ids = set()

        while current_node_id not in visited_node_ids:
            visited_node_ids.add(current_node_id)

            parent_node_id = parent_by_child_id_by_graph_id.get(graph_id, {}).get(
                current_node_id
            )
            if parent_node_id is None:
                break

            included_node_ids_by_graph_id[graph_id].add(parent_node_id)
            current_node_id = parent_node_id

    return included_node_ids_by_graph_id


def _fetch_nodes_by_id_with_order(included_node_ids):
    node_rows_by_id = {}
    ordered_node_ids = []

    for node_row in (
        arches_models.Node.objects.filter(
            nodeid__in=included_node_ids,
            graph__is_active=True,
        )
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
        node_id = node_row["nodeid"]
        node_rows_by_id[node_id] = node_row
        ordered_node_ids.append(node_id)

    return node_rows_by_id, ordered_node_ids


def _fetch_primary_widget_labels(included_node_ids):
    widget_label_by_node_id = {}

    for node_id, widget_label in (
        arches_models.CardXNodeXWidget.objects.filter(
            node_id__in=included_node_ids,
            node__graph__is_active=True,
        )
        .order_by("node_id", "sortorder")
        .distinct("node_id")
        .values_list("node_id", "label")
    ):
        if widget_label:
            widget_label_by_node_id[node_id] = widget_label

    return widget_label_by_node_id


def _build_treeselect_options(
    relatable_graph_ids,
    graph_rows_by_id,
    included_node_ids_by_graph_id,
    node_rows_by_id,
    ordered_node_ids,
    widget_label_by_node_id,
    parent_by_child_id_by_graph_id,
    anchor_graph_id,
):
    options = []

    for graph_id in relatable_graph_ids:
        graph_row = graph_rows_by_id.get(graph_id) or {}
        graph_label = graph_row.get("name") or graph_id

        included_node_ids_for_graph = included_node_ids_by_graph_id.get(graph_id, set())
        parent_by_child_id = parent_by_child_id_by_graph_id.get(graph_id, {})

        children_by_parent_id = defaultdict(list)
        root_node_ids = []

        for node_id in ordered_node_ids:
            if node_id not in included_node_ids_for_graph:
                continue

            node_row = node_rows_by_id[node_id]
            if str(node_row["graph_id"]) != graph_id:
                continue

            parent_node_id = parent_by_child_id.get(node_id)
            if parent_node_id and parent_node_id in included_node_ids_for_graph:
                children_by_parent_id[parent_node_id].append(node_id)
            else:
                root_node_ids.append(node_id)

        def build_node_tree(node_id):
            node_row = node_rows_by_id[node_id]
            node_label = (
                widget_label_by_node_id.get(node_id) or node_row.get("name") or ""
            )
            child_node_ids = children_by_parent_id.get(node_id, [])

            return {
                "key": str(node_id),
                "label": node_label,
                "children": [build_node_tree(child_id) for child_id in child_node_ids],
                "data": {
                    "id": str(node_id),
                    "graph_id": str(node_row.get("graph_id") or graph_id),
                    "alias": node_row.get("alias"),
                    "name": node_row.get("name") or "",
                    "description": node_row.get("description") or "",
                    "datatype": node_row.get("datatype"),
                    "is_inverse": str(node_row.get("graph_id") or graph_id)
                    != anchor_graph_id,
                },
            }

        options.append(
            {
                "key": f"graph:{graph_id}",
                "label": graph_label,
                "children": [build_node_tree(node_id) for node_id in root_node_ids],
                "data": {
                    "graph_id": graph_id,
                    "slug": graph_row.get("slug"),
                    "name": graph_label,
                },
            }
        )

    options.sort(key=lambda graph_option: str(graph_option.get("label") or ""))
    return options
