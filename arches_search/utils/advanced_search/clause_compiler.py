from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet
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

    # ---------- public surface (kept for GroupCompiler compatibility)

    def compile(
        self, clause_payload: Dict[str, Any], correlate_to_tile: bool = False
    ) -> Exists:
        clause_type = (clause_payload["type"] or "").upper()
        if clause_type == CLAUSE_TYPE_LITERAL:
            return self._compile_literal(clause_payload, correlate_to_tile)
        if clause_type == CLAUSE_TYPE_RELATED:
            return self.relationship_compiler.related_presence_exists(clause_payload)
        return Exists(arches_models.ResourceInstance.objects.none())

    def compile_literal_to_q(
        self, clause_payload: Dict[str, Any], scope: str
    ) -> Optional[Q]:
        if (scope or "").upper() == SCOPE_TILE:
            return self.compile_relationshipless_tile_group_to_q(
                {"clauses": [clause_payload], "logic": "AND"},
                use_and_logic=True,
            )
        return Q(self.compile(clause_payload, correlate_to_tile=False))

    def compile_relationshipless_tile_group_to_q(
        self, group_payload: Dict[str, Any], use_and_logic: bool
    ) -> Q:
        clause_payloads = group_payload.get("clauses") or []
        if not clause_payloads:
            return Q()

        tiles_for_anchor_resource = arches_models.Tile.objects.filter(
            resourceinstance_id=OuterRef("resourceinstanceid")
        )

        per_tile_exists_conditions: List[Q] = []
        resource_level_conditions: List[Q] = []

        for clause_payload in clause_payloads:
            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = (clause_payload["operator"] or "").upper()
            quantifier_token = (clause_payload["quantifier"] or "").upper()
            operand_items = clause_payload.get("operands") or []

            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
            )
            model_class = self.search_model_registry.get_model_for_datatype(
                datatype_name
            )
            subject_rows = model_class.objects.filter(
                graph_slug=subject_graph_slug, node_alias=subject_node_alias
            )

            rows_correlated_to_resource = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            )
            rows_correlated_to_tile_resource = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstance_id")
            )

            if not operand_items:
                presence_means_match = self._presence_means_match_for_zero_operands(
                    datatype_name, operator_token
                )

                if quantifier_token == QUANTIFIER_ANY:
                    condition = Q(
                        Exists(
                            rows_correlated_to_tile_resource.filter(
                                tileid=OuterRef("tileid")
                            )
                        )
                    )
                    per_tile_exists_conditions.append(
                        condition if presence_means_match else ~condition
                    )
                    continue

                if quantifier_token == QUANTIFIER_NONE:
                    resource_level_conditions.append(
                        Q(~Exists(rows_correlated_to_resource))
                        if presence_means_match
                        else Q(Exists(rows_correlated_to_resource))
                    )
                    continue

                tiles_missing_match = tiles_for_anchor_resource.filter(
                    ~Exists(
                        rows_correlated_to_tile_resource.filter(
                            tileid=OuterRef("tileid")
                        )
                    )
                )
                requires_all_tiles_match = Q(~Exists(tiles_missing_match))
                has_at_least_one_tile = Q(Exists(tiles_for_anchor_resource))
                resource_level_conditions.append(
                    (requires_all_tiles_match & has_at_least_one_tile)
                    if presence_means_match
                    else Q(~Exists(tiles_for_anchor_resource))
                )
                continue

            predicate_expression, is_template_negated = (
                self.operand_compiler.build_predicate(
                    datatype_name=datatype_name,
                    operator_token=operator_token,
                    operands=operand_items,
                    anchor_resource_id_annotation=None,
                )
            )

            if isinstance(predicate_expression, Q):
                matching_rows_resource = rows_correlated_to_resource.filter(
                    predicate_expression
                )
                matches_in_this_tile = rows_correlated_to_tile_resource.filter(
                    predicate_expression
                ).filter(tileid=OuterRef("tileid"))
            else:
                matching_rows_resource = rows_correlated_to_resource.filter(
                    **predicate_expression
                )
                matches_in_this_tile = rows_correlated_to_tile_resource.filter(
                    **predicate_expression
                ).filter(tileid=OuterRef("tileid"))

            if quantifier_token == QUANTIFIER_ANY:
                per_tile_exists_conditions.append(Q(Exists(matches_in_this_tile)))
                continue

            if quantifier_token == QUANTIFIER_NONE:
                resource_level_conditions.append(Q(~Exists(matching_rows_resource)))
                continue

            has_at_least_one_tile = Q(Exists(tiles_for_anchor_resource))

            if not is_template_negated:
                tiles_missing_match = tiles_for_anchor_resource.filter(
                    ~Exists(matches_in_this_tile)
                )
                resource_level_conditions.append(
                    Q(~Exists(tiles_missing_match)) & has_at_least_one_tile
                )
                continue

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
                if isinstance(positive_expression, Q):
                    positive_matches_in_this_tile = (
                        rows_correlated_to_tile_resource.filter(
                            positive_expression
                        ).filter(tileid=OuterRef("tileid"))
                    )
                else:
                    positive_matches_in_this_tile = (
                        rows_correlated_to_tile_resource.filter(
                            **positive_expression
                        ).filter(tileid=OuterRef("tileid"))
                    )
            elif isinstance(predicate_expression, Q) and getattr(
                predicate_expression, "negated", False
            ):
                positive_matches_in_this_tile = rows_correlated_to_tile_resource.filter(
                    ~predicate_expression
                ).filter(tileid=OuterRef("tileid"))
            else:
                if isinstance(predicate_expression, Q):
                    positive_matches_in_this_tile = (
                        rows_correlated_to_tile_resource.exclude(
                            predicate_expression
                        ).filter(tileid=OuterRef("tileid"))
                    )
                else:
                    positive_matches_in_this_tile = (
                        rows_correlated_to_tile_resource.exclude(
                            **predicate_expression
                        ).filter(tileid=OuterRef("tileid"))
                    )

            tiles_with_violations = tiles_for_anchor_resource.filter(
                Exists(positive_matches_in_this_tile)
            )
            resource_level_conditions.append(
                Q(~Exists(tiles_with_violations)) & has_at_least_one_tile
            )

        if not per_tile_exists_conditions:
            any_expression = Q()
        else:
            if use_and_logic:
                tiles_requiring_all = tiles_for_anchor_resource
                for condition in per_tile_exists_conditions:
                    tiles_requiring_all = tiles_requiring_all.filter(condition)
                any_expression = Q(Exists(tiles_requiring_all))
            else:
                combined_any = Q(pk__in=[])
                for condition in per_tile_exists_conditions:
                    combined_any |= condition
                tiles_with_any = tiles_for_anchor_resource.filter(combined_any)
                any_expression = Q(Exists(tiles_with_any))

        if not resource_level_conditions:
            return any_expression

        if use_and_logic:
            combined_all = Q()
            for condition in resource_level_conditions:
                combined_all &= condition
            return any_expression & combined_all

        combined_or = Q()
        for condition in resource_level_conditions:
            combined_or |= condition
        return any_expression | combined_or

    def filter_pairs_by_clause(
        self,
        pairs_queryset: QuerySet,
        clause_payload: Dict[str, Any],
        correlate_field: str,
    ) -> Tuple[QuerySet, bool]:
        return self.relationship_compiler.filter_pairs_by_clause(
            pairs_queryset, clause_payload, correlate_field
        )

    def related_child_exists_qs(
        self, clause_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ) -> Optional[QuerySet]:
        return self.relationship_compiler.related_child_exists_qs(
            clause_payload, compiled_pair_info
        )

    def child_ok_rows_from_literals(
        self, group_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ) -> Optional[QuerySet]:
        return self.relationship_compiler.child_ok_rows_from_literals(
            group_payload, compiled_pair_info
        )

    def fetch_subject_rows(
        self, graph_slug: str, node_alias: str
    ) -> Optional[QuerySet]:
        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                graph_slug, node_alias
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)
        return model_class.objects.filter(graph_slug=graph_slug, node_alias=node_alias)

    # ---------- literal-only engine

    def _compile_literal(
        self, clause_payload: Dict[str, Any], correlate_to_tile: bool
    ) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload["operator"] or "").upper()
        quantifier_token = (clause_payload["quantifier"] or "").upper()
        operand_items = clause_payload.get("operands") or []

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
            presence_means_match = self._presence_means_match_for_zero_operands(
                datatype_name, operator_token
            )
            if quantifier_token == QUANTIFIER_NONE:
                return (
                    ~Exists(correlated_rows)
                    if presence_means_match
                    else Exists(correlated_rows)
                )
            if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
                return (
                    Exists(correlated_rows)
                    if presence_means_match
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

    def _presence_means_match_for_zero_operands(
        self, datatype_name: str, operator_token: str
    ) -> bool:
        facet = self.facet_registry.get_facet(datatype_name, operator_token)
        accepts_no_operands = not bool(getattr(facet, "operand_types", None))
        if not accepts_no_operands:
            return False
        return bool(getattr(facet, "is_orm_template_negated", False))
