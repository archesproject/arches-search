from __future__ import annotations
from typing import Any, Dict, List

from django.db.models import Exists, OuterRef, Q
from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.operand_compiler import OperandCompiler
from arches_search.utils.advanced_search.relationship_compiler import (
    RelationshipCompiler,
)


SCOPE_RESOURCE = "RESOURCE"
SCOPE_TILE = "TILE"

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"


class ClauseCompiler:
    def __init__(
        self,
        search_model_registry,
        facet_registry,
        path_navigator,
        operand_compiler: OperandCompiler,
        relationship_compiler: RelationshipCompiler,
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.operand_compiler = operand_compiler
        self.relationship_compiler = relationship_compiler

    def compile(
        self, clause_payload: Dict[str, Any], correlate_to_tile: bool = False
    ) -> Exists:
        clause_type = clause_payload["type"].upper()

        if clause_type == CLAUSE_TYPE_LITERAL:
            return self._compile_literal_clause(clause_payload, correlate_to_tile)
        if clause_type == CLAUSE_TYPE_RELATED:
            return self._compile_related_clause(clause_payload)

        return Exists(arches_models.ResourceInstance.objects.none())

    def _compile_related_clause(self, clause_payload: Dict[str, Any]) -> Exists:
        return self.relationship_compiler.related_presence_exists(clause_payload)

    def _compile_literal_clause(
        self, clause_payload: Dict[str, Any], correlate_to_tile: bool
    ) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"].upper()
        quantifier_token = clause_payload["quantifier"].upper()
        operand_items = clause_payload.get("operands")

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)
        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug, node_alias=subject_node_alias
        )

        if correlate_to_tile:
            correlated_rows = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstance_id"),
                tileid=OuterRef("tileid"),
            )
        else:
            correlated_rows = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            )

        if not operand_items:
            presence_implies_match = self.facet_registry.zero_arity_presence_is_match(
                datatype_name, operator_token
            )
            if quantifier_token == QUANTIFIER_NONE:
                return (
                    ~Exists(correlated_rows)
                    if presence_implies_match
                    else Exists(correlated_rows)
                )
            if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
                return (
                    Exists(correlated_rows)
                    if presence_implies_match
                    else ~Exists(correlated_rows)
                )

        predicate_expression, is_template_negated = (
            self.operand_compiler.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=operand_items,
                anchor_resource_id_annotation=None,
            )
        )
        matching_rows = (
            correlated_rows.filter(predicate_expression)
            if isinstance(predicate_expression, Q)
            else correlated_rows.filter(**predicate_expression)
        )

        if quantifier_token == QUANTIFIER_ANY:
            return Exists(matching_rows)
        if quantifier_token == QUANTIFIER_NONE:
            return ~Exists(matching_rows)

        if not is_template_negated:
            violating_rows = (
                correlated_rows.exclude(predicate_expression)
                if isinstance(predicate_expression, Q)
                else correlated_rows.exclude(**predicate_expression)
            )
            return Exists(correlated_rows) & ~Exists(violating_rows)

        positive_facet = self.facet_registry.get_positive_facet_for(
            operator_token, datatype_name
        )
        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name,
                positive_facet.operator,
                "value",
                self.operand_compiler.literal_values_only(operand_items),
            )
            positive_rows = (
                correlated_rows.filter(positive_expression)
                if isinstance(positive_expression, Q)
                else correlated_rows.filter(**positive_expression)
            )
            return Exists(correlated_rows) & ~Exists(positive_rows)

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            return Exists(correlated_rows) & ~Exists(
                correlated_rows.filter(~predicate_expression)
            )

        return Exists(correlated_rows) & ~Exists(matching_rows)
