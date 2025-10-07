from typing import Any, Dict, List, Optional, Sequence, Tuple
from django.db.models import Exists, OuterRef, Q, QuerySet
from arches_search.models.models import (
    AdvancedSearchFacet,
    TermSearch,
    NumericSearch,
    UUIDSearch,
    DateSearch,
    DateRangeSearch,
    BooleanSearch,
)

from arches.app.models import models as arches_models


SEARCH_TABLE_TO_MODEL = {
    "term": TermSearch,
    "numeric": NumericSearch,
    "uuid": UUIDSearch,
    "date": DateSearch,
    "date_range": DateRangeSearch,
    "boolean": BooleanSearch,
}


def build_condition_q(
    facet: AdvancedSearchFacet, value_field_name: str, params: Sequence[Any]
) -> Q:
    lookup = facet.orm_template.replace("{col}", value_field_name)

    if facet.arity == 0:
        return Q(**{lookup: True})

    if facet.arity == 1:
        return Q(**{lookup: params[0]})

    return Q(**{lookup: params[0]})


def build_exists_for_clause(
    graph_slug: str,
    node_alias: str,
    search_table: str,
    datatype: str,
    operator: str,
    params: Sequence[Any],
):
    facet = AdvancedSearchFacet.objects.get(datatype=datatype, operator=operator)
    model_class = SEARCH_TABLE_TO_MODEL[search_table]

    value_field_name = "value"
    condition_q = build_condition_q(facet, value_field_name, params)

    if facet.is_orm_template_negated:
        condition_q = ~condition_q

    subquery = model_class.objects.filter(
        graph_slug=graph_slug,
        node_alias=node_alias,
        resourceinstanceid=OuterRef("resourceinstanceid"),
    ).filter(condition_q)
    return Exists(subquery)


def build_exists_expression_for_group(graph_slug: str, group: Dict[str, Any]):
    logic = (group.get("logic") or "AND").upper()
    expressions: List[Any] = []

    for clause in group.get("clauses", []):
        exists_expr = build_exists_for_clause(
            graph_slug=graph_slug,
            node_alias=clause["node_alias"],
            search_table=clause["search_table"],
            datatype=clause["datatype"],
            operator=clause["operator"],
            params=clause.get("params", []),
        )
        expressions.append(exists_expr)

    for subgroup in group.get("groups", []):
        subgroup_expr = build_exists_expression_for_group(graph_slug, subgroup)
        if subgroup_expr is not None:
            expressions.append(subgroup_expr)

    if not expressions:
        return None

    combined = expressions[0]
    for next_expr in expressions[1:]:
        combined = (combined & next_expr) if logic == "AND" else (combined | next_expr)
    return combined


def resources_queryset_from_payload(payload: Dict[str, Any]) -> QuerySet:
    graph_slug = payload["graph_slug"]
    query = payload.get("query")

    aliased_graph_queryset = arches_models.ResourceInstance.objects.filter(
        graph__slug=graph_slug
    )

    # If there are no clauses or groups, return all resources for the graph
    if not query.get("clauses") and not query.get("groups"):
        return aliased_graph_queryset

    predicate = build_exists_expression_for_group(graph_slug, query)

    if predicate is None:
        return aliased_graph_queryset

    return aliased_graph_queryset.filter(predicate)
