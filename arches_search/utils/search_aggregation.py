"""
Utility functions for building nested subqueries and aggregations
used in advanced search queries within the Arches search system.
"""

from arches.app.models.models import TileModel
from django.apps import apps
from django.db import models
from django.db.models import OuterRef, Subquery, Q, QuerySet
from typing import Optional, Dict, Any, List, Union, Callable


def get_search_model(search_table: str) -> models.Model:
    """
    Retrieve the Django model associated with a given search table name.

    Args:
        search_table (str): The key identifying a search table.

    Returns:
        models.Model: The model class associated with the given search table.

    Raises:
        ValueError: If the search table name is not found in SEARCH_TABLE_TO_MODEL.
    """
    arches_search_config = apps.get_app_config("arches_search")

    for model_class in arches_search_config.get_models():
        if model_class._meta.db_table == search_table:
            return model_class

    raise ValueError(f"Unknown search table '{search_table}'")


def get_aggregate_function(fn_name: str) -> Callable[..., Any]:
    """
    Return a Django aggregate function by its name (e.g., "Sum", "Avg").

    Args:
        fn_name (str): The name of the aggregate function.

    Returns:
        Callable[..., Any]: The corresponding Django aggregate function class.

    Raises:
        ValueError: If no aggregate function matches the provided name.
    """
    try:
        return getattr(models, fn_name)
    except AttributeError:
        raise ValueError(f"Unknown aggregate function: {fn_name}")


def build_value_subquery(
    search_table_name: str,
    node_alias: str,
    parent_ref_field: str = "resourceinstanceid",
    where: Optional[Dict[str, Any]] = None,
    fn: Optional[str] = None,
    aggregate_by_tile: Optional[bool] = False,
    value_field: str = "value",
    annotations: Optional[Dict[str, Any]] = None,
    override_outer_ref: bool = False,
) -> Subquery:
    """
    Build a base Subquery returning a single value from a search table.

    Typically used as a building block for group-by or metric aggregations.

    Args:
        search_table_name (str): The search table used to look up the model.
        node_alias (str): The node alias used to filter the queryset.
        parent_ref_field (str, optional): The column name to join outer and subqueries on.
            Defaults to "resourceinstanceid".
        where (dict, optional): Additional filter conditions to apply.
        fn (str, optional): An aggregate function name to apply (e.g., "Sum", "Avg").
            If provided, the subquery will return the aggregated value.
        aggregate_by_tile (bool, optional): Whether to apply the aggregate function
            per tile before aggregating at the resource level. Defaults to False.
        value_field (str, optional): The field to select as the subquery value.
            Defaults to "value".
        annotations (dict, optional): Extra annotations to apply before subquery selection.

    Returns:
        Subquery: A Django ORM Subquery returning the specified field value.
    """
    search_model = get_search_model(search_table_name)

    filters = {"node_alias": node_alias}
    if aggregate_by_tile:
        filters["tileid"] = OuterRef(parent_ref_field)
    else:
        if override_outer_ref:
            filters["resourceinstanceid"] = OuterRef("resourceinstance_id")
        else:
            filters["resourceinstanceid"] = OuterRef("resourceinstanceid")
    qs = search_model.objects.filter(**filters)

    if annotations:
        qs = qs.annotate(**annotations)

    if where:
        qs = qs.filter(**where)

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
    parent_ref_field: str = "resourceinstanceid",
    aggregate_by_tile: bool = False,
) -> Subquery:
    """
    This function constructs a subquery that can be used to retrieve and aggregate data
    from search tables. It supports nested aggregations and tile-level aggregation,
    allowing for complex hierarchical data queries.


    Args:
        query_def (Dict[str, Any]): A dictionary defining the subquery structure with keys:
            - search_table (str): The name of the search table to query
            - node_alias (str): The alias for the node being queried
            - where (optional): Filter conditions for the subquery
            - fn (optional): Aggregation function to apply
            - aggregate_by_tile (bool, optional): Whether to aggregate at tile level
            - aggregations (list, optional): List of nested aggregation specifications

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
        Exception: If attempting to build a tile-aggregated subquery when the parent
            query is not aggregating by tile.

    Notes:
        - The function validates that tile-level aggregation is consistent between
          parent and child queries
        - Nested aggregations are processed recursively, with each level building
          upon the previous subquery
        - The parent_ref_field changes to "value" for nested recursive calls
    """

    if aggregate_by_tile == False and query_def.get("aggregate_by_tile", None) == True:
        raise Exception(
            "Cannot build subquery that aggregates by tile when parent query is not aggregating by tile."
        )

    override_outer_ref = query_def.get("aggregate_by_tile", None) != None

    subquery = build_value_subquery(
        search_table_name=query_def["search_table"],
        node_alias=query_def["node_alias"],
        parent_ref_field=parent_ref_field,
        where=query_def.get("where"),
        fn=query_def.get("fn"),
        aggregate_by_tile=query_def.get("aggregate_by_tile", aggregate_by_tile),
        override_outer_ref=override_outer_ref,
    )

    # Handle nested aggregations recursively
    for agg in query_def.get("aggregations", []):
        for nested_group in agg.get("group_by", []):
            nested_subquery = build_subquery(
                nested_group,
                parent_ref_field="value",
                aggregate_by_tile=aggregate_by_tile,
            )
            subquery = build_value_subquery(
                search_table_name=query_def["search_table"],
                node_alias=query_def["node_alias"],
                parent_ref_field=parent_ref_field,
                where=query_def.get("where"),
                value_field=nested_group["alias"],
                annotations={nested_group["alias"]: nested_subquery},
                aggregate_by_tile=aggregate_by_tile,
            )

    return subquery


