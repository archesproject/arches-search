"""
Projection of specific node (tile) values onto search results.

A search result row is a ResourceInstance, so a node's value is not on the row:
it lives in tile data. Filtering already handles that with existence subqueries,
but an Exists() answers only "does a matching value exist" -- it cannot be
selected or ordered by. This module annotates the *value itself* onto the result
queryset using arches_querysets' node-value expression, which makes the same
annotation usable for both display and sorting.

The annotation is applied before pagination so ordering applies to the whole
result set rather than to one page, and so the values arrive with the page
instead of costing a follow-up query per column.

Nodes that do not resolve, or whose nodegroup the requesting user cannot read,
are simply absent from the response. "No such node", "not permitted", and "that
resource is on a different graph" are deliberately indistinguishable.
"""

import logging
import hashlib
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches.app.models.models import Node
from arches.app.utils import permission_backend

from arches_querysets.models import TileTree
from arches_querysets.utils.models import get_tile_values_for_resource

# Namespaced so these cannot collide with a sort annotation or a real column.
ANNOTATION_PREFIX = "_arches_search_node_col_"

NodeColumnKey = Tuple[str, str]


logger = logging.getLogger(__name__)


def annotation_name_for(graph_slug: str, node_alias: str) -> str:
    """
    Deterministic annotation name for a (graph, node) pair.

    Deterministic rather than positional so a column requested both for display
    and as a sort key resolves to one annotation instead of two. Hashed rather
    than concatenated so that ("a", "b_c") and ("a_b", "c") cannot collide, and
    so an alias containing characters that are illegal in a kwarg name is safe.
    """
    digest = hashlib.sha1(f"{graph_slug}\x1f{node_alias}".encode("utf-8")).hexdigest()[
        :16
    ]
    return f"{ANNOTATION_PREFIX}{digest}"


def validate_extra_columns(extra_columns: Any) -> None:
    if extra_columns is None:
        return
    if not isinstance(extra_columns, list):
        raise ValidationError(_("extra_columns must be a list."))

    for index, entry in enumerate(extra_columns):
        if not isinstance(entry, dict):
            raise ValidationError(
                _("extra_columns[%(i)s] must be an object.") % {"i": index}
            )
        for key in ("graph_slug", "node_alias"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                raise ValidationError(
                    _("extra_columns[%(i)s] requires a non-empty %(key)s.")
                    % {"i": index, "key": key}
                )


def column_keys(extra_columns: Optional[List[Dict[str, Any]]]) -> List[NodeColumnKey]:
    if not extra_columns:
        return []
    seen: List[NodeColumnKey] = []
    for entry in extra_columns:
        key = (entry["graph_slug"], entry["node_alias"])
        if key not in seen:
            seen.append(key)
    return seen


def resolve_node_columns(
    keys: Iterable[NodeColumnKey], user
) -> Dict[NodeColumnKey, Node]:
    """
    Resolve (graph_slug, node_alias) pairs to Node rows the user may read.

    Unresolvable and unpermitted keys are dropped rather than reported, so the
    response cannot be used to probe which nodes exist.
    """
    keys = list(keys)
    if not keys:
        return {}

    graph_slugs = {graph_slug for graph_slug, _alias in keys}
    node_aliases = {node_alias for _slug, node_alias in keys}

    candidate_nodes = (
        Node.objects.filter(
            graph__slug__in=graph_slugs,
            alias__in=node_aliases,
            source_identifier=None,
        )
        .exclude(datatype="semantic")
        .exclude(nodegroup=None)
        .select_related("nodegroup", "graph")
    )

    readable_nodegroups = set(
        permission_backend.get_nodegroups_by_perm(user, "models.read_nodegroup")
    )
    readable_nodegroup_ids = {
        getattr(nodegroup, "pk", nodegroup) for nodegroup in readable_nodegroups
    }

    nodes_by_key = {}
    for node in candidate_nodes:
        key = (node.graph.slug, node.alias)
        if key not in keys:
            continue
        if node.nodegroup_id not in readable_nodegroup_ids:
            continue
        nodes_by_key[key] = node

    return nodes_by_key


def _graph_nodes_for(graph_slug: str) -> List[Node]:
    """
    Every node of a graph, which get_tile_values_for_resource() needs in order
    to work out whether any nodegroup in the node's hierarchy is cardinality-n.
    """
    return list(
        Node.objects.filter(graph__slug=graph_slug, source_identifier=None)
        .exclude(datatype="semantic")
        .exclude(nodegroup=None)
        .select_related("nodegroup__parentnodegroup")
    )


def annotate_node_columns(queryset, nodes_by_key: Dict[NodeColumnKey, Node]):
    """
    Annotate each resolved node's value onto the resource queryset.

    Returns (queryset, {key: annotation_name}).
    """
    if not nodes_by_key:
        return queryset, {}

    graph_nodes_cache: Dict[str, List[Node]] = {}
    annotations: Dict[str, Any] = {}
    annotation_names: Dict[NodeColumnKey, str] = {}

    for key, node in nodes_by_key.items():
        graph_slug, node_alias = key
        if graph_slug not in graph_nodes_cache:
            graph_nodes_cache[graph_slug] = _graph_nodes_for(graph_slug)

        annotation_name = annotation_name_for(graph_slug, node_alias)
        annotations[annotation_name] = get_tile_values_for_resource(
            node, graph_nodes_cache[graph_slug]
        )
        annotation_names[key] = annotation_name

    return queryset.annotate(**annotations), annotation_names


def format_node_columns(
    resources,
    nodes_by_key: Dict[NodeColumnKey, Node],
    annotation_names: Dict[NodeColumnKey, str],
) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Build {resourceinstanceid: {node_alias: [{node_value, display_value,
    details}, ...]}} from values already annotated onto the fetched rows.

    Values are always a list, even for a cardinality-1 node, so a client does
    not have to branch on cardinality.
    """
    if not nodes_by_key:
        return {}

    columns_by_resource: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for resource in resources:
        resource_id = str(resource.pk)
        columns: Dict[str, List[Dict[str, Any]]] = {}

        for key, node in nodes_by_key.items():
            graph_slug, node_alias = key
            # A resource on another graph simply has no value for this column.
            if (
                str(getattr(resource, "graph_id", ""))
                and resource.graph.slug != graph_slug
            ):
                continue

            raw_value = getattr(resource, annotation_names[key], None)
            values = raw_value if isinstance(raw_value, list) else [raw_value]

            formatted = []
            for value in values:
                if value is None:
                    continue
                try:
                    # An unsaved TileTree is enough to format a value: the
                    # display path reads the value out of tile.data, so putting
                    # the annotated value there gives the same result a
                    # persisted tile would, with no arches-querysets change.
                    stand_in_tile = TileTree(
                        data={str(node.pk): value}, resourceinstance=resource
                    )
                    formatted.append(stand_in_tile.get_value_with_context(node, value))
                except Exception:
                    # One misconfigured node must not take down the whole
                    # response; that column is simply omitted for this row.
                    # Logged rather than passed over silently: swallowing this
                    # makes a broken formatter indistinguishable from a
                    # resource that genuinely has no value for the column.
                    logger.warning(
                        "Could not format node column %s for resource %s",
                        node_alias,
                        resource_id,
                        exc_info=True,
                    )
                    continue
            columns[node_alias] = formatted

        columns_by_resource[resource_id] = columns

    return columns_by_resource
