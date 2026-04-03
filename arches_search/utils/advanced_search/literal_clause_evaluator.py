from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from arches_search.models.models import AdvancedSearchFacet

from django.db.models import Exists, OuterRef, Q, QuerySet
from django.utils.translation import get_language

from arches_search.utils.advanced_search.aggregate_predicate_runtime import (
    build_grouped_rows_matching_aggregate_predicate,
)
from arches_search.utils.advanced_search.constants import (
    CLAUSE_TYPE_LITERAL,
    CLAUSE_TYPE_RELATED,
    QUANTIFIER_ALL,
    QUANTIFIER_ANY,
    QUANTIFIER_NONE,
)
from arches_search.utils.advanced_search.specs import (
    AggregatePredicateSpec,
    CorrelatedLiteralClauseContext,
)


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
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
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
        normalized_operand_items, localized_language = self.localize_string_operands(
            facet=facet,
            operand_items=operand_items,
        )
        correlated_rows = self.apply_localized_language_filter(
            subject_rows.filter(resourceinstanceid=OuterRef(correlate_field_name)),
            facet=facet,
            localized_language=localized_language,
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
        )

    def build_anchor_exists(self, clause_payload: Dict[str, Any]) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
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
            return Exists(correlated_rows.filter(predicate_expression))

        if quantifier_token == QUANTIFIER_NONE:
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
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
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
        literal_clauses: List[Dict[str, Any]] = []

        for direct_child_group in group_payload["groups"]:
            if direct_child_group["relationship"]["path"]:
                continue

            pending_groups: List[Dict[str, Any]] = [direct_child_group]
            while pending_groups:
                current_group = pending_groups.pop()
                if current_group["relationship"]["path"]:
                    continue

                for clause_payload in current_group["clauses"]:
                    clause_type_token = clause_payload["type"]
                    if clause_type_token == CLAUSE_TYPE_LITERAL:
                        clause_graph_slug, _ = clause_payload["subject"][0]
                        if clause_graph_slug != terminal_graph_slug:
                            return None
                        literal_clauses.append(clause_payload)
                    elif clause_type_token == CLAUSE_TYPE_RELATED:
                        continue
                    else:
                        continue

                pending_groups.extend(current_group["groups"])

        if not literal_clauses:
            return None

        intersected_rows: Optional[QuerySet] = None

        for clause_payload in literal_clauses:
            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = clause_payload["operator"]
            operand_items = clause_payload["operands"]

            datatype_name, facet, model_class = self.resolve_facet_and_model(
                subject_graph_slug=subject_graph_slug,
                subject_node_alias=subject_node_alias,
                operator_token=operator_token,
            )

            if not operand_items:
                presence_implies_match = self.facet_registry.presence_implies_match(
                    datatype_name,
                    operator_token,
                )
                base_row_sets = self.build_presence_subject_row_sets(
                    datatype_name=datatype_name,
                    subject_graph_slug=subject_graph_slug,
                    subject_node_alias=subject_node_alias,
                )
                if presence_implies_match:
                    predicate_rows = None
                    for base_rows in base_row_sets:
                        correlated_rows = base_rows.filter(
                            resourceinstanceid=OuterRef(correlate_field)
                        ).values("resourceinstanceid")
                        predicate_rows = (
                            correlated_rows
                            if predicate_rows is None
                            else predicate_rows.union(correlated_rows)
                        )
                else:
                    first_model_class = base_row_sets[0].model
                    predicate_rows = first_model_class.objects.none().values(
                        "resourceinstanceid"
                    )
            else:
                base_rows = self.build_subject_rows(
                    model_class=model_class,
                    subject_graph_slug=subject_graph_slug,
                    subject_node_alias=subject_node_alias,
                )
                normalized_operand_items, localized_language = (
                    self.localize_string_operands(
                        facet=facet,
                        operand_items=operand_items,
                    )
                )
                correlated_rows = self.apply_localized_language_filter(
                    base_rows.filter(resourceinstanceid=OuterRef(correlate_field)),
                    facet=facet,
                    localized_language=localized_language,
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
                if isinstance(predicate_expression, AggregatePredicateSpec):
                    positive_rows = build_grouped_rows_matching_aggregate_predicate(
                        correlated_rows=correlated_rows,
                        aggregate_predicate_spec=predicate_expression,
                        grouping_field_name="resourceinstanceid",
                    )
                    if not is_template_negated:
                        predicate_rows = positive_rows
                    else:
                        predicate_rows = (
                            correlated_rows.values("resourceinstanceid")
                            .exclude(
                                resourceinstanceid__in=positive_rows.values(
                                    "resourceinstanceid"
                                )
                            )
                            .distinct()
                        )
                else:
                    if not is_template_negated:
                        predicate_rows = correlated_rows.filter(predicate_expression)
                    else:
                        positive_rows = self.positive_rows_for_negated_template(
                            operator_token=operator_token,
                            datatype_name=datatype_name,
                            operand_items=normalized_operand_items,
                            correlated_rows=correlated_rows,
                            predicate_expression=predicate_expression,
                        )
                        predicate_rows = correlated_rows.exclude(
                            pk__in=positive_rows.values("pk")
                        )

            intersected_rows = (
                predicate_rows
                if intersected_rows is None
                else intersected_rows.filter(
                    resourceinstanceid__in=predicate_rows.values("resourceinstanceid")
                )
            )

        return intersected_rows

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

    def localize_string_operands(
        self,
        facet: AdvancedSearchFacet,
        operand_items: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        if not facet.filter_field:
            return operand_items, None

        language_code = get_language()
        short_language_code = None

        if language_code:
            short_language_code = language_code.split("-")[0]

        normalized_items: List[Dict[str, Any]] = []
        localized_language: Optional[str] = None

        for operand_item in operand_items:
            raw_value = operand_item.get("value")

            if isinstance(raw_value, dict) and raw_value:
                chosen_value = None
                chosen_language = None

                if language_code and language_code in raw_value:
                    chosen_language = language_code
                    chosen_value = raw_value[language_code]
                elif short_language_code and short_language_code in raw_value:
                    chosen_language = short_language_code
                    chosen_value = raw_value[short_language_code]
                else:
                    chosen_language, chosen_value = next(iter(raw_value.items()))

                normalized_items.append({**operand_item, "value": chosen_value})

                if localized_language is None:
                    localized_language = chosen_language
                elif chosen_language != localized_language:
                    raise ValueError(
                        "Localized string operands resolved to different languages"
                    )
            else:
                normalized_items.append(operand_item)

        return normalized_items, localized_language

    def apply_localized_language_filter(
        self,
        rows: QuerySet,
        facet: AdvancedSearchFacet,
        localized_language: Optional[str],
    ) -> QuerySet:
        if not facet.filter_field or localized_language is None:
            return rows

        return rows.filter(**{facet.filter_field: localized_language})
