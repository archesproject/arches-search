"""
Utility functions for building nested subqueries and aggregations
used in advanced search queries within the Arches search system.
"""

from sqlparse import format

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
    parent_ref_field: str = "tileid",
    where: Optional[Dict[str, Any]] = None,
    fn: Optional[str] = None,
    apply_agg_fn_per_tile: Optional[bool] = False,
    value_field: str = "value",
    annotations: Optional[Dict[str, Any]] = None,
) -> Subquery:
    """
    Build a base Subquery returning a single value from a search table.

    Typically used as a building block for group-by or metric aggregations.

    Args:
        search_table_name (str): The search table used to look up the model.
        node_alias (str): The node alias used to filter the queryset.
        parent_ref_field (str, optional): The reference field in the parent queryset.
            Defaults to "resourceinstanceid".
        where (dict, optional): Additional filter conditions to apply.
        fn (str, optional): An aggregate function name to apply (e.g., "Sum", "Avg").
            If provided, the subquery will return the aggregated value.
        apply_agg_fn_per_tile (bool, optional): Whether to apply the aggregate function
            per tile before aggregating at the resource level. Defaults to False.
        value_field (str, optional): The field to select as the subquery value.
            Defaults to "value".
        annotations (dict, optional): Extra annotations to apply before subquery selection.

    Returns:
        Subquery: A Django ORM Subquery returning the specified field value.
    """
    search_model = get_search_model(search_table_name)
    if apply_agg_fn_per_tile:
        filters = {
            "node_alias": node_alias,
            "tileid": OuterRef(parent_ref_field),
        }
    else:
        filters = {
            "node_alias": node_alias,
            "resourceinstanceid": OuterRef(parent_ref_field),
        }
    qs = search_model.objects.filter(**filters)
    if annotations:
        qs = qs.annotate(**annotations)
    if where:
        qs = qs.filter(**where)
    if fn:
        if apply_agg_fn_per_tile == False and fn != "Count":
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
    group_spec: Dict[str, Any],
    parent_ref_field: str = "tileid",
    apply_agg_fn_per_tile: bool = False,
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
        search_table_name=group_spec["search_table"],
        node_alias=group_spec["node_alias"],
        parent_ref_field=parent_ref_field,
        where=group_spec.get("where"),
        fn=group_spec.get("fn"),
        apply_agg_fn_per_tile=apply_agg_fn_per_tile,
    )

    # Handle nested aggregations recursively
    for agg in group_spec.get("aggregations", []):
        for nested_group in agg.get("group_by", []):
            nested_subquery = build_subquery(
                nested_group,
                parent_ref_field="value",
                apply_agg_fn_per_tile=apply_agg_fn_per_tile,
            )
            subquery = build_value_subquery(
                search_table_name=group_spec["search_table"],
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
        apply_agg_fn_per_tile = agg.get("apply_agg_fn_per_tile", False)
        if apply_agg_fn_per_tile:
            parent_ref_field = "tileid"
            local_queryset = TileModel.objects.filter(resourceinstance_id__in=queryset)
        else:
            parent_ref_field = "resourceinstanceid"
            local_queryset = queryset
        # local_queryset.filter(tilemodel__tileid__isnull=False)
        # import ipdb

        # ipdb.sset_trace()

        # Apply group-by subqueries
        for group_spec in group_bys:
            field_alias = group_spec["alias"]
            local_queryset = local_queryset.annotate(
                **{
                    field_alias: build_subquery(
                        group_spec,
                        parent_ref_field=parent_ref_field,
                        apply_agg_fn_per_tile=apply_agg_fn_per_tile,
                    )
                }
            )

        # Define metric-level aggregations
        metric_annotations: Dict[str, Any] = {}
        for metric_spec in metrics:
            alias = metric_spec["alias"]
            fn = metric_spec["fn"]
            # apply_agg_fn_per_tile = metric_spec.get("apply_agg_fn_per_tile", False)
            # we need to handle Count differently because when we do counts per resource
            # we want to sum the counts of each tile, not count the counts from each tile
            # which would always be 1 per resource
            if apply_agg_fn_per_tile == False and fn == "Count":
                fn = "Sum"
            aggregate_fn = get_aggregate_function(fn)
            subquery = build_subquery(
                metric_spec,
                parent_ref_field=parent_ref_field,
                apply_agg_fn_per_tile=apply_agg_fn_per_tile,
            )
            metric_annotations[alias] = aggregate_fn(subquery)

        # Apply metric annotations and group-by fields
        if metric_annotations:
            group_fields = [g["alias"] for g in group_bys]
            local_queryset = local_queryset.values(*group_fields).annotate(
                **metric_annotations
            )

        if name == "allocation_per_device_type":
            formatted_sql = format(
                str(local_queryset.query), reindent=True, keyword_case="upper"
            )
            print(formatted_sql)

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
