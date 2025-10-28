"""
Utility functions for building nested subqueries and aggregations
used in advanced search queries within the Arches search system.
"""

from django.db import models
from django.db.models import OuterRef, Subquery, Q, QuerySet
from typing import Optional, Dict, Any, List, Union, Callable

from arches_search.utils.advanced_search import SEARCH_TABLE_TO_MODEL


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
    try:
        return SEARCH_TABLE_TO_MODEL[search_table]
    except KeyError:
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
    search_table: str,
    node_alias: str,
    parent_ref_field: str = "resourceinstanceid",
    where: Optional[Dict[str, Any]] = None,
    value_field: str = "value",
    annotations: Optional[Dict[str, Any]] = None,
) -> Subquery:
    """
    Build a base Subquery returning a single value from a search table.

    Typically used as a building block for group-by or metric aggregations.

    Args:
        search_table (str): The search table used to look up the model.
        node_alias (str): The node alias used to filter the queryset.
        parent_ref_field (str, optional): The reference field in the parent queryset.
            Defaults to "resourceinstanceid".
        where (dict, optional): Additional filter conditions to apply.
        value_field (str, optional): The field to select as the subquery value.
            Defaults to "value".
        annotations (dict, optional): Extra annotations to apply before subquery selection.

    Returns:
        Subquery: A Django ORM Subquery returning the specified field value.
    """
    model = get_search_model(search_table)
    filters = {
        "node_alias": node_alias,
        "resourceinstanceid": OuterRef(parent_ref_field),
    }
    qs = model.objects.filter(**filters)
    if annotations:
        qs = qs.annotate(**annotations)
    if where:
        qs = qs.filter(**where)
    return Subquery(qs.values(value_field)[:1])


def build_subquery(
    group_spec: Dict[str, Any],
    parent_ref_field: str = "resourceinstanceid",
) -> Subquery:
    """
    Recursively build nested subqueries for deeply linked nodes in group-by specifications.

    Args:
        group_spec (dict): The group specification containing search table, node alias,
            and potentially nested aggregations.
        parent_ref_field (str, optional): The field in the parent queryset to reference.
            Defaults to "resourceinstanceid".

    Returns:
        Subquery: The constructed nested Subquery.
    """
    subquery = build_value_subquery(
        search_table=group_spec["search_table"],
        node_alias=group_spec["node_alias"],
        parent_ref_field=parent_ref_field,
        where=group_spec.get("where"),
    )

    # Handle nested aggregations recursively
    for agg in group_spec.get("aggregations", []):
        for nested_group in agg.get("group_by", []):
            nested_subquery = build_subquery(nested_group, parent_ref_field="value")
            subquery = build_value_subquery(
                search_table=group_spec["search_table"],
                node_alias=group_spec["node_alias"],
                parent_ref_field=parent_ref_field,
                where=group_spec.get("where"),
                value_field=nested_group["alias"],
                annotations={nested_group["alias"]: nested_subquery},
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
        local_queryset = queryset

        # Apply group-by subqueries
        for group_spec in group_bys:
            field_alias = group_spec["alias"]
            local_queryset = local_queryset.annotate(
                **{field_alias: build_subquery(group_spec)}
            )

        # Define metric-level aggregations
        metric_annotations: Dict[str, Any] = {}
        for metric_spec in metrics:
            alias = metric_spec["alias"]
            aggregate_fn = get_aggregate_function(metric_spec["fn"])
            subquery = build_subquery(metric_spec)
            metric_annotations[alias] = aggregate_fn(subquery)

        # Apply metric annotations and group-by fields
        if metric_annotations:
            group_fields = [g["alias"] for g in group_bys]
            local_queryset = local_queryset.values(*group_fields).annotate(
                **metric_annotations
            )

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
