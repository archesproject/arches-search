from django.db.models import Count, Q, QuerySet

from arches_search.utils.advanced_search.constants import (
    AGGREGATE_KIND_COUNT,
    AGGREGATE_KIND_SET_EQUAL,
    AGGREGATE_KIND_SET_SUPERSET,
)
from arches_search.utils.advanced_search.specs import (
    AggregatePredicateSpec,
)


def build_grouped_rows_matching_aggregate_predicate(
    correlated_rows: QuerySet,
    aggregate_predicate_spec: AggregatePredicateSpec,
    grouping_field_name: str,
) -> QuerySet:
    grouped_rows = correlated_rows.values(grouping_field_name)

    if aggregate_predicate_spec.kind == AGGREGATE_KIND_SET_SUPERSET:
        requested_values_without_duplicates = tuple(
            dict.fromkeys(aggregate_predicate_spec.values)
        )
        field_name = aggregate_predicate_spec.field_name or "value"
        return grouped_rows.annotate(
            _matched_distinct_count=Count(
                field_name,
                filter=Q(
                    **{f"{field_name}__in": list(requested_values_without_duplicates)}
                ),
                distinct=True,
            )
        ).filter(_matched_distinct_count=len(requested_values_without_duplicates))

    if aggregate_predicate_spec.kind == AGGREGATE_KIND_SET_EQUAL:
        requested_values_without_duplicates = tuple(
            dict.fromkeys(aggregate_predicate_spec.values)
        )
        field_name = aggregate_predicate_spec.field_name or "value"
        return grouped_rows.annotate(
            _matched_distinct_count=Count(
                field_name,
                filter=Q(
                    **{f"{field_name}__in": list(requested_values_without_duplicates)}
                ),
                distinct=True,
            ),
            _total_distinct_count=Count(field_name, distinct=True),
        ).filter(
            _matched_distinct_count=len(requested_values_without_duplicates),
            _total_distinct_count=len(requested_values_without_duplicates),
        )

    if aggregate_predicate_spec.kind == AGGREGATE_KIND_COUNT:
        lookup_token = aggregate_predicate_spec.lookup or "exact"
        threshold = aggregate_predicate_spec.values[0]
        return grouped_rows.annotate(_row_count=Count("pk")).filter(
            **{f"_row_count__{lookup_token}": threshold}
        )

    raise ValueError(
        f"Unsupported aggregate predicate kind: {aggregate_predicate_spec.kind}"
    )
