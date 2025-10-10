from django.db.models import aggregates, Q, OuterRef, Subquery
from django.utils.translation import gettext as _

from arches_search.utils.advanced_search import SEARCH_TABLE_TO_MODEL


def get_search_model(search_table: str):
    model = SEARCH_TABLE_TO_MODEL.get(search_table)
    if not model:
        raise ValueError(f"Unknown search table '{search_table}'")
    return model


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
            inner_queryset = queryset.filter(**raw_aggregation.get("where"))
        else:
            inner_queryset = queryset

        if "aggregate" in raw_aggregation:
            annotations = _build_annotations(raw_aggregation["aggregate"])
            results[aggregation_name] = inner_queryset.aggregate(**annotations)
            continue

        if "group_by" in raw_aggregation and "metrics" in raw_aggregation:
            annotations = _build_annotations(raw_aggregation["metrics"])
            group_by_fields = raw_aggregation["group_by"][0]["field"]
            grouped = inner_queryset.values(group_by_fields).annotate(**annotations)

            order_by_fields = raw_aggregation.get("order_by")
            if order_by_fields:
                grouped = grouped.order_by(*order_by_fields)
            else:
                metric_aliases_in_order = list(annotations.keys())
                default_order = (
                    [f"-{metric_aliases_in_order[0]}"]
                    if metric_aliases_in_order
                    else []
                ) + [group_by_fields]
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


def build_joined_queryset_for_aggregations(base_queryset, raw_aggregations):
    """
    Annotates the ResourceInstance queryset with values from arches_search_* tables
    based on the aggregation payload structure.
    """
    queryset = base_queryset

    for agg in raw_aggregations:
        joins = []

        # extract group_by and metrics
        for group in agg.get("group_by", []):
            joins.append((group["search_table"], group["node_alias"]))

        for metric in agg.get("metrics", []):
            joins.append((metric["search_table"], metric["node_alias"]))

        # deduplicate (by tuple)
        joins = list(set(joins))

        for search_table, node_alias in joins:
            model_class = get_search_model(search_table)
            alias_prefix = f"{search_table}_{node_alias}"

            subquery = (
                model_class.objects.filter(
                    resourceinstanceid=OuterRef("resourceinstanceid"),
                    node_alias=node_alias,
                )
                .order_by()
                .values("value")[:1]
            )

            queryset = queryset.annotate(
                **{f"{alias_prefix}__value": Subquery(subquery)}
            )

    return queryset
