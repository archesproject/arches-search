from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.db.models import Exists, OuterRef, Q, QuerySet

from arches_search.utils.advanced_search.aggregate_predicate_runtime import (
    build_grouped_rows_matching_aggregate_predicate,
)
from arches_search.utils.advanced_search.child_rows_computer import ChildRowsComputer
from arches_search.utils.advanced_search.constants import (
    QUANTIFIER_ALL,
    QUANTIFIER_ANY,
    QUANTIFIER_NONE,
)
from arches_search.utils.advanced_search.search_model_clause_evaluator import (
    SearchModelClauseEvaluator,
)
from arches_search.utils.advanced_search.specs import (
    AggregatePredicateSpec,
    CorrelatedLiteralClauseContext,
)
from arches_search.utils.advanced_search.constants import SUBJECT_TYPE_SEARCH_MODELS


class LiteralClauseEvaluator:
    def __init__(
        self,
        search_model_registry,
        facet_registry,
        path_navigator,
        predicate_builder,
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.predicate_builder = predicate_builder
        self._search_model_clause_evaluator = SearchModelClauseEvaluator(
            search_model_registry=search_model_registry,
            facet_registry=facet_registry,
            predicate_builder=predicate_builder,
            literal_clause_evaluator=self,
        )
        self._child_rows_computer = ChildRowsComputer(literal_clause_evaluator=self)

    def build_subject_rows(
        self,
        model_class,
        subject_graph_slug: str,
        subject_node_alias: str,
    ) -> QuerySet:
        return model_class.objects.filter(
            graph_slug=subject_graph_slug,
            node_alias=subject_node_alias,
        )

    def build_presence_subject_row_sets(
        self,
        datatype_name: str,
        subject_graph_slug: str,
        subject_node_alias: str,
    ) -> List[QuerySet]:
        return [
            self.build_subject_rows(
                model_class=model_class,
                subject_graph_slug=subject_graph_slug,
                subject_node_alias=subject_node_alias,
            )
            for model_class in self.search_model_registry.get_all_models_for_datatype(
                datatype_name
            )
        ]

    def resolve_facet_and_model(
        self,
        subject_graph_slug: str,
        subject_node_alias: str,
        operator_token: str,
    ):
        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug,
                subject_node_alias,
            )
        )
        facet = self.facet_registry.get_facet(datatype_name, operator_token)
        model_class = facet.target_model_class
        return datatype_name, facet, model_class

    def _build_any_value_exists_for_subject(
        self,
        datatype_name: str,
        subject_graph_slug: str,
        subject_node_alias: str,
        correlate_field_name: str,
    ):
        correlated_row_sets = [
            subject_rows.filter(resourceinstanceid=OuterRef(correlate_field_name))
            for subject_rows in self.build_presence_subject_row_sets(
                datatype_name=datatype_name,
                subject_graph_slug=subject_graph_slug,
                subject_node_alias=subject_node_alias,
            )
        ]

        any_value_exists = Exists(correlated_row_sets[0])
        for current_row_set in correlated_row_sets[1:]:
            any_value_exists = any_value_exists | Exists(current_row_set)

        return any_value_exists

    def _build_correlated_literal_clause_predicate(
        self,
        clause_payload: Dict[str, Any],
        correlate_field_name: str,
    ) -> CorrelatedLiteralClauseContext:
        subject = clause_payload["subject"]
        subject_graph_slug = subject["graph_slug"]
        subject_node_alias = subject["node_alias"]
        operator_token = clause_payload["operator"]
        operand_items = clause_payload["operands"]

        datatype_name, facet, model_class = self.resolve_facet_and_model(
            subject_graph_slug=subject_graph_slug,
            subject_node_alias=subject_node_alias,
            operator_token=operator_token,
        )

        subject_rows = self.build_subject_rows(
            model_class=model_class,
            subject_graph_slug=subject_graph_slug,
            subject_node_alias=subject_node_alias,
        )
        normalized_operand_items, filter_value = (
            model_class.normalize_operands(operand_items)
            if hasattr(model_class, "normalize_operands")
            else (list(operand_items), None)
        )
        correlated_rows = facet.filter_rows(
            subject_rows.filter(resourceinstanceid=OuterRef(correlate_field_name)),
            filter_value,
        )
        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=normalized_operand_items,
                anchor_resource_id_annotation=None,
                facet=facet,
            )
        )

        return CorrelatedLiteralClauseContext(
            datatype_name=datatype_name,
            correlated_rows=correlated_rows,
            normalized_operand_items=normalized_operand_items,
            predicate_expression=predicate_expression,
            is_template_negated=is_template_negated,
            facet_arity=facet.arity,
        )

    def build_anchor_exists(self, clause_payload: Dict[str, Any]) -> Exists:
        if clause_payload["subject"].get("type") == SUBJECT_TYPE_SEARCH_MODELS:
            return self._search_model_clause_evaluator.build_exists(
                clause_payload, correlate_field_name="resourceinstanceid"
            )
        subject = clause_payload["subject"]
        subject_graph_slug = subject["graph_slug"]
        subject_node_alias = subject["node_alias"]
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        operand_items = clause_payload["operands"]

        if not operand_items:
            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug,
                    subject_node_alias,
                )
            )
            any_value_exists = self._build_any_value_exists_for_subject(
                datatype_name=datatype_name,
                subject_graph_slug=subject_graph_slug,
                subject_node_alias=subject_node_alias,
                correlate_field_name="resourceinstanceid",
            )
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name,
                operator_token,
            )
            if quantifier_token == QUANTIFIER_NONE:
                return ~any_value_exists if presence_implies_match else any_value_exists
            return any_value_exists if presence_implies_match else ~any_value_exists

        correlated_clause_predicate = self._build_correlated_literal_clause_predicate(
            clause_payload=clause_payload,
            correlate_field_name="resourceinstanceid",
        )
        datatype_name = correlated_clause_predicate.datatype_name
        correlated_rows = correlated_clause_predicate.correlated_rows
        normalized_operand_items = correlated_clause_predicate.normalized_operand_items
        predicate_expression = correlated_clause_predicate.predicate_expression
        is_template_negated = correlated_clause_predicate.is_template_negated

        if isinstance(predicate_expression, AggregatePredicateSpec):
            aggregate_matches = build_grouped_rows_matching_aggregate_predicate(
                correlated_rows=correlated_rows,
                aggregate_predicate_spec=predicate_expression,
                grouping_field_name="resourceinstanceid",
            )

            if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
                return (
                    ~Exists(aggregate_matches)
                    if is_template_negated
                    else Exists(aggregate_matches)
                )

            if quantifier_token == QUANTIFIER_NONE:
                return (
                    Exists(aggregate_matches)
                    if is_template_negated
                    else ~Exists(aggregate_matches)
                )

            raise ValueError(f"Unsupported quantifier: {quantifier_token}")

        if quantifier_token == QUANTIFIER_ANY:
            if not is_template_negated:
                return Exists(correlated_rows.filter(predicate_expression))

            matching_negated_rows = correlated_rows.filter(predicate_expression)
            if correlated_clause_predicate.facet_arity > 0:
                return Exists(matching_negated_rows) | ~Exists(correlated_rows)
            return Exists(matching_negated_rows)

        if quantifier_token == QUANTIFIER_NONE:
            if not is_template_negated:
                return ~Exists(correlated_rows.filter(predicate_expression))

            return ~Exists(correlated_rows.filter(predicate_expression))

        if quantifier_token == QUANTIFIER_ALL:
            if not is_template_negated:
                violating_rows = correlated_rows.exclude(predicate_expression)
                return Exists(correlated_rows) & ~Exists(violating_rows)

            positive_per_row = self.positive_rows_for_negated_template(
                operator_token=operator_token,
                datatype_name=datatype_name,
                operand_items=normalized_operand_items,
                correlated_rows=correlated_rows,
                predicate_expression=predicate_expression,
            )
            return Exists(correlated_rows) & ~Exists(positive_per_row)

        raise ValueError(f"Unsupported quantifier: {quantifier_token}")

    def build_child_exists(
        self,
        clause_payload: Dict[str, Any],
        correlate_field: str,
    ) -> Exists:
        if clause_payload["subject"].get("type") == SUBJECT_TYPE_SEARCH_MODELS:
            return self._search_model_clause_evaluator.build_exists(
                clause_payload, correlate_field_name=correlate_field
            )
        subject = clause_payload["subject"]
        subject_graph_slug = subject["graph_slug"]
        subject_node_alias = subject["node_alias"]
        operator_token = clause_payload["operator"]
        operand_items = clause_payload["operands"]

        if not operand_items:
            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug,
                    subject_node_alias,
                )
            )
            any_value_exists = self._build_any_value_exists_for_subject(
                datatype_name=datatype_name,
                subject_graph_slug=subject_graph_slug,
                subject_node_alias=subject_node_alias,
                correlate_field_name=correlate_field,
            )
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name,
                operator_token,
            )
            return any_value_exists if presence_implies_match else ~any_value_exists

        correlated_clause_predicate = self._build_correlated_literal_clause_predicate(
            clause_payload=clause_payload,
            correlate_field_name=correlate_field,
        )
        datatype_name = correlated_clause_predicate.datatype_name
        correlated_rows = correlated_clause_predicate.correlated_rows
        normalized_operand_items = correlated_clause_predicate.normalized_operand_items
        predicate_expression = correlated_clause_predicate.predicate_expression
        is_template_negated = correlated_clause_predicate.is_template_negated

        if isinstance(predicate_expression, AggregatePredicateSpec):
            aggregate_matches = build_grouped_rows_matching_aggregate_predicate(
                correlated_rows=correlated_rows,
                aggregate_predicate_spec=predicate_expression,
                grouping_field_name="resourceinstanceid",
            )
            return (
                ~Exists(aggregate_matches)
                if is_template_negated
                else Exists(aggregate_matches)
            )

        if not is_template_negated:
            return Exists(correlated_rows.filter(predicate_expression))

        positive_rows = self.positive_rows_for_negated_template(
            operator_token=operator_token,
            datatype_name=datatype_name,
            operand_items=normalized_operand_items,
            correlated_rows=correlated_rows,
            predicate_expression=predicate_expression,
        )
        return ~Exists(positive_rows)

    def compute_child_rows(
        self,
        group_payload: Dict[str, Any],
        correlate_field: str,
        terminal_graph_slug: str,
    ) -> Optional[QuerySet]:
        return self._child_rows_computer.compute_child_rows(
            group_payload, correlate_field, terminal_graph_slug
        )

    def positive_rows_for_negated_template(
        self,
        operator_token: str,
        datatype_name: str,
        operand_items: List[Dict[str, Any]],
        correlated_rows: QuerySet,
        predicate_expression: Q,
    ) -> QuerySet:
        positive_facet = self.facet_registry.resolve_positive_facet(
            operator_token,
            datatype_name,
        )

        if positive_facet is not None:
            positive_expression, _ = self.predicate_builder.build_predicate(
                datatype_name,
                positive_facet.operator,
                operand_items,
                facet=positive_facet,
            )
            return correlated_rows.filter(positive_expression)

        if predicate_expression.negated:
            return correlated_rows.filter(~predicate_expression)

        return correlated_rows.exclude(predicate_expression)
