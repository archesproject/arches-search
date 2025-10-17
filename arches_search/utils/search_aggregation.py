from django.db.models import aggregates, Q, OuterRef, Subquery
from django.utils.translation import gettext as _

from arches_search.utils.advanced_search import SEARCH_TABLE_TO_MODEL
from django.db.models import OuterRef, Subquery, F, Q, Value
from django.db.models import Sum, Avg, Count, Min, Max
from django.db import models


# --- Utilities ---


def get_search_model(search_table: str):
    try:
        return SEARCH_TABLE_TO_MODEL[search_table]
    except KeyError:
        raise ValueError(f"Unknown search table '{search_table}'")


def build_subquery_for_groupby(group_spec, parent_ref_field="resourceinstanceid"):
    """
    Build a correlated Subquery that pulls a field from a search table.
    Example:
        Subquery(
            TermSearch.objects.filter(
                node_alias='account_type',
                resourceinstanceid=OuterRef(parent_ref_field),
            ).values('value')[:1]
        )
    """
    model = get_search_model(group_spec["search_table"])
    node_alias = group_spec["node_alias"]
    field = group_spec.get("field", "value")

    subquery = model.objects.filter(
        node_alias=node_alias,
        resourceinstanceid=OuterRef(parent_ref_field),
    ).values("value")[:1]

    return subquery


# --- Recursive Subquery Builder ---


def build_nested_subquery(group_spec, parent_ref_field="resourceinstanceid"):
    """
    Recursively build nested subqueries for deeply linked nodes.
    """

    # Base subquery for this level
    base_subquery = build_subquery_for_groupby(
        group_spec, parent_ref_field=parent_ref_field
    )

    # Handle nested aggregations if present
    if "aggregations" in group_spec and group_spec["aggregations"]:
        # Each nested aggregation will become another subquery wrapped inside this one
        for agg in group_spec["aggregations"]:
            for nested_group in agg.get("group_by", []):
                nested_subquery = build_nested_subquery(
                    nested_group,
                    parent_ref_field="value",  # Each nested subquery joins on the previous value
                )

                # Rebuild the current subquery, wrapping the nested one
                model = get_search_model(group_spec["search_table"])
                base_subquery = Subquery(
                    model.objects.filter(
                        node_alias=group_spec["node_alias"],
                        resourceinstanceid=OuterRef(parent_ref_field),
                    )
                    .annotate(**{nested_group["field"]: nested_subquery})
                    .values(nested_group["field"])[:1]
                )

    return base_subquery


# --- Aggregation Builder ---


def _build_annotations(metric_specs):
    annotations = {}
    for metric_spec in metric_specs:
        alias = metric_spec["alias"]
        fn_name = metric_spec["fn"]
        model = get_search_model(metric_spec["search_table"])
        node_alias = metric_spec["node_alias"]
        field = metric_spec.get("field", "value")

        try:
            aggregate_fn = getattr(models, fn_name)
        except AttributeError as e:
            raise ValueError(f"Unknown aggregate function: {fn_name}") from e

        subquery = Subquery(
            model.objects.filter(
                node_alias=node_alias,
                resourceinstanceid=OuterRef("resourceinstanceid"),
            ).values("value")[:1]
        )

        annotations[field] = aggregate_fn(subquery)
    return annotations


def build_joined_queryset_for_aggregations(queryset, aggregations):
    """
    Takes a base ResourceInstance queryset and a list of aggregation definitions
    and returns a queryset annotated with nested subqueries for group_by and metrics.
    """
    # queryset = base_queryset
    for agg in aggregations:
        group_bys = agg.get("group_by", [])
        metrics = agg.get("metrics", [])
        # field = agg.get("field", "value")
        # print(f"field: {field}")

        # Handle group_by subqueries
        for group_spec in group_bys:
            subquery = build_nested_subquery(group_spec)
            alias = group_spec.get("alias") or f"{group_spec['node_alias']}__value"
            field = group_spec.get("field")
            queryset = queryset.annotate(**{field: subquery})

        # Handle metric annotations
        metric_annotations = _build_annotations(metrics)
        if metric_annotations:
            queryset = queryset.annotate(**metric_annotations)

    print(queryset.query)
    return queryset


def apply_json_aggregations(raw_aggregations, queryset):
    if not raw_aggregations:
        raise ValueError(_("No aggregations provided"))

    results = {}

    for raw_aggregation in raw_aggregations:
        aggregation_name = raw_aggregation["name"]

        if raw_aggregation.get("where"):
            local_queryset = queryset.filter(**raw_aggregation.get("where"))
        else:
            local_queryset = queryset.all()

        if "aggregate" in raw_aggregation:
            annotations = _build_annotations(raw_aggregation["aggregate"])
            results[aggregation_name] = local_queryset.aggregate(**annotations)
            continue

        if "group_by" in raw_aggregation and "metrics" in raw_aggregation:
            annotations = _build_annotations(raw_aggregation["metrics"])
            group_by_fields = [item["field"] for item in raw_aggregation["group_by"]]
            grouped = local_queryset.values(*group_by_fields).annotate(**annotations)

            order_by_fields = raw_aggregation.get("order_by")
            if order_by_fields:
                grouped = grouped.order_by(*order_by_fields)
            else:
                metric_aliases_in_order = list(annotations.keys())
                default_order = (
                    [f"-{metric_aliases_in_order[0]}"]
                    if metric_aliases_in_order
                    else []
                ) + group_by_fields
                grouped = grouped.order_by(*default_order)

            limit_value = raw_aggregation.get("limit")
            if isinstance(limit_value, int) and limit_value > 0:
                grouped = grouped[:limit_value]

            results[aggregation_name] = list(grouped)
            continue

        raise ValueError(
            "Each raw_aggregation must be either 'aggregate' or ('group_by' + 'metrics')."
        )

    return results
