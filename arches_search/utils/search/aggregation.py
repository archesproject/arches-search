"""
Grouped counts and metrics over the whole result set.

Group-bys and metrics name a NODE by graph_slug and node_alias, or a
RESOURCE_FIELD by field, and resolve through the same registries clauses use.
Functions come from AGGREGATE_FUNCTIONS. Nothing in a request reaches the ORM
as a lookup, a table name or a function name.
"""

from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, Union

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, OuterRef, QuerySet, Subquery
from django.utils.translation import gettext as _

from arches.app.models.models import TileModel

from arches_search.utils.advanced_search.registries.node_alias_datatype_registry import (
    NodeAliasDatatypeRegistry,
)
from arches_search.utils.advanced_search.registries.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.readable_nodes import ReadableNodes
from arches_search.utils.resource_field_search.field_registry import (
    get_resource_instance_fields,
)
from arches_search.utils.resource_field_search.grouping import (
    is_resource_field_spec,
    resolve_group_by_path,
    resolve_metric_path,
)

AGGREGATE_FUNCTIONS: Dict[str, Callable[..., Any]] = {
    "Count": models.Count,
    "Sum": models.Sum,
    "Avg": models.Avg,
    "Min": models.Min,
    "Max": models.Max,
}


def get_aggregate_function(fn_name: str) -> Callable[..., Any]:
    """
    Looked up in AGGREGATE_FUNCTIONS rather than on django.db.models, where a
    name could reach any expression class.
    """
    try:
        return AGGREGATE_FUNCTIONS[fn_name]
    except KeyError:
        raise ValidationError(
            _("Unknown aggregate function: %(fn)s."), params={"fn": fn_name}
        )


class NodeRowResolver:
    """
    Resolves a NODE spec to its rows in the search index table for its datatype.

    Resolution goes through NodeAliasDatatypeRegistry, so a node the user cannot
    read is refused exactly as a clause naming it would be.
    """

    def __init__(self, readable_nodes: ReadableNodes) -> None:
        self._node_registry = NodeAliasDatatypeRegistry(readable_nodes=readable_nodes)

    @cached_property
    def _search_model_registry(self) -> SearchModelRegistry:
        # Built on first use: it costs a query, and an aggregation over resource
        # fields alone never needs it.
        return SearchModelRegistry()

    def rows_for(self, node_spec: Dict[str, Any]) -> QuerySet:
        graph_slug = node_spec["graph_slug"]
        node_alias = node_spec["node_alias"]
        datatype_name = self._node_registry.get_datatype_for_alias(
            graph_slug, node_alias
        )

        try:
            model_class = self._search_model_registry.get_value_model_for_datatype(
                datatype_name
            )
        except ValueError:
            raise ValidationError(
                _("%(graph_slug)s node %(node_alias)s has no value to aggregate."),
                params={"graph_slug": graph_slug, "node_alias": node_alias},
            )

        return self._node_registry.node_rows(model_class, graph_slug, node_alias)


def build_value_subquery(
    node_rows: QuerySet,
    node_alias: str,
    parent_ref_field: str = "resourceinstanceid",
    fn: Optional[str] = None,
    aggregate_by_tile: Optional[bool] = False,
    value_field: str = "value",
    annotations: Optional[Dict[str, Any]] = None,
    outer_aggregate_by_tile: Optional[bool] = False,
) -> Subquery:
    """
    Build a base Subquery returning a single value from a node's search index rows.

    Typically used as a building block for group-by or metric aggregations.

    Args:
        node_rows (QuerySet): The node's rows, from NodeRowResolver.
        node_alias (str): The node's alias, used to name an aggregated value.
        parent_ref_field (str, optional): The column name to join outer and subqueries on.
            Defaults to "resourceinstanceid".
        fn (str, optional): An aggregate function name to apply (e.g., "Sum", "Avg").
            If provided, the subquery will return the aggregated value.
        aggregate_by_tile (bool, optional): Whether to apply the aggregate function
            per tile before aggregating at the resource level. Defaults to False.
        value_field (str, optional): The field to select as the subquery value.
            Defaults to "value".
        annotations (dict, optional): Extra annotations to apply before subquery selection.
        outer_aggregate_by_tile (bool, optional): Indicates if the parent query is aggregating by tile.
            This affects how we join the subquery to the parent query.  Defaults to False.

    Returns:
        Subquery: A Django ORM Subquery returning the specified field value.
    """
    filters = {}
    if aggregate_by_tile:
        filters["tileid"] = OuterRef(parent_ref_field)
    else:
        if outer_aggregate_by_tile == True and aggregate_by_tile == False:
            # When "joining" the Tiles table to the ResourceInstances table we need
            # to reference resources via resourceinstance_id rather than resourceinstanceid
            filters["resourceinstanceid"] = OuterRef("resourceinstance_id")
        else:
            filters["resourceinstanceid"] = OuterRef(parent_ref_field)
    qs = node_rows.filter(**filters)

    if annotations:
        qs = qs.annotate(**annotations)

    if fn:
        if aggregate_by_tile == False and fn != "Count":
            fn = "Sum"
        aggregate_fn = get_aggregate_function(fn)
        aggregated_value_field = f"{fn.lower()}_{node_alias}"
        qs = (
            qs.values(parent_ref_field)
            .annotate(**{aggregated_value_field: aggregate_fn(value_field)})
            .values(aggregated_value_field)
        )
        return Subquery(qs[:1])
    return Subquery(qs.values(value_field)[:1])


