from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, QuerySet

from arches_search.models.models import AdvancedSearchFacet
from arches_search.utils.advanced_search.constants import (
    QUANTIFIER_ALL,
    QUANTIFIER_ANY,
    QUANTIFIER_NONE,
)
from arches_search.utils.advanced_search.specs import (
    AggregatePredicateSpec,
    CorrelatedLiteralClauseContext,
)


class SearchModelClauseEvaluator:
    def __init__(
        self,
        search_model_registry,
        facet_registry,
        predicate_builder,
        literal_clause_evaluator,
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.predicate_builder = predicate_builder
        self.literal_clause_evaluator = literal_clause_evaluator

    def build_exists(
        self,
        clause_payload: Dict[str, Any],
        correlate_field_name: str,
    ):
        subject = clause_payload["subject"]
        graph_slug = subject["graph_slug"]
        search_models = subject["search_models"]
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        operand_items = clause_payload["operands"]

        if not operand_items:
            any_row_exists = self._combine_exists_expressions(
                [
                    Exists(
                        self._build_search_model_presence_rows(
                            class_name=class_name,
                            graph_slug=graph_slug,
                            correlate_field_name=correlate_field_name,
                        )
                    )
                    for class_name in search_models
                ]
            )
            if any_row_exists is None:
                raise AdvancedSearchFacet.DoesNotExist(
                    f"No search-model classes were provided for operator '{operator_token}'"
                )

            if self._search_models_presence_implies_match(operator_token):
                return (
                    ~any_row_exists
                    if quantifier_token == QUANTIFIER_NONE
                    else any_row_exists
                )

            return (
                any_row_exists
                if quantifier_token == QUANTIFIER_NONE
                else ~any_row_exists
            )

        any_row_exists_fragments = []
        matching_row_exists_fragments = []
        violating_row_exists_fragments = []
        allow_empty_for_negated_any = False

        for class_name in search_models:
            class_context = self._build_search_model_operand_context(
                class_name=class_name,
                graph_slug=graph_slug,
                operator_token=operator_token,
                operand_items=operand_items,
                correlate_field_name=correlate_field_name,
            )
            if class_context is None:
                continue

            any_row_exists_fragments.append(Exists(class_context.correlated_rows))

            if class_context.is_template_negated:
                matching_row_exists_fragments.append(
                    Exists(
                        class_context.correlated_rows.filter(
                            class_context.predicate_expression
                        )
                    )
                )
                positive_rows = (
                    self.literal_clause_evaluator.positive_rows_for_negated_template(
                        operator_token=operator_token,
                        datatype_name=class_context.datatype_name,
                        operand_items=class_context.normalized_operand_items,
                        correlated_rows=class_context.correlated_rows,
                        predicate_expression=class_context.predicate_expression,
                    )
                )
                allow_empty_for_negated_any = (
                    allow_empty_for_negated_any or class_context.facet_arity > 0
                )
                violating_rows = positive_rows
            else:
                matching_row_exists_fragments.append(
                    Exists(
                        class_context.correlated_rows.filter(
                            class_context.predicate_expression
                        )
                    )
                )
                violating_rows = class_context.correlated_rows.exclude(
                    class_context.predicate_expression
                )
            violating_row_exists_fragments.append(Exists(violating_rows))

        matching_row_exists = self._combine_exists_expressions(
            matching_row_exists_fragments
        )
        if matching_row_exists is None:
            raise AdvancedSearchFacet.DoesNotExist(
                f"No facet or search-model mapping found for operator '{operator_token}' "
                f"on search models {search_models}"
            )

        if quantifier_token == QUANTIFIER_ANY:
            if allow_empty_for_negated_any:
                any_row_exists = self._combine_exists_expressions(
                    any_row_exists_fragments
                )
                if any_row_exists is None:
                    raise AdvancedSearchFacet.DoesNotExist(
                        f"No facet or search-model mapping found for operator '{operator_token}' "
                        f"on search models {search_models}"
                    )
                return matching_row_exists | ~any_row_exists
            return matching_row_exists

        if quantifier_token == QUANTIFIER_NONE:
            return ~matching_row_exists

        if quantifier_token == QUANTIFIER_ALL:
            any_row_exists = self._combine_exists_expressions(any_row_exists_fragments)
            violating_row_exists = self._combine_exists_expressions(
                violating_row_exists_fragments
            )
            if any_row_exists is None:
                raise AdvancedSearchFacet.DoesNotExist(
                    f"No facet or search-model mapping found for operator '{operator_token}' "
                    f"on search models {search_models}"
                )
            if violating_row_exists is None:
                return any_row_exists
            return any_row_exists & ~violating_row_exists

        raise ValueError(f"Unsupported quantifier: {quantifier_token}")

    def _build_search_model_presence_rows(
        self,
        class_name: str,
        graph_slug: str,
        correlate_field_name: str,
    ) -> QuerySet:
        model_class, _ = (
            self.search_model_registry.get_model_and_datatype_for_class_name(class_name)
        )
        return model_class.objects.filter(
            graph_slug=graph_slug,
            resourceinstanceid=OuterRef(correlate_field_name),
        )

    def _build_search_model_operand_context(
        self,
        class_name: str,
        graph_slug: str,
        operator_token: str,
        operand_items: List[Dict[str, Any]],
        correlate_field_name: str,
    ) -> Optional[CorrelatedLiteralClauseContext]:
        all_entries = self.search_model_registry.get_all_entries_for_class_name(
            class_name
        )

        try:
            model_class, datatype_name, facet = self._resolve_model_facet_for_operator(
                all_entries=all_entries,
                class_name=class_name,
                operator_token=operator_token,
            )
        except AdvancedSearchFacet.DoesNotExist:
            return None

        correlated_rows = model_class.objects.filter(
            graph_slug=graph_slug,
            resourceinstanceid=OuterRef(correlate_field_name),
        )
        normalized_operand_items, filter_value = (
            model_class.normalize_operands(operand_items)
            if hasattr(model_class, "normalize_operands")
            else (list(operand_items), None)
        )
        correlated_rows = facet.filter_rows(correlated_rows, filter_value)
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
            raise NotImplementedError(
                "Aggregate operators are not supported with SEARCH_MODELS subjects."
            )

        return CorrelatedLiteralClauseContext(
            datatype_name=datatype_name,
            correlated_rows=correlated_rows,
            normalized_operand_items=normalized_operand_items,
            predicate_expression=predicate_expression,
            is_template_negated=is_template_negated,
            facet_arity=facet.arity,
        )

    def _resolve_model_facet_for_operator(
        self,
        all_entries: List[Tuple[Any, str]],
        class_name: str,
        operator_token: str,
    ):
        for model_class, datatype_name in all_entries:
            try:
                facet = self.facet_registry.get_facet_for_model(
                    datatype_name, operator_token, model_class
                )
            except AdvancedSearchFacet.DoesNotExist:
                continue
            return model_class, datatype_name, facet
        raise AdvancedSearchFacet.DoesNotExist(
            f"No facet found for operator '{operator_token}' on any datatype "
            f"associated with search model '{class_name}'"
        )

    def _search_models_presence_implies_match(self, operator_token: str) -> bool:
        if operator_token == "HAS_ANY_VALUE":
            return True
        if operator_token == "HAS_NO_VALUE":
            return False
        raise AdvancedSearchFacet.DoesNotExist(
            f"Operator '{operator_token}' is not supported for empty SEARCH_MODELS operands"
        )

    def _combine_exists_expressions(self, expressions: List[Any]):
        combined_expression = None
        for expression in expressions:
            combined_expression = (
                expression
                if combined_expression is None
                else (combined_expression | expression)
            )
        return combined_expression
