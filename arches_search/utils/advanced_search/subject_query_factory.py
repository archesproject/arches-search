from __future__ import annotations
from typing import Any, List, Tuple, Union

from django.db.models import OuterRef, Q, QuerySet


class SubjectQueryFactory:
    def __init__(
        self, search_model_registry, node_alias_datatype_registry, facet_registry
    ) -> None:
        self.search_model_registry = search_model_registry
        self.node_alias_datatype_registry = node_alias_datatype_registry
        self.facet_registry = facet_registry

    def subject_rows(
        self, datatype_name: str, graph_slug: str, node_alias: str
    ) -> QuerySet:
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)
        return model_class.objects.filter(graph_slug=graph_slug, node_alias=node_alias)

    def correlate_to_anchor(self, subject_rows: QuerySet) -> QuerySet:
        return subject_rows.filter(resourceinstanceid=OuterRef("resourceinstanceid"))

    def correlate(self, subject_rows: QuerySet, outerref_field_name: str) -> QuerySet:
        return subject_rows.filter(resourceinstanceid=OuterRef(outerref_field_name))

    def positive_expression(
        self,
        datatype_name: str,
        operator_token: str,
        literal_values: List[Any],
    ) -> Tuple[Union[Q, dict], bool]:
        positive_facet = self.facet_registry.get_positive_facet_for(
            operator_token, datatype_name
        )
        if positive_facet is None:
            return Q(pk__in=[]), False
        positive_expression, _ = self.facet_registry.predicate(
            datatype_name,
            positive_facet.operator,
            "value",
            literal_values,
        )
        return positive_expression, True
