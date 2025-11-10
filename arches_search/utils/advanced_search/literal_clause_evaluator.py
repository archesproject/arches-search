from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet

LOGIC_AND = "AND"
LOGIC_OR = "OR"

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"


class LiteralClauseEvaluator:
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
        clause_payload: Optional[Dict[str, Any]] = None,
        correlate_field: Optional[str] = None,
        tiles_for_anchor_resource: Optional[QuerySet] = None,
        tile_id_outer_ref: Optional[Any] = None,
        group_payload: Optional[Dict[str, Any]] = None,
        terminal_graph_slug: Optional[str] = None,
    ):
        if mode == "anchor":
            return self._build_anchor_exists(clause_payload)
        if mode == "child":
            return self._build_child_exists(clause_payload, correlate_field)
        if mode == "tile":
            return self._build_tile_scope_predicates(
                clause_payload, tiles_for_anchor_resource, tile_id_outer_ref
            )
        if mode == "compute_child_rows":
            return self._compute_child_rows(
                group_payload, correlate_field, terminal_graph_slug
            )
        raise ValueError(f"Unsupported evaluation mode: {mode}")

    def _build_anchor_exists(self, clause_payload: Dict[str, Any]) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        operand_items = clause_payload["operands"]

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
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name, operator_token
            )
            if quantifier_token == QUANTIFIER_NONE:
                return (
                    ~Exists(correlated_rows)
                    if presence_implies_match
                    else Exists(correlated_rows)
                )
            return (
                Exists(correlated_rows)
                if presence_implies_match
                else ~Exists(correlated_rows)
            )

        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=operand_items,
                anchor_resource_id_annotation=None,
            )
        )

        if isinstance(predicate_expression, Q):
            matching_rows = correlated_rows.filter(predicate_expression)
            violating_rows = correlated_rows.exclude(predicate_expression)
        else:
            matching_rows = correlated_rows.filter(**predicate_expression)
            violating_rows = correlated_rows.exclude(**predicate_expression)

        if quantifier_token == QUANTIFIER_ANY:
            return Exists(matching_rows)
        if quantifier_token == QUANTIFIER_NONE:
            return ~Exists(matching_rows)

        if not is_template_negated:
            return Exists(correlated_rows) & ~Exists(violating_rows)

        positive_facet = self.facet_registry.resolve_positive_facet(
            operator_token, datatype_name
        )
        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name,
                positive_facet.operator,
                "value",
                self._literal_values_only(operand_items),
            )
            if isinstance(positive_expression, Q):
                positive_rows = correlated_rows.filter(positive_expression)
            else:
                positive_rows = correlated_rows.filter(**positive_expression)
            return Exists(correlated_rows) & ~Exists(positive_rows)

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            return Exists(correlated_rows) & ~Exists(
                correlated_rows.filter(~predicate_expression)
            )

        return Exists(correlated_rows) & ~Exists(matching_rows)

    def _build_child_exists(
        self, clause_payload: Dict[str, Any], correlate_field: str
    ) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"]
        operand_items = clause_payload["operands"]

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
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name, operator_token
            )
            return (
                Exists(correlated_rows)
                if presence_implies_match
                else ~Exists(correlated_rows)
            )

        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
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

        positive_facet = self.facet_registry.resolve_positive_facet(
            operator_token, datatype_name
        )
        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name,
                positive_facet.operator,
                "value",
                self._literal_values_only(operand_items),
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

    def _compute_child_rows(
        self,
        group_payload: Dict[str, Any],
        correlate_field: str,
        terminal_graph_slug: str,
    ) -> Optional[QuerySet]:
        literal_clauses: List[Dict[str, Any]] = []

        for direct_child_group in group_payload["groups"]:
            if direct_child_group["relationship"]["path"]:
                continue
            if direct_child_group["logic"] != LOGIC_AND:
                return None

            pending_groups: List[Dict[str, Any]] = [direct_child_group]
            while pending_groups:
                current_group = pending_groups.pop()
                if current_group["relationship"]["path"]:
                    continue

                for clause_payload in current_group["clauses"]:
                    if clause_payload["type"] != CLAUSE_TYPE_LITERAL:
                        continue
                    clause_graph_slug, _ = clause_payload["subject"][0]
                    if clause_graph_slug != terminal_graph_slug:
                        return None
                    literal_clauses.append(clause_payload)

                pending_groups.extend(current_group["groups"])

        if not literal_clauses:
            return None

        intersected_rows: Optional[QuerySet] = None

        for clause_payload in literal_clauses:
            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = clause_payload["operator"]
            operand_items = clause_payload["operands"]

            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
            )
            model_class = self.search_model_registry.get_model_for_datatype(
                datatype_name
            )

            base_rows = model_class.objects.filter(
                graph_slug=subject_graph_slug, node_alias=subject_node_alias
            )
            correlated_rows = base_rows.filter(
                resourceinstanceid=OuterRef(correlate_field)
            )

            if not operand_items:
                presence_implies_match = self.facet_registry.presence_implies_match(
                    datatype_name, operator_token
                )
                predicate_rows = (
                    correlated_rows
                    if presence_implies_match
                    else correlated_rows.none()
                )
            else:
                predicate_expression, is_template_negated = (
                    self.predicate_builder.build_predicate(
                        datatype_name=datatype_name,
                        operator_token=operator_token,
                        operands=operand_items,
                        anchor_resource_id_annotation=None,
                    )
                )

                if isinstance(predicate_expression, Q):
                    filtered_rows = correlated_rows.filter(predicate_expression)
                    excluded_rows = correlated_rows.exclude(predicate_expression)
                else:
                    filtered_rows = correlated_rows.filter(**predicate_expression)
                    excluded_rows = correlated_rows.exclude(**predicate_expression)

                if not is_template_negated:
                    predicate_rows = filtered_rows
                else:
                    positive_facet = self.facet_registry.resolve_positive_facet(
                        operator_token, datatype_name
                    )
                    if positive_facet is not None:
                        positive_expression, _ = self.facet_registry.predicate(
                            datatype_name,
                            positive_facet.operator,
                            "value",
                            self._literal_values_only(operand_items),
                        )
                        if isinstance(positive_expression, Q):
                            predicate_rows = correlated_rows.exclude(
                                positive_expression
                            )
                        else:
                            predicate_rows = correlated_rows.exclude(
                                **positive_expression
                            )
                    elif isinstance(predicate_expression, Q) and getattr(
                        predicate_expression, "negated", False
                    ):
                        predicate_rows = correlated_rows.exclude(~predicate_expression)
                    else:
                        predicate_rows = excluded_rows

            intersected_rows = (
                predicate_rows
                if intersected_rows is None
                else intersected_rows.filter(pk__in=predicate_rows.values("pk"))
            )

        return intersected_rows

    def _build_tile_scope_predicates(
        self,
        clause_payload: Dict[str, Any],
        tiles_for_anchor_resource: QuerySet,
        tile_id_outer_ref: Any,
    ) -> Tuple[Optional[Q], Optional[Q]]:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        operand_items = clause_payload["operands"]

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)

        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug, node_alias=subject_node_alias
        )
        resource_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstanceid")
        )
        tile_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstance_id")
        )

        resource_has_any_tile_q = Q(Exists(tiles_for_anchor_resource))

        if not operand_items:
            presence_implies_match = self.facet_registry.presence_implies_match(
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
                Q(~Exists(tiles_missing_match)) & resource_has_any_tile_q
                if presence_implies_match
                else Q(~Exists(tiles_for_anchor_resource))
            )
            return (None, resource_level_q)

        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
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
            return (None, Q(~Exists(tiles_missing_match)) & resource_has_any_tile_q)

        positive_facet = self.facet_registry.resolve_positive_facet(
            operator_token, datatype_name
        )
        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name,
                positive_facet.operator,
                "value",
                self._literal_values_only(operand_items),
            )
            if isinstance(positive_expression, Q):
                positive_tile_matches = tile_rows.filter(positive_expression).filter(
                    tileid=tile_id_outer_ref
                )
            else:
                positive_tile_matches = tile_rows.filter(**positive_expression).filter(
                    tileid=tile_id_outer_ref
                )
        elif isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            positive_tile_matches = tile_rows.filter(~predicate_expression).filter(
                tileid=tile_id_outer_ref
            )
        elif isinstance(predicate_expression, Q):
            positive_tile_matches = tile_rows.exclude(predicate_expression).filter(
                tileid=tile_id_outer_ref
            )
        else:
            positive_tile_matches = tile_rows.exclude(**predicate_expression).filter(
                tileid=tile_id_outer_ref
            )

        tiles_with_violations = tiles_for_anchor_resource.filter(
            Exists(positive_tile_matches)
        )
        return (None, Q(~Exists(tiles_with_violations)) & resource_has_any_tile_q)

    def _literal_values_only(self, operands: List[Any]) -> List[Any]:
        literal_values: List[Any] = []
        for operand_item in operands:
            if isinstance(operand_item, dict):
                operand_type = operand_item["type"].upper()
                if operand_type == "PATH":
                    continue
                literal_values.append(operand_item["value"])
            else:
                literal_values.append(operand_item)
        return literal_values
