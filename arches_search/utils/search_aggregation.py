from django.db.models import aggregates, Q
from django.utils.translation import gettext as _


def _build_annotations(metric_specs):
    annotations = {}

    for metric_spec in metric_specs:
        metric_alias = metric_spec["alias"]
        aggregate_name = metric_spec["fn"]
        field_name = metric_spec.get("field")

        try:
            aggregate_fn = getattr(aggregates, aggregate_name)
        except AttributeError as error:
            raise ValueError(f"Unknown aggregate '{aggregate_name}'") from error

        kwargs = dict(metric_spec.get("kwargs") or {})

        if metric_spec.get("where"):
            kwargs["filter"] = Q(**metric_spec.get("where"))
        if metric_spec.get("distinct"):
            kwargs["distinct"] = True

        annotations[metric_alias] = aggregate_fn(field_name, **kwargs)

    return annotations


def apply_json_aggregations(raw_aggregations, queryset):
    if not raw_aggregations:
        raise ValueError(_("No aggregations provided"))

    results = {}

    for raw_aggregation in raw_aggregations:
        aggregation_name = raw_aggregation["name"]

        if raw_aggregation.get("where"):
            queryset = queryset.filter(**raw_aggregation.get("where"))

        if "aggregate" in raw_aggregation:
            annotations = _build_annotations(raw_aggregation["aggregate"])
            results[aggregation_name] = queryset.aggregate(**annotations)
            continue

        if "group_by" in raw_aggregation and "metrics" in raw_aggregation:
            annotations = _build_annotations(raw_aggregation["metrics"])
            group_by_fields = raw_aggregation["group_by"]
            grouped = queryset.values(*group_by_fields).annotate(**annotations)

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
