from django.db import models
from django.db.models import OuterRef, Subquery
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
) -> Subquery:
    """
    Builds a base Subquery that returns a single 'value' field from the given search table.
    Shared by both group_by and metric builders.
    """
    model = get_search_model(search_table)
    filters = {
        "node_alias": node_alias,
        "resourceinstanceid": OuterRef(parent_ref_field),
    }
    qs = model.objects.filter(**filters)
    if where:
        qs = qs.filter(**where)
    return Subquery(qs.values("value")[:1])


def build_nested_subquery(group_spec, parent_ref_field="resourceinstanceid"):
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
            nested_subquery = build_nested_subquery(
                nested_group, parent_ref_field="value"
            )
            nested_field = nested_group["field"]

            # Annotate the current subquery with the nested subquery
            model = get_search_model(group_spec["search_table"])
            qs = (
                model.objects.filter(
                    node_alias=group_spec["node_alias"],
                    resourceinstanceid=OuterRef(parent_ref_field),
                )
                .annotate(**{nested_field: nested_subquery})
                .values(nested_field)[:1]
            )

            if group_spec.get("where"):
                qs = qs.filter(**group_spec["where"])

            subquery = Subquery(qs)

    return subquery


def _build_annotations(metric_specs):
    annotations = {}

    for spec in metric_specs:
        alias = spec["alias"]
        aggregate_fn = get_aggregate_function(spec["fn"])
        field = spec.get("field", "value")

        # Use our unified helper
        subquery = build_value_subquery(
            search_table=spec["search_table"],
            node_alias=spec["node_alias"],
            parent_ref_field="resourceinstanceid",
        )
        annotations[alias] = aggregate_fn(subquery)

    return annotations


def build_aggregations(queryset, aggregations):
    results = {}

    for agg in aggregations:
        name = agg["name"]

        if "aggregate" in agg:
            # annotations = _build_annotations(agg["aggregate"])
            annotations = {}
            for aggregate in agg["aggregate"]:
                field = aggregate.get("field", "value")
                aggregate_fn = get_aggregate_function(aggregate["fn"])
                kwargs = dict(aggregate.get("kwargs") or {})

                if aggregate.get("where"):
                    kwargs["filter"] = Q(**aggregate.get("where"))
                if aggregate.get("distinct"):
                    kwargs["distinct"] = True
                annotations[aggregate["alias"]] = aggregate_fn(field, **kwargs)
            results[name] = queryset.aggregate(**annotations)
            continue

        group_bys = agg.get("group_by", [])
        metrics = agg.get("metrics", [])

        for group_spec in group_bys:
            field_alias = group_spec["field"]
            queryset = queryset.annotate(
                **{field_alias: build_nested_subquery(group_spec)}
            )

        metric_annotations = _build_annotations(metrics)
        if metric_annotations:
            group_fields = [g["field"] for g in group_bys]
            queryset = queryset.values(*group_fields).annotate(**metric_annotations)

        results[name] = list(queryset)

    return results
