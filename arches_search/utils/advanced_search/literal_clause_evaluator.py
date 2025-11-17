from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet
from django.utils.translation import get_language


EVAL_MODE_ANCHOR = "anchor"
EVAL_MODE_CHILD = "child"
EVAL_MODE_TILE = "tile"
EVAL_MODE_COMPUTE_CHILD_ROWS = "compute_child_rows"

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"


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
        if mode == EVAL_MODE_ANCHOR:
            if clause_payload is None:
                raise ValueError("clause_payload is required for anchor mode")
            return self._build_anchor_exists(clause_payload)

        if mode == EVAL_MODE_CHILD:
            if clause_payload is None or correlate_field is None:
                raise ValueError(
                    "clause_payload and correlate_field are required for child mode"
                )
            return self._build_child_exists(
                clause_payload=clause_payload,
                correlate_field=correlate_field,
            )

        if mode == EVAL_MODE_TILE:
            if clause_payload is None or tiles_for_anchor_resource is None:
                raise ValueError(
                    "clause_payload and tiles_for_anchor_resource are required for "
                    "tile mode"
                )
            if tile_id_outer_ref is None:
                raise ValueError("tile_id_outer_ref is required for tile mode")
            return self._build_tile_scope_predicates(
                clause_payload=clause_payload,
                tiles_for_anchor_resource=tiles_for_anchor_resource,
                tile_id_outer_ref=tile_id_outer_ref,
            )

        if mode == EVAL_MODE_COMPUTE_CHILD_ROWS:
            if group_payload is None:
                raise ValueError(
                    "group_payload is required for compute_child_rows mode"
                )
            if correlate_field is None or terminal_graph_slug is None:
                raise ValueError(
                    "correlate_field and terminal_graph_slug are required for "
                    "compute_child_rows mode"
                )
            return self._compute_child_rows(
                group_payload=group_payload,
                correlate_field=correlate_field,
                terminal_graph_slug=terminal_graph_slug,
            )

        raise ValueError(f"Unsupported evaluation mode: {mode}")

    def _build_anchor_exists(self, clause_payload: Dict[str, Any]) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        operand_items = clause_payload["operands"]

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug,
                subject_node_alias,
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)

        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug,
            node_alias=subject_node_alias,
        )
        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstanceid")
        )

        if not operand_items:
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name,
                operator_token,
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

        normalized_operand_items = self._normalize_operands(
            datatype_name=datatype_name,
            operand_items=operand_items,
        )

        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=normalized_operand_items,
                anchor_resource_id_annotation=None,
            )
        )
        predicate_q = (
            predicate_expression
            if isinstance(predicate_expression, Q)
            else Q(**predicate_expression)
        )

        if quantifier_token == QUANTIFIER_ANY:
            return Exists(correlated_rows.filter(predicate_q))

        if quantifier_token == QUANTIFIER_NONE:
            return ~Exists(correlated_rows.filter(predicate_q))

        if quantifier_token == QUANTIFIER_ALL:
            if not is_template_negated:
                violating_rows = correlated_rows.exclude(predicate_q)
                return Exists(correlated_rows) & ~Exists(violating_rows)

            positive_per_row = self._positive_rows_for_negated_template(
                operator_token=operator_token,
                datatype_name=datatype_name,
                operand_items=normalized_operand_items,
                correlated_rows=correlated_rows,
                predicate_expression=predicate_q,
            )
            return Exists(correlated_rows) & ~Exists(positive_per_row)

        raise ValueError(f"Unsupported quantifier: {quantifier_token}")

    def _build_child_exists(
        self,
        clause_payload: Dict[str, Any],
        correlate_field: str,
    ) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"]
        operand_items = clause_payload["operands"]

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug,
                subject_node_alias,
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)

        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug,
            node_alias=subject_node_alias,
        )
        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef(correlate_field)
        )

        if not operand_items:
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name,
                operator_token,
            )
            return (
                Exists(correlated_rows)
                if presence_implies_match
                else ~Exists(correlated_rows)
            )

        normalized_operand_items = self._normalize_operands(
            datatype_name=datatype_name,
            operand_items=operand_items,
        )

        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=normalized_operand_items,
                anchor_resource_id_annotation=None,
            )
        )
        predicate_q = (
            predicate_expression
            if isinstance(predicate_expression, Q)
            else Q(**predicate_expression)
        )

        if not is_template_negated:
            return Exists(correlated_rows.filter(predicate_q))

        positive_rows = self._positive_rows_for_negated_template(
            operator_token=operator_token,
            datatype_name=datatype_name,
            operand_items=normalized_operand_items,
            correlated_rows=correlated_rows,
            predicate_expression=predicate_q,
        )
        return ~Exists(positive_rows)

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

            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug,
                    subject_node_alias,
                )
            )
            model_class = self.search_model_registry.get_model_for_datatype(
                datatype_name
            )

            base_rows = model_class.objects.filter(
                graph_slug=subject_graph_slug,
                node_alias=subject_node_alias,
            )
            correlated_rows = base_rows.filter(
                resourceinstanceid=OuterRef(correlate_field)
            )

            if not operand_items:
                presence_implies_match = self.facet_registry.presence_implies_match(
                    datatype_name,
                    operator_token,
                )
                predicate_rows = (
                    correlated_rows
                    if presence_implies_match
                    else correlated_rows.none()
                )
            else:
                normalized_operand_items = self._normalize_operands(
                    datatype_name=datatype_name,
                    operand_items=operand_items,
                )

                predicate_expression, is_template_negated = (
                    self.predicate_builder.build_predicate(
                        datatype_name=datatype_name,
                        operator_token=operator_token,
                        operands=normalized_operand_items,
                        anchor_resource_id_annotation=None,
                    )
                )
                predicate_q = (
                    predicate_expression
                    if isinstance(predicate_expression, Q)
                    else Q(**predicate_expression)
                )

                if not is_template_negated:
                    predicate_rows = correlated_rows.filter(predicate_q)
                else:
                    positive_rows = self._positive_rows_for_negated_template(
                        operator_token=operator_token,
                        datatype_name=datatype_name,
                        operand_items=normalized_operand_items,
                        correlated_rows=correlated_rows,
                        predicate_expression=predicate_q,
                    )
                    predicate_rows = correlated_rows.exclude(
                        pk__in=positive_rows.values("pk")
                    )

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
                subject_graph_slug,
                subject_node_alias,
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

        any_tile_for_resource_q = Q(Exists(tiles_for_anchor_resource))

        if not operand_items:
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name,
                operator_token,
            )

            if quantifier_token == QUANTIFIER_ANY:
                per_tile_presence = tile_rows.filter(tileid=tile_id_outer_ref)
                return (
                    (
                        Q(Exists(per_tile_presence))
                        if presence_implies_match
                        else ~Q(Exists(per_tile_presence))
                    ),
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

            tiles_missing_presence = tiles_for_anchor_resource.filter(
                ~Exists(tile_rows.filter(tileid=tile_id_outer_ref))
            )
            resource_level_q = (
                Q(~Exists(tiles_missing_presence)) & any_tile_for_resource_q
                if presence_implies_match
                else Q(~Exists(tiles_for_anchor_resource))
            )
            return None, resource_level_q

        normalized_operand_items = self._normalize_operands(
            datatype_name=datatype_name,
            operand_items=operand_items,
        )

        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=normalized_operand_items,
                anchor_resource_id_annotation=None,
            )
        )
        predicate_q = (
            predicate_expression
            if isinstance(predicate_expression, Q)
            else Q(**predicate_expression)
        )

        if quantifier_token == QUANTIFIER_ANY:
            per_tile_matches = tile_rows.filter(predicate_q).filter(
                tileid=tile_id_outer_ref
            )
            return Q(Exists(per_tile_matches)), None

        if quantifier_token == QUANTIFIER_NONE:
            resource_level_matches = resource_rows.filter(predicate_q)
            return None, Q(~Exists(resource_level_matches))

        if quantifier_token == QUANTIFIER_ALL:
            if not is_template_negated:
                per_tile_matches = tile_rows.filter(predicate_q).filter(
                    tileid=tile_id_outer_ref
                )
                tiles_missing_match = tiles_for_anchor_resource.filter(
                    ~Exists(per_tile_matches)
                )
                return (
                    None,
                    Q(~Exists(tiles_missing_match)) & any_tile_for_resource_q,
                )

            positive_per_tile_rows = self._positive_rows_for_negated_template(
                operator_token=operator_token,
                datatype_name=datatype_name,
                operand_items=normalized_operand_items,
                correlated_rows=tile_rows.filter(tileid=tile_id_outer_ref),
                predicate_expression=predicate_q,
            )
            tiles_with_violations = tiles_for_anchor_resource.filter(
                Exists(positive_per_tile_rows)
            )
            return (
                None,
                Q(~Exists(tiles_with_violations)) & any_tile_for_resource_q,
            )

        raise ValueError(f"Unsupported quantifier: {quantifier_token}")

    def _positive_rows_for_negated_template(
        self,
        operator_token: str,
        datatype_name: str,
        operand_items: List[Dict[str, Any]],
        correlated_rows: QuerySet,
        predicate_expression: Q | Dict[str, Any],
    ) -> QuerySet:
        positive_facet = self.facet_registry.resolve_positive_facet(
            operator_token,
            datatype_name,
        )

        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name,
                positive_facet.operator,
                "value",
                [operand_item["value"] for operand_item in operand_items],
            )
            positive_q = (
                positive_expression
                if isinstance(positive_expression, Q)
                else Q(**positive_expression)
            )
            return correlated_rows.filter(positive_q)

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression,
            "negated",
            False,
        ):
            return correlated_rows.filter(~predicate_expression)

        predicate_q = (
            predicate_expression
            if isinstance(predicate_expression, Q)
            else Q(**predicate_expression)
        )
        return correlated_rows.exclude(predicate_q)

    def _normalize_operands(
        self,
        datatype_name: str,
        operand_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if datatype_name.lower() != "string":
            return operand_items

        language_code = get_language()
        short_language_code = None

        if language_code:
            short_language_code = language_code.split("-")[0]

        normalized_items: List[Dict[str, Any]] = []

        for operand_item in operand_items:
            raw_value = operand_item.get("value")

            if isinstance(raw_value, dict) and raw_value:
                chosen_value = None

                if language_code and language_code in raw_value:
                    chosen_value = raw_value[language_code]
                elif short_language_code and short_language_code in raw_value:
                    chosen_value = raw_value[short_language_code]
                else:
                    chosen_value = next(iter(raw_value.values()))

                normalized_items.append({**operand_item, "value": chosen_value})
            else:
                normalized_items.append(operand_item)

        return normalized_items
