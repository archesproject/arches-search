from django.db.models import Exists, Q, QuerySet

from arches_search.utils.advanced_search.constants import (
    AGGREGATE_KIND_SET_EQUAL,
    AGGREGATE_KIND_SET_SUPERSET,
)
from arches_search.utils.advanced_search.specs import (
    AggregatePredicateSpec,
)


def build_aggregate_predicate_q(
    correlated_rows: QuerySet,
    aggregate_predicate_spec: AggregatePredicateSpec,
) -> Q:
    if aggregate_predicate_spec.kind not in (
        AGGREGATE_KIND_SET_SUPERSET,
        AGGREGATE_KIND_SET_EQUAL,
    ):
        raise ValueError(
            f"Unsupported aggregate predicate kind: {aggregate_predicate_spec.kind}"
        )

    requested_values = tuple(dict.fromkeys(aggregate_predicate_spec.values))
    field_name = aggregate_predicate_spec.field_name or "value"

    if not requested_values:
        if aggregate_predicate_spec.kind == AGGREGATE_KIND_SET_SUPERSET:
            return Q(Exists(correlated_rows))
        return Q(Exists(correlated_rows.none()))

    predicate = Q()
    allowed_values = []
    for requested_value in requested_values:
        if isinstance(requested_value, tuple):
            lookup = {f"{field_name}__in": requested_value}
            allowed_values.extend(requested_value)
        else:
            lookup = {field_name: requested_value}
            allowed_values.append(requested_value)
        predicate &= Q(Exists(correlated_rows.filter(**lookup)))

    if aggregate_predicate_spec.kind == AGGREGATE_KIND_SET_EQUAL:
        predicate &= ~Q(
            Exists(correlated_rows.exclude(**{f"{field_name}__in": allowed_values}))
        )

    return predicate
