from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet

from arches_search.models.models import AdvancedSearchFacet
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
from arches_search.utils.advanced_search.relationship_utils import (
    has_relationship_path,
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

    def _build_exists_for_search_models(
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
                positive_rows = self.positive_rows_for_negated_template(
                    operator_token=operator_token,
                    datatype_name=class_context.datatype_name,
                    operand_items=class_context.normalized_operand_items,
                    correlated_rows=class_context.correlated_rows,
                    predicate_expression=class_context.predicate_expression,
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
    ) -> CorrelatedLiteralClauseContext | None:
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

    def _combine_exists_expressions(self, expressions: List[Any]):
        combined_expression = None
        for expression in expressions:
            combined_expression = (
                expression
                if combined_expression is None
                else (combined_expression | expression)
            )
        return combined_expression

    def _search_models_presence_implies_match(self, operator_token: str) -> bool:
        if operator_token == "HAS_ANY_VALUE":
            return True
        if operator_token == "HAS_NO_VALUE":
            return False
        raise AdvancedSearchFacet.DoesNotExist(
            f"Operator '{operator_token}' is not supported for empty SEARCH_MODELS operands"
        )

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
            return self._build_exists_for_search_models(
                clause_payload=clause_payload,
                correlate_field_name="resourceinstanceid",
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
            return self._build_exists_for_search_models(
                clause_payload=clause_payload,
                correlate_field_name=correlate_field,
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
        literal_clauses: List[Dict[str, Any]] = []

        for direct_child_group in group_payload["groups"]:
            if has_relationship_path(direct_child_group.get("relationship")):
                continue

            pending_groups: List[Dict[str, Any]] = [direct_child_group]
            while pending_groups:
                current_group = pending_groups.pop()
                if has_relationship_path(current_group.get("relationship")):
                    continue

                for clause_payload in current_group["clauses"]:
                    clause_type_token = clause_payload["type"]
                    if clause_type_token == CLAUSE_TYPE_LITERAL:
                        subject = clause_payload["subject"]
                        if subject.get("type") == SUBJECT_TYPE_SEARCH_MODELS:
                            continue
                        clause_graph_slug = subject["graph_slug"]
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
                normalized_operand_items, filter_value = (
                    model_class.normalize_operands(operand_items)
                    if hasattr(model_class, "normalize_operands")
                    else (list(operand_items), None)
                )
                correlated_rows = facet.filter_rows(
                    base_rows.filter(resourceinstanceid=OuterRef(correlate_field)),
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
