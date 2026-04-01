from typing import Any, Dict, Optional
from django.db.models import Exists, OuterRef, Q
from django.utils.translation import gettext as _
from arches_search.utils.advanced_search.literal_clause_evaluator import (
    _build_aggregate_match_rows,
    _combine_exists,
)
from arches_search.utils.advanced_search.predicate_builder import (
    AggregatePredicateSpec,
)

from arches_search.utils.advanced_search.constants import (
    QUANTIFIER_ALL,
    QUANTIFIER_ANY,
    QUANTIFIER_NONE,
)


class RelatedClauseEvaluator:
    def __init__(
        self, search_model_registry, facet_registry, path_navigator, predicate_builder
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.predicate_builder = predicate_builder

    def evaluate(
        self,
        mode: str,
        clause_payload: Dict[str, Any],
        traversal_context: Optional[Dict[str, Any]] = None,
        terminal_datatype_name: Optional[str] = None,
    ):
        if mode == "anchor":
            return self._build_anchor_presence_exists(
                clause_payload, terminal_datatype_name
            )
        if mode == "child":
            if traversal_context is None:
                raise ValueError(_("traversal_context is required for mode='child'"))
            return self._build_child_presence_exists(clause_payload, traversal_context)
        raise ValueError(_("Unsupported evaluation mode: {mode}").format(mode=mode))

    def _build_anchor_presence_exists(
        self,
        clause_payload: Dict[str, Any],
        terminal_datatype_name: Optional[str],
    ):
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        subject_path_sequence = clause_payload["subject"]

        traversal_context, child_row_set = self.path_navigator.build_relationship_pairs(
            {"path": subject_path_sequence, "is_inverse": False}
        )

        if terminal_datatype_name is None:
            terminal_datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    traversal_context["terminal_graph_slug"],
                    traversal_context["terminal_node_alias"],
                )
            )

        presence_implies_match = self.facet_registry.presence_implies_match(
            terminal_datatype_name, operator_token
        )

        if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
            return (
                Exists(child_row_set)
                if presence_implies_match
                else ~Exists(child_row_set)
            )

        if quantifier_token == QUANTIFIER_NONE:
            return (
                ~Exists(child_row_set)
                if presence_implies_match
                else Exists(child_row_set)
            )

        raise ValueError(f"Unsupported quantifier: {quantifier_token}")

    def _build_child_presence_exists(
        self, clause_payload: Dict[str, Any], traversal_context: Dict[str, Any]
    ):
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"]
        operand_items = clause_payload["operands"]

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        facet = self.facet_registry.get_facet(datatype_name, operator_token)
        if not operand_items:
            correlated_subject_row_sets = [
                model_class.objects.filter(
                    graph_slug=subject_graph_slug,
                    node_alias=subject_node_alias,
                    resourceinstanceid=OuterRef(traversal_context["child_id_field"]),
                ).annotate(
                    _anchor_resource_id=OuterRef(traversal_context["anchor_id_field"])
                )
                for model_class in self.search_model_registry.get_all_models_for_datatype(
                    datatype_name
                )
            ]
            any_value_exists = _combine_exists(correlated_subject_row_sets)
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name, operator_token
            )
            return any_value_exists if presence_implies_match else ~any_value_exists

        model_class = facet.target_model_class
        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug, node_alias=subject_node_alias
        )

        correlated_subject_rows = subject_rows.filter(
            resourceinstanceid=OuterRef(traversal_context["child_id_field"])
        ).annotate(_anchor_resource_id=OuterRef(traversal_context["anchor_id_field"]))

        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=operand_items,
                anchor_resource_id_annotation="_anchor_resource_id",
                facet=facet,
            )
        )

        if isinstance(predicate_expression, AggregatePredicateSpec):
            aggregate_matches = _build_aggregate_match_rows(
                correlated_rows=correlated_subject_rows,
                aggregate_spec=predicate_expression,
                group_field_name="resourceinstanceid",
            )
            return (
                ~Exists(aggregate_matches)
                if is_template_negated
                else Exists(aggregate_matches)
            )

        return Exists(correlated_subject_rows.filter(predicate_expression))
