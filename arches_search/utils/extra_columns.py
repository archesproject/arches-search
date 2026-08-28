import logging

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches.app.models.models import Node
from arches.app.utils import permission_backend

from arches_querysets.models import GraphWithPrefetching, TileTree

logger = logging.getLogger(__name__)


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


def attach_extra_columns(resources, extra_columns_spec, user):
    if not extra_columns_spec:
        return {str(resource.pk): {} for resource in resources}

    result = {}
    resourceinstanceids_by_graph_id = {}
    for resource in resources:
        resourceinstanceid = str(resource.pk)
        result[resourceinstanceid] = {}
        resourceinstanceids_by_graph_id.setdefault(resource.graph_id, []).append(
            resourceinstanceid
        )

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

        return tiles_by_resource
    except Exception:
        logger.exception(
            "extra_columns: failed to resolve %s:%s -- returning [] for this column",
            entry["graph_slug"],
            entry["node_alias"],
        )
        return {}
