from typing import Any, Dict, List, Sequence
from django.db.models import Exists, OuterRef, Q, QuerySet
from arches_search.models.models import (
    AdvancedSearchFacet,
    DDatatypeXAdvancedSearchModel,
)

from arches.app.models import models as arches_models


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
    datatype: str,
    operator: str,
    params: Sequence[Any],
    model_by_datatype: Dict[str, Any],
):
    facet = AdvancedSearchFacet.objects.get(datatype=datatype, operator=operator)
    condition_q = build_condition_q(facet, "value", params)

    if facet.is_orm_template_negated:
        condition_q = ~condition_q

    model_class = model_by_datatype[datatype]
    subquery = model_class.objects.filter(
        graph_slug=graph_slug,
        node_alias=node_alias,
        resourceinstanceid=OuterRef("resourceinstanceid"),
    ).filter(condition_q)

    return Exists(subquery)


def build_exists_expression_for_group(
    graph_slug: str,
    group: Dict[str, Any],
    model_by_datatype: Dict[str, Any],
):
    logic = (group.get("logic") or "AND").upper()
    expressions: List[Any] = []

    for clause in group.get("clauses", []):
        exists_expr = build_exists_for_clause(
            graph_slug=graph_slug,
            node_alias=clause["node_alias"],
            datatype=clause["datatype"],
            operator=clause["operator"],
            params=clause.get("params", []),
            model_by_datatype=model_by_datatype,
        )
        expressions.append(exists_expr)

    for subgroup in group.get("groups", []):
        subgroup_expr = build_exists_expression_for_group(
            graph_slug,
            subgroup,
            model_by_datatype=model_by_datatype,
        )
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

    resource_instances = arches_models.ResourceInstance.objects.filter(
        graph__slug=graph_slug
    )

    model_by_datatype = {}

    for mapping in DDatatypeXAdvancedSearchModel.objects.select_related(
        "content_type"
    ).all():
        if mapping.model_class:
            model_by_datatype[mapping.datatype.datatype] = mapping.model_class

    if not query.get("clauses") and not query.get("groups"):
        return resource_instances

    predicate = build_exists_expression_for_group(
        graph_slug,
        query,
        model_by_datatype=model_by_datatype,
    )

    if predicate is None:
        return resource_instances

    return resource_instances.filter(predicate)
