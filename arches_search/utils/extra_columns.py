import logging

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches.app.models.models import Node, ResourceInstance
from arches.app.utils import permission_backend

from arches_querysets.models import GraphWithPrefetching, TileTree

logger = logging.getLogger(__name__)

# These two datatypes' `details`/`display_value` name a *different*
# resource than the one being displayed (the related resource being
# pointed at), which is why they alone need the extra permission pass in
# _filter_permitted_related_resources
RESOURCE_INSTANCE_DATATYPES = ("resource-instance", "resource-instance-list")


def validate_extra_columns(extra_columns_spec):
    if extra_columns_spec is None:
        return
    if not isinstance(extra_columns_spec, list):
        raise ValidationError(_("extra_columns must be a list."))
    for entry in extra_columns_spec:
        if not isinstance(entry, dict):
            raise ValidationError(_("Each extra_columns entry must be an object."))

        graph_slug = entry.get("graph_slug")
        node_alias = entry.get("node_alias")

        if not isinstance(graph_slug, str) or not graph_slug:
            raise ValidationError(
                _("Each extra_columns entry requires a non-empty graph_slug.")
            )
        if not isinstance(node_alias, str) or not node_alias:
            raise ValidationError(
                _("Each extra_columns entry requires a non-empty node_alias.")
            )


def resolve_node_refs(extra_columns_spec, user):
    if not extra_columns_spec:
        return {}

    graph_slugs = {entry["graph_slug"] for entry in extra_columns_spec}
    node_aliases = {entry["node_alias"] for entry in extra_columns_spec}

    nodes_by_key = {
        (node.graph.slug, node.alias): node
        for node in Node.objects.filter(
            graph__slug__in=graph_slugs,
            alias__in=node_aliases,
            source_identifier=None,
        )
        .exclude(datatype="semantic")
        .select_related("graph")
    }

    permitted_nodegroup_ids = set(
        permission_backend.get_nodegroups_by_perm(user, "models.read_nodegroup")
    )

    resolved = {}
    for entry in extra_columns_spec:
        key = (entry["graph_slug"], entry["node_alias"])
        node = nodes_by_key.get(key)
        if node is not None and node.nodegroup_id in permitted_nodegroup_ids:
            resolved[key] = node
    return resolved


def _filter_permitted_related_resources(tiles_by_resource, user):
    related_resource_ids = set()
    for values in tiles_by_resource.values():
        for value in values:
            for detail in value.get("details") or []:
                if detail.get("resource_id"):
                    related_resource_ids.add(detail["resource_id"])

    if not related_resource_ids:
        return

    permitted_ids = set(
        str(pk)
        for pk in permission_backend.filter_resource_queryset(
            user, ResourceInstance.objects.filter(pk__in=related_resource_ids)
        ).values_list("resourceinstanceid", flat=True)
    )

    for values in tiles_by_resource.values():
        for value in values:
            details = value.get("details") or []
            permitted_details = [
                detail
                for detail in details
                if detail.get("resource_id") in permitted_ids
            ]

            value["details"] = permitted_details
            value["display_value"] = ", ".join(
                detail["display_value"] or "" for detail in permitted_details
            )
            value["node_value"] = [
                inner_val
                for inner_val in value.get("node_value") or []
                if inner_val and inner_val.get("resourceId") in permitted_ids
            ]


def attach_extra_columns(resources, extra_columns_spec, user):
    result = {}
    resourceinstanceids_by_graph_id = {}
    for resource in resources:
        resourceinstanceid = str(resource.pk)
        result[resourceinstanceid] = {}
        resourceinstanceids_by_graph_id.setdefault(resource.graph_id, []).append(
            resourceinstanceid
        )

    if not extra_columns_spec:
        return result

    resolved_nodes = resolve_node_refs(extra_columns_spec, user)
    graph_query_by_graph_slug = {}

    for entry in extra_columns_spec:
        node = resolved_nodes.get((entry["graph_slug"], entry["node_alias"]))
        if node is None:
            continue

        matching_resourceinstanceids = resourceinstanceids_by_graph_id.get(
            node.graph_id, []
        )
        if not matching_resourceinstanceids:
            continue

        values_by_resource = _resolve_column(
            entry, node, matching_resourceinstanceids, user, graph_query_by_graph_slug
        )
        for resourceinstanceid in matching_resourceinstanceids:
            result[resourceinstanceid][entry["node_alias"]] = values_by_resource.get(
                resourceinstanceid, []
            )

    return result


def _resolve_column(entry, node, resourceinstanceids, user, graph_query_by_graph_slug):
    try:
        graph_slug = entry["graph_slug"]
        # get_tiles() needs the graph's full node/nodegroup structure to
        # resolve tile.nodegroup correctly (~13 queries -- see
        # GraphWithPrefetchingQuerySet.prefetch) regardless of how narrowly
        # `nodes=` scopes the actual decode. That cost is real but paid at
        # most once per graph per request: every column sharing a graph_slug
        # reuses the same (already-evaluated) queryset instead of repeating it.
        if graph_slug not in graph_query_by_graph_slug:
            graph_query_by_graph_slug[graph_slug] = (
                GraphWithPrefetching.objects.prefetch(graph_slug)
            )

        tiles = TileTree.objects.get_tiles(
            graph_slug=graph_slug,
            nodegroup_alias=node.alias,
            resource_ids=resourceinstanceids,
            nodes=[node],
            depth=0,
            as_representation=True,
            graph_query=graph_query_by_graph_slug[graph_slug],
        )

        tiles_by_resource = {}
        for tile in tiles:
            value = getattr(tile.aliased_data, node.alias)
            tiles_by_resource.setdefault(str(tile.resourceinstance_id), []).append(
                value
            )

        if node.datatype in RESOURCE_INSTANCE_DATATYPES:
            _filter_permitted_related_resources(tiles_by_resource, user)

        return tiles_by_resource
    except Exception:
        logger.exception(
            "extra_columns: failed to resolve %s:%s -- returning [] for this column",
            entry["graph_slug"],
            entry["node_alias"],
        )
        return {}
