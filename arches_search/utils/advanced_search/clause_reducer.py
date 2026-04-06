from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet

from arches_search.utils.advanced_search.literal_clause_evaluator import (
    LiteralClauseEvaluator,
)
from arches_search.utils.advanced_search.related_clause_evaluator import (
    RelatedClauseEvaluator,
)
from arches_search.utils.advanced_search.tile_scope_evaluator import (
    TileScopeEvaluator,
)
from arches_search.utils.advanced_search.node_alias_datatype_registry import (
    NodeAliasDatatypeRegistry,
)
from arches_search.utils.advanced_search.relationship_utils import (
    has_relationship_path,
)
from arches_search.utils.advanced_search.constants import (
    CLAUSE_TYPE_LITERAL,
    CLAUSE_TYPE_RELATED,
    LOGIC_AND,
    LOGIC_OR,
    QUANTIFIER_ANY,
    QUANTIFIER_NONE,
    SUBJECT_TYPE_NODE,
)
from arches_search.utils.advanced_search.specs import ClauseReductionResult


class ClauseReducer:
    def __init__(
        self,
        literal_clause_evaluator: LiteralClauseEvaluator,
        related_clause_evaluator: RelatedClauseEvaluator,
        tile_scope_evaluator: TileScopeEvaluator,
        facet_registry,
        path_navigator,
        node_alias_datatype_registry: NodeAliasDatatypeRegistry,
    ) -> None:
        self.literal_clause_evaluator = literal_clause_evaluator
        self.related_clause_evaluator = related_clause_evaluator
        self.tile_scope_evaluator = tile_scope_evaluator
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.node_alias_datatype_registry = node_alias_datatype_registry

    def build_anchor_literal_q(
        self,
        group_payload: Dict[str, Any],
        logic: str,
    ) -> Tuple[Q, bool]:
        anchor_graph_slug = group_payload["graph_slug"]
        anchor_exists_expressions: List[Exists] = []

        for clause_payload in group_payload.get("clauses") or []:
            clause_type_token = clause_payload.get("type")
            if clause_type_token != CLAUSE_TYPE_LITERAL:
                continue

            subject = clause_payload.get("subject")
            if not subject:
                continue

            subject_graph_slug = subject.get("graph_slug", "")
            if subject_graph_slug != anchor_graph_slug:
                continue

            exists_expression = self.literal_clause_evaluator.build_anchor_exists(
                clause_payload
            )
            anchor_exists_expressions.append(exists_expression)

        if not anchor_exists_expressions:
            return Q(), False

        if logic == LOGIC_OR:
            combined_predicate: Optional[Q] = None
            for exists_expression in anchor_exists_expressions:
                exists_q = Q(exists_expression)
                combined_predicate = (
                    exists_q
                    if combined_predicate is None
                    else (combined_predicate | exists_q)
                )
            return combined_predicate or Q(), True

        combined_predicate = Q()
        for exists_expression in anchor_exists_expressions:
            combined_predicate &= Q(exists_expression)

        return combined_predicate, True

    def reduce(
        self,
        group_payload: Dict[str, Any],
        traversal_context: Dict[str, Any],
        child_rows: QuerySet,
        logic: str = LOGIC_AND,
    ) -> ClauseReductionResult:
        constrained_child_rows, had_inner_filters = self._reduce_child_side(
            group_payload, traversal_context, child_rows, logic
        )
        return ClauseReductionResult(
            relationshipless_q=None,
            constrained_child_rows=constrained_child_rows,
            had_inner_filters=had_inner_filters,
        )

    def _reduce_child_side(
        self,
        group_payload: Dict[str, Any],
        traversal_context: Dict[str, Any],
        child_rows: QuerySet,
        logic: str,
    ) -> Tuple[QuerySet, bool]:
        constrained_child_rows = child_rows
        had_inner_filters = False

        if logic == LOGIC_AND:
            constrained_child_rows, applied_and = self._apply_and_literals_to_children(
                constrained_child_rows=constrained_child_rows,
                traversal_context=traversal_context,
                group_payload=group_payload,
            )
            if applied_and:
                had_inner_filters = True
        else:
            or_exists_predicate = self._build_or_exists_from_literals(
                group_payload=group_payload,
                traversal_context=traversal_context,
            )
            if or_exists_predicate is not None:
                constrained_child_rows = child_rows.filter(or_exists_predicate)
                had_inner_filters = True

        nested_relationship_group = next(
            (
                candidate_group
                for candidate_group in group_payload["groups"]
                if has_relationship_path(candidate_group.get("relationship"))
            ),
            None,
        )
        if nested_relationship_group:
            constrained_child_rows, applied_nested = (
                self._apply_nested_single_hop_literals(
                    base_child_rows=constrained_child_rows,
                    traversal_context=traversal_context,
                    nested_group_payload=nested_relationship_group,
                )
            )
            if applied_nested:
                had_inner_filters = True

        constrained_child_rows, applied_related = (
            self._apply_related_clauses_to_children(
                child_rows=constrained_child_rows,
                traversal_context=traversal_context,
                group_payload=group_payload,
            )
        )
        if applied_related:
            had_inner_filters = True

        return constrained_child_rows, had_inner_filters

    def _apply_and_literals_to_children(
        self,
        constrained_child_rows: QuerySet,
        traversal_context: Dict[str, Any],
        group_payload: Dict[str, Any],
    ) -> Tuple[QuerySet, bool]:
        working_child_rows = constrained_child_rows
        applied_any_filter = False

        pending_group_payloads: List[Dict[str, Any]] = list(group_payload["groups"])
        while pending_group_payloads:
            current_group_payload = pending_group_payloads.pop()
            has_path = has_relationship_path(current_group_payload.get("relationship"))
            if not has_path:
                for clause_payload in current_group_payload["clauses"]:
                    if clause_payload["type"] != CLAUSE_TYPE_LITERAL:
                        continue
                    exists_expression = (
                        self.literal_clause_evaluator.build_child_exists(
                            clause_payload=clause_payload,
                            correlate_field=traversal_context["child_id_field"],
                        )
                    )
                    working_child_rows = working_child_rows.filter(exists_expression)
                    applied_any_filter = True
                pending_group_payloads.extend(current_group_payload["groups"])

        return working_child_rows, applied_any_filter

    def _build_or_exists_from_literals(
        self,
        group_payload: Dict[str, Any],
        traversal_context: Dict[str, Any],
    ) -> Optional[Q]:
        combined_or_exists: Optional[Q] = None
        pending_group_payloads: List[Dict[str, Any]] = list(group_payload["groups"])

        while pending_group_payloads:
            current_group_payload = pending_group_payloads.pop()
            has_path = has_relationship_path(current_group_payload.get("relationship"))
            if not has_path:
                ok_rowset = self.literal_clause_evaluator.compute_child_rows(
                    group_payload=current_group_payload,
                    correlate_field=traversal_context["child_id_field"],
                    terminal_graph_slug=traversal_context["terminal_graph_slug"],
                )
                if ok_rowset is not None:
                    exists_q = Q(Exists(ok_rowset))
                    combined_or_exists = (
                        exists_q
                        if combined_or_exists is None
                        else (combined_or_exists | exists_q)
                    )
                pending_group_payloads.extend(current_group_payload["groups"])

        return combined_or_exists

    def _apply_nested_single_hop_literals(
        self,
        base_child_rows: QuerySet,
        traversal_context: Dict[str, Any],
        nested_group_payload: Dict[str, Any],
    ) -> Tuple[QuerySet, bool]:
        nested_relationship = nested_group_payload.get("relationship") or {}
        if not has_relationship_path(nested_relationship):
            return base_child_rows, False

        parent_child_id_field_name = traversal_context["child_id_field"]
        nested_quantifier = nested_relationship.get(
            "traversal_quantifier", QUANTIFIER_ANY
        )

        *_, nested_child_rows, nested_child_id_field_name = (
            self.path_navigator.build_scoped_pairs_for_relationship_path(
                relationship_path=nested_relationship["path"],
                is_inverse_relationship=bool(nested_relationship["is_inverse"]),
                correlate_on_field=parent_child_id_field_name,
            )
        )

        nested_ok_rows = nested_child_rows

        pending_group_payloads: List[Dict[str, Any]] = list(
            nested_group_payload["groups"]
        )
        while pending_group_payloads:
            current_group_payload = pending_group_payloads.pop()
            has_path = has_relationship_path(current_group_payload.get("relationship"))
            if not has_path:
                for clause_payload in current_group_payload["clauses"]:
                    if clause_payload["type"] != CLAUSE_TYPE_LITERAL:
                        continue
                    exists_expression = (
                        self.literal_clause_evaluator.build_child_exists(
                            clause_payload=clause_payload,
                            correlate_field=nested_child_id_field_name,
                        )
                    )
                    nested_ok_rows = nested_ok_rows.filter(exists_expression)
                pending_group_payloads.extend(current_group_payload["groups"])

        if nested_quantifier == QUANTIFIER_ANY:
            return base_child_rows.filter(Exists(nested_ok_rows)), True

        if nested_quantifier == QUANTIFIER_NONE:
            return (
                base_child_rows.filter(
                    Exists(nested_child_rows) & ~Exists(nested_ok_rows)
                ),
                True,
            )

        same_child_ok = nested_ok_rows.filter(
            **{nested_child_id_field_name: OuterRef(nested_child_id_field_name)}
        )
        violating_rows = nested_child_rows.filter(~Exists(same_child_ok))
        return (
            base_child_rows.filter(Exists(nested_child_rows) & ~Exists(violating_rows)),
            True,
        )

    def _apply_related_clauses_to_children(
        self,
        child_rows: QuerySet,
        traversal_context: Dict[str, Any],
        group_payload: Dict[str, Any],
    ) -> Tuple[QuerySet, bool]:
        constrained_rows = child_rows
        applied_any_related = False
        terminal_graph_slug = traversal_context["terminal_graph_slug"]
        terminal_node_alias = traversal_context["terminal_node_alias"]

        for clause_payload in group_payload["clauses"]:
            if clause_payload["type"] != CLAUSE_TYPE_RELATED:
                continue

            subject = clause_payload["subject"]
            if subject.get("type") != SUBJECT_TYPE_NODE:
                raise ValueError("RELATED clauses require a node subject.")

            subject_graph_slug = subject["graph_slug"]
            subject_node_alias = subject["node_alias"]
            operator_token = clause_payload["operator"]
            has_operands = bool(clause_payload["operands"])

            targets_current_terminal = (
                subject_graph_slug == terminal_graph_slug
                and subject_node_alias == terminal_node_alias
            )

            if not has_operands and targets_current_terminal:
                datatype_name = (
                    self.node_alias_datatype_registry.get_datatype_for_alias(
                        subject_graph_slug, subject_node_alias
                    )
                )
                if self.facet_registry.presence_implies_match(
                    datatype_name, operator_token
                ):
                    continue

            presence_expression = self.related_clause_evaluator.evaluate_at_child(
                clause_payload=clause_payload,
                traversal_context=traversal_context,
            )
            constrained_rows = constrained_rows.filter(presence_expression)
            applied_any_related = True

        return constrained_rows, applied_any_related
