from django.db import models
from django.db.models import OuterRef, Subquery, Q
from typing import Optional, Dict, Any

from arches_search.utils.advanced_search import SEARCH_TABLE_TO_MODEL


def get_search_model(search_table: str):
    try:
        return SEARCH_TABLE_TO_MODEL[search_table]
    except KeyError:
        raise ValueError(f"Unknown search table '{search_table}'")


def get_aggregate_function(fn_name: str):
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
    Builds a base Subquery that returns a single 'value' field by default
      from the given search table.
    Shared by both group_by and metric builders.
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


def build_subquery(group_spec, parent_ref_field="resourceinstanceid"):
    """
    Recursively build nested subqueries for deeply linked nodes.
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
            nested_field = nested_group["field"]

            # Annotate the current subquery with the nested subquery
            subquery = build_value_subquery(
                search_table=group_spec["search_table"],
                node_alias=group_spec["node_alias"],
                parent_ref_field=parent_ref_field,
                where=group_spec.get("where"),
                value_field=nested_group["field"],
                annotations={nested_group["field"]: nested_subquery},
            )

    return subquery


def build_aggregations(queryset, aggregations):
    results = {}

    for agg in aggregations:
        name = agg["name"]

        group_bys = agg.get("group_by", [])
        metrics = agg.get("metrics", [])
        local_queryset = queryset

        for group_spec in group_bys:
            field_alias = group_spec["field"]
            local_queryset = local_queryset.annotate(
                **{field_alias: build_subquery(group_spec)}
            )

        metric_annotations = {}
        for metric_spec in metrics:
            alias = metric_spec["alias"]
            aggregate_fn = get_aggregate_function(metric_spec["fn"])

            subquery = build_subquery(metric_spec)
            metric_annotations[alias] = aggregate_fn(subquery)

        if metric_annotations:
            group_fields = [g["field"] for g in group_bys]
            local_queryset = local_queryset.values(*group_fields).annotate(
                **metric_annotations
            )

        results[name] = list(local_queryset)

        # These "simple" aggregates operate on the entire local queryset level
        # and essentially ignore any grouping but allow for further aggregation of the annotated values.
        # These values are returned as a single dictionary keyed by the aggregation name.
        if "aggregate" in agg:
            for aggregate in agg["aggregate"]:
                field = aggregate.get("field", "value")
                aggregate_fn = get_aggregate_function(aggregate["fn"])
                kwargs = dict(aggregate.get("kwargs") or {})

                if aggregate.get("where"):
                    kwargs["filter"] = Q(**aggregate.get("where"))
                if aggregate.get("distinct"):
                    kwargs["distinct"] = True

                results[aggregate.get("name")] = local_queryset.aggregate(
                    **{aggregate.get("alias"): aggregate_fn(field, **kwargs)}
                )

    return results