def build_aggregations(
    queryset: QuerySet,
    aggregations: List[Dict[str, Any]],
) -> Dict[str, Union[List[Dict[str, Any]], Dict[str, Any]]]:
    """
    Build and evaluate aggregations on a queryset.

    Supports both grouped metric aggregations and simple global aggregates.

    Args:
        queryset (QuerySet): The base queryset to aggregate.
        aggregations (list[dict]): Aggregation specifications that define grouping,
            metrics, and/or direct aggregate operations.

    Returns:
        dict: A dictionary mapping aggregation names to their computed results.
            Each value is either a list of grouped records or a dictionary of aggregate values.
    """
    results: Dict[str, Union[List[Dict[str, Any]], Dict[str, Any]]] = {}

    for agg in aggregations:
        name = agg["name"]

        group_bys = agg.get("group_by", [])
        metrics = agg.get("metrics", [])
        where_clause = agg.get("where", None)

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
            local_queryset = local_queryset.annotate(
                **{
                    field_alias: build_subquery(
                        group_spec,
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
            # we need to handle Count differently because when we do counts per resource
            # we want to sum the counts of each tile, not count the counts from each tile
            # which would always be 1 per resource
            if aggregate_by_tile == False and fn == "Count":
                fn = "Sum"
            aggregate_fn = get_aggregate_function(fn)
            subquery = build_subquery(
                metric_spec,
                parent_ref_field=parent_ref_field,
                aggregate_by_tile=aggregate_by_tile,
            )
            metric_annotations[alias] = aggregate_fn(subquery)

        # Apply metric annotations and group-by fields
        if metric_annotations:
            group_fields = [g["alias"] for g in group_bys]
            local_queryset = local_queryset.values(*group_fields).annotate(
                **metric_annotations
            )

        if where_clause:
            local_queryset = local_queryset.filter(**where_clause)

        results[name] = list(local_queryset)

        # Handle "simple" aggregates on the current queryset level
        if "aggregate" in agg:
            for aggregate in agg["aggregate"]:
                field = aggregate.get("field", "value")
                aggregate_fn = get_aggregate_function(aggregate["fn"])
                kwargs = dict(aggregate.get("kwargs") or {})

                if aggregate.get("where"):
                    kwargs["filter"] = Q(**aggregate.get("where"))
                if aggregate.get("distinct"):
                    kwargs["distinct"] = True

                results[aggregate.get("alias")] = local_queryset.aggregate(
                    **{aggregate.get("alias"): aggregate_fn(field, **kwargs)}
                )[aggregate.get("alias")]

    return results
