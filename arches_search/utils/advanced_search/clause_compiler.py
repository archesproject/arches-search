from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet
from arches.app.models import models as arches_models


QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"


class ClauseCompiler:
    def __init__(
        self, subject_query_factory, facet_registry, operand_compiler, path_navigator
    ) -> None:
        self.subject_query_factory = subject_query_factory
        self.facet_registry = facet_registry
        self.operand_compiler = operand_compiler
        self.path_navigator = path_navigator
        self.node_alias_datatype_registry = (
            subject_query_factory.node_alias_datatype_registry
        )

    # ========= Anchor-only single clause =========

    def compile(self, clause_payload: Dict[str, Any]) -> Exists:
        clause_type = (clause_payload.get("type") or "").upper()
        if clause_type == CLAUSE_TYPE_LITERAL:
            return self._compile_literal_clause_anchor(clause_payload)
        if clause_type == CLAUSE_TYPE_RELATED:
            return self._compile_related_presence_anchor(clause_payload)
        return Exists(arches_models.ResourceInstance.objects.none())

    def _compile_literal_clause_anchor(self, clause_payload: Dict[str, Any]) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload.get("operator") or "").upper()
        quantifier_token = (clause_payload.get("quantifier") or "").upper()
        operand_items = clause_payload.get("operands")

        datatype_name = self.node_alias_datatype_registry.get_datatype_for_alias(
            subject_graph_slug, subject_node_alias
        )
        base_subject_rows = self.subject_query_factory.subject_rows(
            datatype_name, subject_graph_slug, subject_node_alias
        )
        correlated_rows = self.subject_query_factory.correlate_to_anchor(
            base_subject_rows
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

        positive_expression, has_positive = (
            self.subject_query_factory.positive_expression(
                datatype_name,
                operator_token,
                self.operand_compiler.literal_values_only(operand_items),
            )
        )
        if has_positive:
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

    def _compile_related_presence_anchor(
        self, clause_payload: Dict[str, Any]
    ) -> Exists:
        operator_token = (clause_payload["operator"] or "").upper()
        quantifier_token = (clause_payload["quantifier"] or "").upper()
        subject_path_sequence = clause_payload["subject"]

        traversal_context, leg_queryset_scoped_to_anchor = (
            self.path_navigator.build_relationship_pairs(
                {"path": subject_path_sequence, "is_inverse": False}
            )
        )

        # RELATED presence is about the edge, not terminal value facets.
        # Interpret operators purely as leg existence tests.
        if operator_token == "HAS_ANY_VALUE":
            if quantifier_token in ("ANY", "ALL"):
                return Exists(leg_queryset_scoped_to_anchor)
            if quantifier_token == "NONE":
                return ~Exists(leg_queryset_scoped_to_anchor)
        elif operator_token == "HAS_NO_VALUE":
            if quantifier_token in ("ANY", "ALL"):
                return ~Exists(leg_queryset_scoped_to_anchor)
            if quantifier_token == "NONE":
                return Exists(leg_queryset_scoped_to_anchor)

        # Fallback: conservative empty (should not be reached with supported operators)
        return Exists(arches_models.ResourceInstance.objects.none())

    # ========= Correlated helpers for GroupCompiler (clause-agnostic orchestration) =========

    def apply_clause_to_correlated_queryset(
        self,
        correlated_queryset: QuerySet,
        clause_payload: Dict[str, Any],
        *,
        correlate_field: str,
        anchor_resource_id_annotation: Optional[str] = None,
    ) -> Tuple[QuerySet, bool]:
        clause_type = (clause_payload.get("type") or "").upper()
        if clause_type == CLAUSE_TYPE_LITERAL:
            return self._apply_literal_clause_to_correlated_queryset(
                correlated_queryset,
                clause_payload,
                correlate_field=correlate_field,
            )
        if clause_type == CLAUSE_TYPE_RELATED:
            return self._apply_related_clause_to_correlated_queryset(
                correlated_queryset,
                clause_payload,
                correlate_field=correlate_field,
                anchor_resource_id_annotation=anchor_resource_id_annotation,
            )
        return correlated_queryset, False

    def filter_correlated_by_group_literals(
        self,
        correlated_queryset: QuerySet,
        *,
        group_payload: Dict[str, Any],
        correlate_field: str,
    ) -> Tuple[QuerySet, bool]:
        """
        AND-fold all literal constraints from non-relationship child groups into the correlated queryset.
        """
        working = correlated_queryset
        applied_any = False

        stack = [
            g
            for g in (group_payload.get("groups") or [])
            if not ((g.get("relationship") or {}).get("path"))
        ]
        while stack:
            node_payload = stack.pop()
            for clause_payload in node_payload.get("clauses") or []:
                if (clause_payload.get("type") or "").upper() != CLAUSE_TYPE_LITERAL:
                    continue
                working, applied_here = (
                    self._apply_literal_clause_to_correlated_queryset(
                        working, clause_payload, correlate_field=correlate_field
                    )
                )
                applied_any = applied_any or applied_here
            stack.extend(node_payload.get("groups") or [])
        return working, applied_any

    def build_or_q_for_group(
        self,
        group_payload: Dict[str, Any],
        *,
        traversal_context: Dict[str, Any],
    ) -> Tuple[Optional[Q], bool]:
        or_q = Q(pk__in=[])
        saw_any = False

        ok_rows = self.ok_rows_from_literals_in_group(
            group_payload, traversal_context=traversal_context
        )
        if ok_rows is not None:
            or_q |= Q(Exists(ok_rows))
            saw_any = True

        return (or_q if saw_any else None), saw_any

    def ok_rows_from_literals_in_group(
        self,
        group_payload: Dict[str, Any],
        *,
        traversal_context: Dict[str, Any],
    ) -> Optional[QuerySet]:
        terminal_graph_slug = traversal_context["terminal_graph_slug"]
        related_resource_id_field = self._get_related_resource_id_field(
            traversal_context
        )

        literal_clauses: List[Dict[str, Any]] = []
        stack_for_collection: List[Dict[str, Any]] = list(
            group_payload.get("groups") or []
        )
        while stack_for_collection:
            node_payload = stack_for_collection.pop()
            if (node_payload.get("relationship") or {}).get("path"):
                continue
            if (node_payload.get("logic") or "AND").upper() != "AND":
                return None
            for clause_payload in node_payload.get("clauses") or []:
                if (clause_payload.get("type") or "").upper() == CLAUSE_TYPE_LITERAL:
                    subject_graph_slug, _ = clause_payload["subject"][0]
                    if subject_graph_slug != terminal_graph_slug:
                        return None
                    literal_clauses.append(clause_payload)
            stack_for_collection.extend(node_payload.get("groups") or [])

        if not literal_clauses:
            return None

        accumulated_rows = None
        for clause_payload in literal_clauses:
            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = (clause_payload.get("operator") or "").upper()
            operand_items = clause_payload.get("operands") or []

            datatype_name = self.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
            base_subject_rows = self.subject_query_factory.subject_rows(
                datatype_name, subject_graph_slug, subject_node_alias
            )
            correlated_rows = self.subject_query_factory.correlate(
                base_subject_rows, related_resource_id_field
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
                    positive_expression, has_positive = (
                        self.subject_query_factory.positive_expression(
                            datatype_name,
                            operator_token,
                            self.operand_compiler.literal_values_only(operand_items),
                        )
                    )
                    if has_positive:
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

    def constrain_nested_single_hop_literals(
        self,
        *,
        base_queryset_for_leg: QuerySet,
        traversal_context: Dict[str, Any],
        nested_group_payload: Dict[str, Any],
    ) -> Tuple[QuerySet, bool]:
        nested_relationship = nested_group_payload.get("relationship") or {}
        nested_path = nested_relationship.get("path") or []
        if len(nested_path) != 1:
            return base_queryset_for_leg, False

        parent_related_id_field = self._get_related_resource_id_field(traversal_context)
        nested_quantifier = (
            (nested_relationship.get("traversal_quantifiers") or [QUANTIFIER_ANY])[0]
        ).upper()

        (
            _anchor_graph_slug_ignored,
            _nested_terminal_graph_slug,
            nested_leg_queryset,
            nested_related_id_field,
        ) = self.path_navigator.build_scoped_pairs_for_path(
            path_segments=nested_path,
            is_inverse_relationship=bool(nested_relationship.get("is_inverse")),
            correlate_on_field=parent_related_id_field,
        )

        ok_nested = nested_leg_queryset
        had_any_inner_filters = False

        stack_for_collection: List[Dict[str, Any]] = [nested_group_payload]
        while stack_for_collection:
            node_payload = stack_for_collection.pop()
            if (node_payload.get("relationship") or {}).get("path"):
                continue
            for clause_payload in node_payload.get("clauses") or []:
                ok_nested, applied_here = (
                    self._apply_literal_clause_to_correlated_queryset(
                        ok_nested,
                        clause_payload,
                        correlate_field=nested_related_id_field,
                    )
                )
                had_any_inner_filters = had_any_inner_filters or applied_here
            stack_for_collection.extend(node_payload.get("groups") or [])

        if nested_quantifier == QUANTIFIER_ANY:
            return base_queryset_for_leg.filter(Exists(ok_nested)), True

        if nested_quantifier == QUANTIFIER_NONE:
            return (
                base_queryset_for_leg.filter(
                    Exists(nested_leg_queryset) & ~Exists(ok_nested)
                ),
                True,
            )

        same_ok = ok_nested.filter(
            **{nested_related_id_field: OuterRef(nested_related_id_field)}
        )
        violating_nested = nested_leg_queryset.filter(~Exists(same_ok))
        return (
            base_queryset_for_leg.filter(
                Exists(nested_leg_queryset) & ~Exists(violating_nested)
            ),
            True or had_any_inner_filters,
        )

    # ===== internals for correlated contexts =====

    def _apply_literal_clause_to_correlated_queryset(
        self,
        correlated_queryset: QuerySet,
        clause_payload: Dict[str, Any],
        *,
        correlate_field: str,
    ) -> Tuple[QuerySet, bool]:
        if (clause_payload.get("type") or "").upper() != CLAUSE_TYPE_LITERAL:
            return correlated_queryset, False

        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload.get("operator") or "").upper()
        operand_items = clause_payload.get("operands") or []

        datatype_name = self.node_alias_datatype_registry.get_datatype_for_alias(
            subject_graph_slug, subject_node_alias
        )
        base_subject_rows = self.subject_query_factory.subject_rows(
            datatype_name, subject_graph_slug, subject_node_alias
        )
        correlated_rows = self.subject_query_factory.correlate(
            base_subject_rows, correlate_field
        )

        if not operand_items:
            presence_implies_match = self.facet_registry.zero_arity_presence_is_match(
                datatype_name, operator_token
            )
            return (
                (correlated_queryset.filter(Exists(correlated_rows)), True)
                if presence_implies_match
                else (correlated_queryset.filter(~Exists(correlated_rows)), True)
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
                return (
                    correlated_queryset.filter(
                        Exists(correlated_rows.filter(predicate_expression))
                    ),
                    True,
                )
            return (
                correlated_queryset.filter(
                    Exists(correlated_rows.filter(**predicate_expression))
                ),
                True,
            )

        positive_expression, has_positive = (
            self.subject_query_factory.positive_expression(
                datatype_name,
                operator_token,
                self.operand_compiler.literal_values_only(operand_items),
            )
        )
        if has_positive:
            if isinstance(positive_expression, Q):
                return (
                    correlated_queryset.filter(
                        ~Exists(correlated_rows.filter(positive_expression))
                    ),
                    True,
                )
            return (
                correlated_queryset.filter(
                    ~Exists(correlated_rows.filter(**positive_expression))
                ),
                True,
            )

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            return (
                correlated_queryset.filter(
                    ~Exists(correlated_rows.filter(~predicate_expression))
                ),
                True,
            )

        if isinstance(predicate_expression, Q):
            return (
                correlated_queryset.filter(
                    ~Exists(correlated_rows.filter(predicate_expression))
                ),
                True,
            )
        return (
            correlated_queryset.filter(
                ~Exists(correlated_rows.filter(**predicate_expression))
            ),
            True,
        )

    def _apply_related_clause_to_correlated_queryset(
        self,
        correlated_queryset: QuerySet,
        clause_payload: Dict[str, Any],
        *,
        correlate_field: str,
        anchor_resource_id_annotation: Optional[str],
    ) -> Tuple[QuerySet, bool]:
        if (clause_payload.get("type") or "").upper() != CLAUSE_TYPE_RELATED:
            return correlated_queryset, False

        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload.get("operator") or "").upper()
        operand_items = clause_payload.get("operands") or []

        # When operands are present, RELATED behaves like a child-value filter.
        # When no operands, RELATED is pure edge presence on the child side.
        datatype_name = self.node_alias_datatype_registry.get_datatype_for_alias(
            subject_graph_slug, subject_node_alias
        )
        base_subject_rows = self.subject_query_factory.subject_rows(
            datatype_name, subject_graph_slug, subject_node_alias
        )
        correlated_subject_rows = self.subject_query_factory.correlate(
            base_subject_rows, correlate_field
        )
        if anchor_resource_id_annotation:
            correlated_subject_rows = correlated_subject_rows.annotate(
                _anchor_resource_id=OuterRef(anchor_resource_id_annotation)
            )

        if not operand_items:
            # PURE PRESENCE/ABSENCE on the child side (edge existence),
            # independent of datatype facets.
            if operator_token == "HAS_ANY_VALUE":
                return correlated_queryset.filter(Exists(correlated_subject_rows)), True
            if operator_token == "HAS_NO_VALUE":
                return (
                    correlated_queryset.filter(~Exists(correlated_subject_rows)),
                    True,
                )
            # Unknown operator with zero operands: do nothing, be permissive.
            return correlated_queryset, False

        # With operands: apply as a child-value predicate (same as before)
        predicate_expression, _ = self.operand_compiler.build_predicate(
            datatype_name=datatype_name,
            operator_token=operator_token,
            operands=operand_items,
            anchor_resource_id_annotation=(
                "_anchor_resource_id" if anchor_resource_id_annotation else None
            ),
        )

        if isinstance(predicate_expression, Q):
            return (
                correlated_queryset.filter(
                    Exists(correlated_subject_rows.filter(predicate_expression))
                ),
                True,
            )
        return (
            correlated_queryset.filter(
                Exists(correlated_subject_rows.filter(**predicate_expression))
            ),
            True,
        )

    def _get_related_resource_id_field(self, traversal_context: Dict[str, Any]) -> str:
        return traversal_context.get(
            "related_resource_id_field"
        ) or traversal_context.get("child_id_field")