def build_subquery(
    query_def: Dict[str, Any],
    node_row_resolver: NodeRowResolver,
    parent_ref_field: str = "resourceinstanceid",
    aggregate_by_tile: bool = False,
) -> Subquery:
    """
    This function constructs a subquery that can be used to retrieve and aggregate data
    from search tables. It supports nested aggregations and tile-level aggregation,
    allowing for complex hierarchical data queries.


    Args:
        query_def (Dict[str, Any]): A NODE spec defining the subquery structure with keys:
            - graph_slug (str): The graph the node belongs to
            - node_alias (str): The alias for the node being queried
            - fn (optional): Aggregation function to apply
            - aggregate_by_tile (bool, optional): Whether to aggregate at tile level
            - aggregations (list, optional): List of nested aggregation specifications

        node_row_resolver (NodeRowResolver): Resolves each node to its rows.

        parent_ref_field (str, optional): The column name used to join the outer query
            with this subquery. Defaults to "resourceinstanceid".
            Should be set to True when grouped fields are at the tile level with
            cardinality n and metrics are on the same tile. Defaults to False.

        aggregate_by_tile (bool, optional): Whether to aggregate data per tile.
            Set to True when your grouped fields are at the tile level and are cardinality n
            and when your metrics are on the same tile. Defaults to False.

    Returns:
        Subquery: A constructed nested Subquery object that can be used in Django ORM
            queries or further nested in other subqueries.

    Raises:
        ValidationError: If the node does not resolve, or if attempting to build a
            tile-aggregated subquery when the parent query is not aggregating by tile.

    Notes:
        - The function validates that tile-level aggregation is consistent between
          parent and child queries
        - Nested aggregations are processed recursively, with each level building
          upon the previous subquery
        - The parent_ref_field changes to "value" for nested recursive calls
    """

    if aggregate_by_tile == False and query_def.get("aggregate_by_tile", None) == True:
        raise ValidationError(
            _(
                "Cannot build subquery that aggregates by tile when parent query is not aggregating by tile."
            )
        )

    node_rows = node_row_resolver.rows_for(query_def)
    subquery = build_value_subquery(
        node_rows,
        query_def["node_alias"],
        parent_ref_field=parent_ref_field,
        fn=query_def.get("fn"),
        aggregate_by_tile=query_def.get("aggregate_by_tile", aggregate_by_tile),
        outer_aggregate_by_tile=aggregate_by_tile,
    )

    # Handle nested aggregations recursively
    for agg in query_def.get("aggregations", []):
        for nested_group in agg.get("group_by", []):
            nested_subquery = build_subquery(
                nested_group,
                node_row_resolver,
                parent_ref_field="value",
                aggregate_by_tile=aggregate_by_tile,
            )
            subquery = build_value_subquery(
                node_rows,
                query_def["node_alias"],
                parent_ref_field=parent_ref_field,
                value_field=nested_group["alias"],
                annotations={nested_group["alias"]: nested_subquery},
                aggregate_by_tile=aggregate_by_tile,
            )

    return subquery


def _needs_resource_field_registry(aggregations: List[Dict[str, Any]]) -> bool:
    """
    Whether any spec here names a resource field.

    Checked up front because building the registry costs a query, and an
    aggregation over node values alone never touches it.
    """
    return any(
        is_resource_field_spec(spec)
        for aggregation in aggregations
        for spec in (aggregation.get("group_by") or [])
        + (aggregation.get("metrics") or [])
    )


