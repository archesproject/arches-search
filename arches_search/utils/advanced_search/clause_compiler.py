from typing import Any, Dict, Optional, Union

from django.db.models import Exists, OuterRef, Q, QuerySet, Subquery
from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.advanced_search.facet_registry import FacetRegistry
from arches_search.utils.advanced_search.path_navigator import PathNavigator

from django.utils.translation import gettext as _


class ClauseCompiler:
    def __init__(
        self,
        search_model_registry: SearchModelRegistry,
        facet_registry: FacetRegistry,
        path_navigator: PathNavigator,
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator

    def compile(
        self,
        clause_payload: Dict[str, Any],
        anchor_graph_slug: str,
        parent_graph_slug: Optional[str],
        unioned_subgroup_ids_queryset: Optional[QuerySet],
    ) -> Exists:
        if not clause_payload["subject"]:
            return Exists(arches_models.ResourceInstance.objects.none())

        subject_datatype_name, _subject_model, subject_queryset = (
            self.path_navigator.build_path_queryset(
                path_segments=clause_payload["subject"],
                context_graph_slug=anchor_graph_slug,
            )
        )

        facet = self.facet_registry.get_facet(
            subject_datatype_name=subject_datatype_name,
            operator_token=clause_payload["operator"],
        )

        if facet.arity == 0:
            return self._apply_exists(
                subject_queryset.order_by()[:1], facet.is_orm_template_negated
            )

        operand = clause_payload["operands"][0]

        right_hand_side_value = self._compile_right_hand_side_expression(
            operand_type=operand["type"],
            operand_value=operand["value"],
            anchor_graph_slug=anchor_graph_slug,
            parent_graph_slug=parent_graph_slug,
            unioned_subgroup_ids_queryset=unioned_subgroup_ids_queryset,
        )

        condition_expression = self._build_condition_from_facet(
            facet=facet,
            field_name="value",
            right_hand_side_value=right_hand_side_value,
        )

        filtered_subject = subject_queryset.filter(condition_expression).order_by()[:1]
        return self._apply_exists(filtered_subject, facet.is_orm_template_negated)

    def _build_condition_from_facet(
        self, facet: Any, field_name: str, right_hand_side_value: Any
    ) -> Q:
        is_collection = isinstance(
            right_hand_side_value, (list, tuple, Subquery)
        ) and not isinstance(right_hand_side_value, OuterRef)
        base_key = f"{field_name}__in" if is_collection else field_name

        if facet.orm_template is None:
            return Q(**{base_key: right_hand_side_value})

        if (
            facet.orm_template.startswith(("AGG_", "HAVING_"))
            or ":" in facet.orm_template
        ):
            return Q(**{base_key: right_hand_side_value})

        if "{col}" in facet.orm_template:
            lookup_key = facet.orm_template.replace("{col}", field_name)

            if is_collection and (
                lookup_key == field_name or lookup_key.endswith("__exact")
            ):
                lookup_key = f"{field_name}__in"

            return Q(**{lookup_key: right_hand_side_value})

        return Q(**{base_key: right_hand_side_value})

    def _compile_right_hand_side_expression(
        self,
        operand_type: str,
        operand_value: Any,
        anchor_graph_slug: str,
        parent_graph_slug: Optional[str],
        unioned_subgroup_ids_queryset: Optional[QuerySet] = None,
    ) -> Union[Any, Subquery, OuterRef]:
        if operand_type == "LITERAL":
            return operand_value

        if operand_type == "RESULTSET":
            if unioned_subgroup_ids_queryset is None:
                raise ValueError(
                    _(
                        "RESULTSET operand used but current group has no direct subgroups."
                    )
                )

            path_segments = operand_value or []
            if not path_segments:
                return Subquery(unioned_subgroup_ids_queryset)

            last_graph_slug, last_node_alias = path_segments[-1]
            last_datatype_name = (
                self.path_navigator.node_alias_datatype_registry.lookup_node_datatype(
                    last_graph_slug,
                    last_node_alias,
                )
            )
            last_model = self.search_model_registry.get_model_for_datatype(
                last_datatype_name
            )

            node_values = (
                last_model.objects.only(
                    "graph_slug", "node_alias", "resourceinstanceid", "value"
                )
                .filter(
                    graph_slug=last_graph_slug,
                    node_alias=last_node_alias,
                    resourceinstanceid__in=unioned_subgroup_ids_queryset,
                )
                .values_list("value", flat=True)
            )

            return Subquery(node_values)

        if operand_type == "SELF":
            path_segments = operand_value or []

            if not path_segments:
                return OuterRef("anchor_resourceinstanceid")

            return self.path_navigator.build_values_subquery(
                outer_resource_instance_id_reference="anchor_resourceinstanceid",
                starting_graph_slug=anchor_graph_slug,
                path_segments=path_segments,
            )

        if operand_type == "PARENT":
            path_segments = operand_value or []
            starting_graph = parent_graph_slug or anchor_graph_slug

            if not path_segments:
                return OuterRef("parent_resourceinstanceid")

            return self.path_navigator.build_values_subquery(
                outer_resource_instance_id_reference="parent_resourceinstanceid",
                starting_graph_slug=starting_graph,
                path_segments=path_segments,
            )

        raise ValueError("Unsupported operand form")

    def _apply_exists(
        self, candidate: Union[QuerySet, Exists], is_negated: bool
    ) -> Exists:
        exists_expression = (
            candidate if isinstance(candidate, Exists) else Exists(candidate)
        )

        if is_negated:
            return ~exists_expression

        return exists_expression
