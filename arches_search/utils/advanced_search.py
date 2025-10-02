from typing import Any, Dict, List, Sequence, Set
from django.db.models import Q, QuerySet

from arches_search.models.models import (
    AdvancedSearchFacet,
    TermSearch,
    NumericSearch,
    UUIDSearch,
    DateSearch,
    DateRangeSearch,
    BooleanSearch,
)

SEARCH_TABLE_TO_MODEL = {
    "term": TermSearch,
    "numeric": NumericSearch,
    "uuid": UUIDSearch,
    "date": DateSearch,
    "date_range": DateRangeSearch,
    "boolean": BooleanSearch,
}


def get_facet(datatype_code: str, operator_code: str) -> AdvancedSearchFacet:
    return AdvancedSearchFacet.objects.get(
        datatype=datatype_code, operator=operator_code
    )


def coerce_params(raw_params: Sequence[Any]) -> List[Any]:
    coerced_values: List[Any] = []
    for raw in raw_params:
        try:
            coerced_values.append(float(raw))
        except (TypeError, ValueError):
            coerced_values.append(raw)
    return coerced_values


def build_clause_queryset(
    graph_alias: str,
    node_alias: str,
    search_table: str,
    datatype: str,
    operator: str,
    params: Sequence[Any],
) -> QuerySet:
    facet = get_facet(datatype, operator)
    model_class = SEARCH_TABLE_TO_MODEL[search_table]
    base_queryset = model_class.objects.filter(
        graph_alias=graph_alias, node_alias=node_alias
    )

    value_field_name = "value"
    lookup = facet.orm_template.replace("{col}", value_field_name)

    if facet.arity == 0:
        q_object = Q(**{lookup: True})
    elif facet.arity == 1:
        coerced = coerce_params(params)
        q_object = Q(**{lookup: coerced[0]})

    if facet.is_orm_template_negated:
        q_object = ~q_object

    return base_queryset.filter(q_object)


def collect_resource_ids_for_group(graph_alias: str, group: Dict[str, Any]) -> Set[str]:
    logic = (group.get("logic") or "AND").upper()
    buckets: List[Set[str]] = []

    for clause in group.get("clauses", []):
        qs = build_clause_queryset(
            graph_alias=graph_alias,
            node_alias=clause["node_alias"],
            search_table=clause["search_table"],
            datatype=clause["datatype"],
            operator=clause["operator"],
            params=clause.get("params", []),
        )
        buckets.append(set(qs.values_list("resourceinstanceid", flat=True)))

    for subgroup in group.get("groups", []):
        buckets.append(collect_resource_ids_for_group(graph_alias, subgroup))

    if not buckets:
        return set()

    if logic == "AND":
        result_ids = buckets[0]
        for next_ids in buckets[1:]:
            result_ids = result_ids.intersection(next_ids)
        return result_ids

    result_ids: Set[str] = set()
    for next_ids in buckets:
        result_ids |= next_ids
    return result_ids


def search_resource_ids_from_payload(payload: Dict[str, Any]) -> Set[str]:
    graph_alias = payload["graph_alias"]
    root_group = (
        payload.get("query")
        or payload.get("where")
        or {"logic": "AND", "clauses": [], "groups": []}
    )
    return collect_resource_ids_for_group(graph_alias, root_group)