def build_aggregations(
    queryset: QuerySet,
    aggregations: List[Dict[str, Any]],
    readable_nodes: ReadableNodes,
) -> Dict[str, Union[List[Dict[str, Any]], Dict[str, Any]]]:
    """
    Build and evaluate aggregations on a queryset.

    Supports both grouped metric aggregations and simple global aggregates.

    Args:
        queryset (QuerySet): The base queryset to aggregate.
        aggregations (list[dict]): Aggregation specifications that define grouping,
            metrics, and/or direct aggregate operations.
        readable_nodes (ReadableNodes): Which nodes the aggregations may read.

    Returns:
        dict: A dictionary mapping aggregation names to their computed results.
            Each value is either a list of grouped records or a dictionary of aggregate values.
    """
    results: Dict[str, Union[List[Dict[str, Any]], Dict[str, Any]]] = {}

    # Built once: resolving each spec separately rebuilt it every time.
    resource_field_registry = (
        get_resource_instance_fields()
        if _needs_resource_field_registry(aggregations)
        else None
    )
    node_row_resolver = NodeRowResolver(readable_nodes)

    for agg in aggregations:
        name = agg["name"]

        group_bys = agg.get("group_by", [])
        metrics = agg.get("metrics", [])

        aggregate_by_tile = agg.get("aggregate_by_tile", False)
        if aggregate_by_tile:
            parent_ref_field = "tileid"
            local_queryset = TileModel.objects.filter(resourceinstance_id__in=queryset)
        else:
            parent_ref_field = "resourceinstanceid"
            local_queryset = queryset

        # Apply group-by subqueries
        for group_spec in group_bys:
            field_alias = group_spec["alias"]
            if is_resource_field_spec(group_spec):
                # A resource field is already a column on the row being grouped,
                # so it needs a plain reference rather than a correlated subquery.
                local_queryset = local_queryset.annotate(
                    **{
                        field_alias: F(
                            resolve_group_by_path(
                                group_spec,
                                aggregate_by_tile=aggregate_by_tile,
                                registry=resource_field_registry,
                            )
                        )
                    }
                )
                continue
            local_queryset = local_queryset.annotate(
                **{
                    field_alias: build_subquery(
                        group_spec,
                        node_row_resolver,
                        parent_ref_field=parent_ref_field,
                        aggregate_by_tile=aggregate_by_tile,
                    )
                }
            )

        # Define metric-level aggregations
        metric_annotations: Dict[str, Any] = {}
        for metric_spec in metrics:
            alias = metric_spec["alias"]
            fn = metric_spec["fn"]
            if is_resource_field_spec(metric_spec):
                # Aggregating a column of the row itself (e.g. counting rows per
                # group) needs a plain aggregate, not a correlated subquery, and
                # must skip the Count->Sum rewrite below, which exists only to
                # roll per-tile counts up to the resource.
                metric_annotations[alias] = get_aggregate_function(fn)(
                    resolve_metric_path(
                        metric_spec,
                        aggregate_by_tile=aggregate_by_tile,
                        registry=resource_field_registry,
                    )
                )
                continue
            # we need to handle Count differently because when we do counts per resource
            # we want to sum the counts of each tile, not count the counts from each tile
            # which would always be 1 per resource
            if aggregate_by_tile == False and fn == "Count":
                fn = "Sum"
            aggregate_fn = get_aggregate_function(fn)
            subquery = build_subquery(
                metric_spec,
                node_row_resolver,
                parent_ref_field=parent_ref_field,
                aggregate_by_tile=aggregate_by_tile,
            )
            metric_annotations[alias] = aggregate_fn(subquery)

        # Only the requested columns come back, never whole rows.
        group_fields = [g["alias"] for g in group_bys]
        local_queryset = local_queryset.order_by().values(*group_fields)
        if metric_annotations:
            local_queryset = local_queryset.annotate(**metric_annotations)

        results[name] = list(local_queryset)

        # Handle "simple" aggregates over the columns requested above
        for aggregate in agg.get("aggregate", []):
            aggregate_fn = get_aggregate_function(aggregate["fn"])
            alias = aggregate["alias"]
            results[alias] = local_queryset.aggregate(
                **{
                    alias: aggregate_fn(
                        aggregate["field"], distinct=bool(aggregate.get("distinct"))
                    )
                }
            )[alias]

    return results
