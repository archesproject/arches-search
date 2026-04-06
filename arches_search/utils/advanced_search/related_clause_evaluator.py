from typing import Any, Dict, Optional

from django.db.models import Exists, OuterRef

from arches_search.utils.advanced_search.aggregate_predicate_runtime import (
    build_grouped_rows_matching_aggregate_predicate,
)
from arches_search.utils.advanced_search.constants import (
    QUANTIFIER_ALL,
    QUANTIFIER_ANY,
    QUANTIFIER_NONE,
)
from arches_search.utils.advanced_search.specs import AggregatePredicateSpec
from arches_search.utils.advanced_search.subject_utils import is_node_subject


class RelatedClauseEvaluator:
    def __init__(
        self, search_model_registry, facet_registry, path_navigator, predicate_builder
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.predicate_builder = predicate_builder

    def evaluate_at_anchor(
        self,
        clause_payload: Dict[str, Any],
        terminal_datatype_name: Optional[str] = None,
    ):
        return self._build_anchor_presence_exists(
            clause_payload, terminal_datatype_name
        )

    def evaluate_at_child(
        self,
        clause_payload: Dict[str, Any],
        traversal_context: Dict[str, Any],
    ):
        return self._build_child_presence_exists(clause_payload, traversal_context)

    def _build_anchor_presence_exists(
        self,
        clause_payload: Dict[str, Any],
        terminal_datatype_name: Optional[str],
    ):
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        subject = clause_payload["subject"]
        if not is_node_subject(subject):
            raise ValueError("RELATED clauses require a node subject.")

        traversal_context, child_row_set = self.path_navigator.build_relationship_pairs(
            {"path": subject, "is_inverse": False}
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
        subject = clause_payload["subject"]
        if not is_node_subject(subject):
            raise ValueError("RELATED clauses require a node subject.")
        subject_graph_slug = subject["graph_slug"]
        subject_node_alias = subject["node_alias"]
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
            any_value_exists = Exists(correlated_subject_row_sets[0])
            for current_row_set in correlated_subject_row_sets[1:]:
                any_value_exists = any_value_exists | Exists(current_row_set)
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
            aggregate_matches = build_grouped_rows_matching_aggregate_predicate(
                correlated_rows=correlated_subject_rows,
                aggregate_predicate_spec=predicate_expression,
                grouping_field_name="resourceinstanceid",
            )
            return (
                ~Exists(aggregate_matches)
                if is_template_negated
                else Exists(aggregate_matches)
            )

        return Exists(correlated_subject_rows.filter(predicate_expression))
