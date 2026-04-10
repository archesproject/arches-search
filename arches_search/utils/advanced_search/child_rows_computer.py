from typing import Any, Dict, List, Optional

from django.db.models import OuterRef, QuerySet

from arches_search.utils.advanced_search.aggregate_predicate_runtime import (
    build_grouped_rows_matching_aggregate_predicate,
)
from arches_search.utils.advanced_search.constants import (
    CLAUSE_TYPE_LITERAL,
    CLAUSE_TYPE_RELATED,
    SUBJECT_TYPE_SEARCH_MODELS,
)
from arches_search.utils.advanced_search.relationship_utils import has_relationship_path
from arches_search.utils.advanced_search.specs import AggregatePredicateSpec


class ChildRowsComputer:
    def __init__(self, literal_clause_evaluator) -> None:
        self.literal_clause_evaluator = literal_clause_evaluator

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

        evaluator = self.literal_clause_evaluator
        intersected_rows: Optional[QuerySet] = None

        for clause_payload in literal_clauses:
            subject = clause_payload["subject"]
            subject_graph_slug = subject["graph_slug"]
            subject_node_alias = subject["node_alias"]
            operator_token = clause_payload["operator"]
            operand_items = clause_payload["operands"]

            datatype_name, facet, model_class = evaluator.resolve_facet_and_model(
                subject_graph_slug=subject_graph_slug,
                subject_node_alias=subject_node_alias,
                operator_token=operator_token,
            )

            if not operand_items:
                presence_implies_match = (
                    evaluator.facet_registry.presence_implies_match(
                        datatype_name,
                        operator_token,
                    )
                )
                base_row_sets = evaluator.build_presence_subject_row_sets(
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
                base_rows = evaluator.build_subject_rows(
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
                    evaluator.predicate_builder.build_predicate(
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
                        positive_rows = evaluator.positive_rows_for_negated_template(
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
