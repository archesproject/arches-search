from typing import Any, Dict, List, Optional, Tuple
from django.db.models import Exists, OuterRef, Q, QuerySet
from arches.app.models import models as arches_models

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"


class LiteralClauseEvaluator:
    def __init__(
        self,
        search_model_registry,
        facet_registry,
        path_navigator,
        operand_compiler,
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.operand_compiler = operand_compiler

    # ---------- Existing resource-scope helpers ----------

    def exists_for_anchor(self, clause_payload: Dict[str, Any]) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload.get("operator") or "").upper()
        quantifier_token = (clause_payload.get("quantifier") or "").upper()
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

    def exists_for_child(
        self, clause_payload: Dict[str, Any], *, correlate_field: str
    ) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload.get("operator") or "").upper()
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
        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef(correlate_field)
        )

        if not operand_items:
            presence_implies_match = self.facet_registry.zero_arity_presence_is_match(
                datatype_name, operator_token
            )
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

        if not is_template_negated:
            if isinstance(predicate_expression, Q):
                return Exists(correlated_rows.filter(predicate_expression))
            return Exists(correlated_rows.filter(**predicate_expression))

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
                return ~Exists(correlated_rows.filter(positive_expression))
            return ~Exists(correlated_rows.filter(**positive_expression))

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            return ~Exists(correlated_rows.filter(~predicate_expression))

        if isinstance(predicate_expression, Q):
            return ~Exists(correlated_rows.filter(predicate_expression))
        return ~Exists(correlated_rows.filter(**predicate_expression))

    def ok_child_rows_from_literals(
        self,
        group_payload: Dict[str, Any],
        *,
        correlate_field: str,
        terminal_graph_slug: str,
    ) -> Optional[QuerySet]:
        literal_clauses: List[Dict[str, Any]] = []
        for child_group_payload in group_payload.get("groups") or []:
            if (child_group_payload.get("relationship") or {}).get("path"):
                continue
            if (child_group_payload.get("logic") or "AND").upper() != "AND":
                return None

            pending_nodes: List[Dict[str, Any]] = [child_group_payload]
            while pending_nodes:
                node_payload = pending_nodes.pop()
                if (node_payload.get("relationship") or {}).get("path"):
                    continue

                for clause_payload in node_payload.get("clauses") or []:
                    if (
                        clause_payload.get("type") or ""
                    ).upper() != CLAUSE_TYPE_LITERAL:
                        continue
                    subject_graph_slug, _ = clause_payload["subject"][0]
                    if subject_graph_slug != terminal_graph_slug:
                        return None
                    literal_clauses.append(clause_payload)

                for nested in node_payload.get("groups") or []:
                    pending_nodes.append(nested)

        if not literal_clauses:
            return None

        accumulated_rows = None
        for clause_payload in literal_clauses:
            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = (clause_payload["operator"] or "").upper()
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
            correlated_rows = subject_rows.filter(
                resourceinstanceid=OuterRef(correlate_field)
            )

            if not operand_items:
                presence_implies_match = (
                    self.facet_registry.zero_arity_presence_is_match(
                        datatype_name, operator_token
                    )
                )
                predicate_rows = (
                    correlated_rows
                    if presence_implies_match
                    else correlated_rows.none()
                )
            else:
                predicate_expression, is_template_negated = (
                    self.operand_compiler.build_predicate(
                        datatype_name=datatype_name,
                        operator_token=operator_token,
                        operands=operand_items,
                        anchor_resource_id_annotation=None,
                    )
                )
                filtered_rows = (
                    correlated_rows.filter(predicate_expression)
                    if isinstance(predicate_expression, Q)
                    else correlated_rows.filter(**predicate_expression)
                )
                if not is_template_negated:
                    predicate_rows = filtered_rows
                else:
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
                        predicate_rows = (
                            correlated_rows.exclude(positive_expression)
                            if isinstance(positive_expression, Q)
                            else correlated_rows.exclude(**positive_expression)
                        )
                    elif isinstance(predicate_expression, Q) and getattr(
                        predicate_expression, "negated", False
                    ):
                        predicate_rows = correlated_rows.exclude(~predicate_expression)
                    else:
                        predicate_rows = (
                            correlated_rows.exclude(predicate_expression)
                            if isinstance(predicate_expression, Q)
                            else correlated_rows.exclude(**predicate_expression)
                        )

            if accumulated_rows is None:
                accumulated_rows = predicate_rows
            else:
                accumulated_rows = accumulated_rows.filter(
                    pk__in=predicate_rows.values("pk")
                )

        return accumulated_rows

    # ---------- New tile-scope helper (isolates all operand handling) ----------

    def evaluate_literal_clause_for_tile_scope(
        self,
        *,
        clause_payload: Dict[str, Any],
        tiles_for_anchor_resource: QuerySet,
        tile_id_outer_ref: Any,
    ) -> Tuple[Optional[Q], Optional[Q]]:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload.get("operator") or "").upper()
        quantifier_token = (clause_payload.get("quantifier") or "").upper()
        operand_items = clause_payload.get("operands") or []

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)

        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug,
            node_alias=subject_node_alias,
        )
        resource_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstanceid")
        )
        tile_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstance_id")
        )

        resource_has_any_tile_q = Q(Exists(tiles_for_anchor_resource))

        if not operand_items:
            presence_implies_match = self.facet_registry.zero_arity_presence_is_match(
                datatype_name, operator_token
            )
            if quantifier_token == QUANTIFIER_ANY:
                present_in_tile = Q(Exists(tile_rows.filter(tileid=tile_id_outer_ref)))
                return (
                    present_in_tile if presence_implies_match else ~present_in_tile,
                    None,
                )

            if quantifier_token == QUANTIFIER_NONE:
                return (
                    None,
                    (
                        Q(~Exists(resource_rows))
                        if presence_implies_match
                        else Q(Exists(resource_rows))
                    ),
                )

            tiles_missing_match = tiles_for_anchor_resource.filter(
                ~Exists(tile_rows.filter(tileid=tile_id_outer_ref))
            )
            resource_level_q = (
                (Q(~Exists(tiles_missing_match)) & resource_has_any_tile_q)
                if presence_implies_match
                else Q(~Exists(tiles_for_anchor_resource))
            )
            return (None, resource_level_q)

        predicate_expression, is_template_negated = (
            self.operand_compiler.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=operand_items,
                anchor_resource_id_annotation=None,
            )
        )

        if isinstance(predicate_expression, Q):
            resource_matches = resource_rows.filter(predicate_expression)
            tile_matches = tile_rows.filter(predicate_expression).filter(
                tileid=tile_id_outer_ref
            )
        else:
            resource_matches = resource_rows.filter(**predicate_expression)
            tile_matches = tile_rows.filter(**predicate_expression).filter(
                tileid=tile_id_outer_ref
            )

        if quantifier_token == QUANTIFIER_ANY:
            return (Q(Exists(tile_matches)), None)

        if quantifier_token == QUANTIFIER_NONE:
            return (None, Q(~Exists(resource_matches)))

        if not is_template_negated:
            tiles_missing_match = tiles_for_anchor_resource.filter(
                ~Exists(tile_matches)
            )
            return (
                None,
                Q(~Exists(tiles_missing_match)) & resource_has_any_tile_q,
            )

        positive_tile_matches = self._derive_positive_tile_matches_for_tile_scope(
            tile_rows=tile_rows,
            tile_id_outer_ref=tile_id_outer_ref,
            predicate_expression=predicate_expression,
            operator_token=operator_token,
            datatype_name=datatype_name,
            operand_items=operand_items,
        )
        tiles_with_violations = tiles_for_anchor_resource.filter(
            Exists(positive_tile_matches)
        )
        return (
            None,
            Q(~Exists(tiles_with_violations)) & resource_has_any_tile_q,
        )

    def _derive_positive_tile_matches_for_tile_scope(
        self,
        *,
        tile_rows: QuerySet,
        tile_id_outer_ref: Any,
        predicate_expression: Any,
        operator_token: str,
        datatype_name: str,
        operand_items: List[Dict[str, Any]],
    ) -> QuerySet:
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
                return tile_rows.filter(positive_expression).filter(
                    tileid=tile_id_outer_ref
                )
            return tile_rows.filter(**positive_expression).filter(
                tileid=tile_id_outer_ref
            )

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            return tile_rows.filter(~predicate_expression).filter(
                tileid=tile_id_outer_ref
            )

        if isinstance(predicate_expression, Q):
            return tile_rows.exclude(predicate_expression).filter(
                tileid=tile_id_outer_ref
            )

        return tile_rows.exclude(**predicate_expression).filter(
            tileid=tile_id_outer_ref
        )
