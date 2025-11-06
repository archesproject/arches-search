from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet

from arches_search.utils.advanced_search.clause_compiler import ClauseCompiler
from arches_search.utils.advanced_search.path_navigator import PathNavigator


LOGIC_AND = "AND"
LOGIC_OR = "OR"

SCOPE_RESOURCE = "RESOURCE"
SCOPE_TILE = "TILE"

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"

CONTEXT_ANCHOR = "ANCHOR"
CONTEXT_CHILD = "CHILD"


class GroupCompiler:
    def __init__(
        self, clause_compiler: ClauseCompiler, path_navigator: PathNavigator
    ) -> None:
        self.clause_compiler = clause_compiler
        self.path_navigator = path_navigator

    def compile(
        self,
        group_payload: Dict[str, Any],
        anchor_graph_slug: str,
        current_context_side: str = CONTEXT_ANCHOR,
        relationship_context_for_parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Q, List[Exists]]:
        relationship_context = group_payload.get("relationship")
        relationship_path_segments = (relationship_context or {}).get("path")
        has_relationship = bool(relationship_path_segments)

        if not has_relationship:
            relationshipless_q = self._compile_relationshipless_group_to_q(
                group_payload, anchor_graph_slug
            )
            if relationshipless_q is not None:
                return relationshipless_q, []

        exists_predicates: List[Exists] = []
        compiled_pair_info: Optional[Dict[str, Any]] = None
        pairs_scoped_to_anchor: Optional[QuerySet] = None

        if has_relationship:
            compiled_pair_info, pairs_scoped_to_anchor = (
                self.path_navigator.build_relationship_pairs(relationship_context)
            )
            child_identifier_field = compiled_pair_info["child_id_field"]
            base_pairs_excluding_self = pairs_scoped_to_anchor.exclude(
                **{child_identifier_field: OuterRef("resourceinstanceid")}
            )

            constrained_child_rows, inner_filters_present = (
                self._apply_group_constraints(
                    group_payload=group_payload,
                    compiled_pair_info=compiled_pair_info,
                    base_pairs=base_pairs_excluding_self,
                )
            )

            hop_info = self.path_navigator.normalize_relationship_context(
                relationship_context
            )
            hop_quantifier = hop_info["hop_quantifier"]
            is_inverse = hop_info["is_inverse"]
            inverse_single_hop = is_inverse and len(hop_info["path_segments"]) == 1

            if inverse_single_hop:
                has_related_clause = any(
                    c["type"].upper() == CLAUSE_TYPE_RELATED
                    for c in group_payload["clauses"]
                )
                if has_related_clause and hop_quantifier == QUANTIFIER_ALL:
                    hop_quantifier = QUANTIFIER_ANY

            if hop_quantifier == QUANTIFIER_ANY:
                exists_predicates.append(Exists(constrained_child_rows))
            elif hop_quantifier == QUANTIFIER_NONE:
                if inner_filters_present:
                    exists_predicates.append(
                        Exists(base_pairs_excluding_self)
                        & ~Exists(constrained_child_rows)
                    )
                else:
                    exists_predicates.append(~Exists(base_pairs_excluding_self))
            else:
                if inverse_single_hop:
                    child_satisfying_rows = (
                        self.clause_compiler.child_ok_rows_from_literals(
                            group_payload, compiled_pair_info
                        )
                    )
                else:
                    child_satisfying_rows = None

                if inverse_single_hop and child_satisfying_rows is not None:
                    violating_pairs = base_pairs_excluding_self.filter(
                        ~Exists(child_satisfying_rows)
                    )
                    exists_predicates.append(
                        Exists(base_pairs_excluding_self) & ~Exists(violating_pairs)
                    )
                else:
                    same_child_ok = constrained_child_rows.filter(
                        **{child_identifier_field: OuterRef(child_identifier_field)}
                    )
                    violating_pairs = base_pairs_excluding_self.filter(
                        ~Exists(same_child_ok)
                    )
                    exists_predicates.append(
                        Exists(base_pairs_excluding_self) & ~Exists(violating_pairs)
                    )

        correlate_to_tile = group_payload["scope"].upper() == SCOPE_TILE

        for clause_payload in group_payload["clauses"]:
            if clause_payload["type"].upper() == CLAUSE_TYPE_RELATED:
                continue
            exists_predicates.append(
                self.clause_compiler.compile(
                    clause_payload,
                    anchor_graph_slug,
                    correlate_to_tile=correlate_to_tile,
                )
            )

        child_q, child_exists_predicates = self._compile_children(
            subgroups=group_payload["groups"],
            anchor_graph_slug=anchor_graph_slug,
            parent_has_relationship=has_relationship,
            current_context_side=(
                CONTEXT_CHILD if has_relationship else current_context_side
            ),
            relationship_context_for_parent=(
                compiled_pair_info
                if has_relationship
                else relationship_context_for_parent
            ),
        )

        group_logic = group_payload["logic"].upper()
        all_exists_predicates: List[Exists] = [
            *exists_predicates,
            *child_exists_predicates,
        ]

        if group_logic == LOGIC_OR:
            q_expression = child_q if child_q is not None else Q()
            for predicate in all_exists_predicates:
                q_expression = q_expression | Q(predicate)
            return q_expression, []

        q_expression = child_q if child_q is not None else Q()
        return q_expression, all_exists_predicates

    def _compile_children(
        self,
        subgroups: List[Dict[str, Any]],
        anchor_graph_slug: str,
        parent_has_relationship: bool,
        current_context_side: str,
        relationship_context_for_parent: Optional[Dict[str, Any]],
    ) -> Tuple[Q, List[Exists]]:
        combined_q = Q()
        exists_predicates: List[Exists] = []

        for subgroup_payload in subgroups:
            subgroup_has_relationship = bool(
                ((subgroup_payload.get("relationship")) or {}).get("path")
            )
            if parent_has_relationship and subgroup_has_relationship:
                continue

            subgroup_q, subgroup_exists = self.compile(
                group_payload=subgroup_payload,
                anchor_graph_slug=anchor_graph_slug,
                current_context_side=(
                    CONTEXT_CHILD
                    if parent_has_relationship and not subgroup_has_relationship
                    else current_context_side
                ),
                relationship_context_for_parent=relationship_context_for_parent,
            )

            if (
                parent_has_relationship
                and not subgroup_has_relationship
                and current_context_side == CONTEXT_CHILD
            ):
                continue

            combined_q &= subgroup_q
            exists_predicates.extend(subgroup_exists)

        return combined_q, exists_predicates

    def _compile_relationshipless_group_to_q(
        self, group_payload: Dict[str, Any], anchor_graph_slug: str
    ) -> Optional[Q]:
        if ((group_payload.get("relationship")) or {}).get("path"):
            return None

        logic = group_payload["logic"].upper()
        scope = group_payload["scope"].upper()

        if scope == SCOPE_TILE:
            return self.clause_compiler.compile_relationshipless_tile_group_to_q(
                group_payload=group_payload,
                anchor_graph_slug=anchor_graph_slug,
                logic=logic,
            )

        has_any_piece = False
        combined_q = Q()

        for clause_payload in group_payload["clauses"]:
            clause_q = self.clause_compiler.compile_literal_to_q(
                clause_payload=clause_payload,
                anchor_graph_slug=anchor_graph_slug,
                scope=SCOPE_RESOURCE,
            )
            combined_q = (
                clause_q
                if not has_any_piece
                else (
                    combined_q & clause_q
                    if logic == LOGIC_AND
                    else combined_q | clause_q
                )
            )
            has_any_piece = True

        for child_group_payload in group_payload["groups"]:
            child_q = self._compile_relationshipless_group_to_q(
                child_group_payload, anchor_graph_slug
            )
            if child_q is None:
                return None
            combined_q = (
                child_q
                if not has_any_piece
                else (
                    combined_q & child_q if logic == LOGIC_AND else combined_q | child_q
                )
            )
            has_any_piece = True

        if not has_any_piece:
            return Q() if logic == LOGIC_AND else Q(pk__in=[])
        return combined_q

    def _apply_group_constraints(
        self,
        group_payload: Dict[str, Any],
        compiled_pair_info: Dict[str, Any],
        base_pairs: QuerySet,
    ) -> Tuple[QuerySet, bool]:
        child_match_rows = base_pairs
        inner_filters_present = False
        child_identifier_field = compiled_pair_info["child_id_field"]

        for child_group_payload in group_payload["groups"]:
            if ((child_group_payload.get("relationship")) or {}).get("path"):
                continue
            if child_group_payload["logic"].upper() != LOGIC_AND:
                continue

            child_group_graph_slug = child_group_payload["graph_slug"].strip()
            pending_nodes: List[Dict[str, Any]] = [child_group_payload]

            while pending_nodes:
                node_payload = pending_nodes.pop()
                if ((node_payload.get("relationship")) or {}).get("path"):
                    continue

                for clause_payload in node_payload["clauses"]:
                    if clause_payload["type"].upper() != CLAUSE_TYPE_LITERAL:
                        continue

                    subject_graph_slug, _subject_alias = clause_payload["subject"][0]
                    if (
                        child_group_graph_slug
                        and subject_graph_slug
                        and subject_graph_slug != child_group_graph_slug
                    ):
                        continue

                    child_match_rows, applied_here = (
                        self.clause_compiler.filter_pairs_by_clause(
                            pairs_queryset=child_match_rows,
                            clause_payload=clause_payload,
                            correlate_field=child_identifier_field,
                        )
                    )
                    inner_filters_present = inner_filters_present or applied_here

                for nested_group_payload in node_payload["groups"]:
                    pending_nodes.append(nested_group_payload)

        nested_group_payload = next(
            (
                nested
                for nested in group_payload["groups"]
                if ((nested.get("relationship")) or {}).get("path")
            ),
            None,
        )
        if nested_group_payload:
            nested_relationship = nested_group_payload.get("relationship") or {}
            nested_path = nested_relationship.get("path") or []

            if len(nested_path) == 1:
                nested_quantifier = (
                    nested_relationship.get("traversal_quantifiers") or [QUANTIFIER_ANY]
                )[0].upper()
                _, nested_terminal_graph, nested_pairs, nested_child_field = (
                    self.path_navigator.build_scoped_pairs_for_path(
                        path_segments=nested_path,
                        is_inverse_relationship=bool(
                            nested_relationship.get("is_inverse")
                        ),
                        correlate_on_field=child_identifier_field,
                    )
                )

                literal_clauses_all: List[Dict[str, Any]] = []
                stack: List[Dict[str, Any]] = [nested_group_payload]
                while stack:
                    node_payload = stack.pop()
                    if not ((node_payload.get("relationship")) or {}).get("path"):
                        for clause_payload in node_payload["clauses"]:
                            if clause_payload["type"].upper() == CLAUSE_TYPE_LITERAL:
                                literal_clauses_all.append(clause_payload)
                    for deeper_group_payload in node_payload["groups"]:
                        stack.append(deeper_group_payload)

                nested_literal_clauses = [
                    cp
                    for cp in literal_clauses_all
                    if cp["subject"][0][0] == nested_terminal_graph
                ]
                if not nested_literal_clauses:
                    filtered_literals: List[Dict[str, Any]] = []
                    for cp in literal_clauses_all:
                        subject_graph_slug, subject_alias = cp["subject"][0]
                        rows_model = self.clause_compiler.fetch_subject_rows(
                            subject_graph_slug, subject_alias
                        )
                        if rows_model is not None:
                            filtered_literals.append(cp)
                    nested_literal_clauses = filtered_literals

                nested_ok_pairs = nested_pairs
                for cp in nested_literal_clauses:
                    nested_ok_pairs, applied_here = (
                        self.clause_compiler.filter_pairs_by_clause(
                            pairs_queryset=nested_ok_pairs,
                            clause_payload=cp,
                            correlate_field=nested_child_field,
                        )
                    )
                    inner_filters_present = inner_filters_present or applied_here

                if nested_quantifier == QUANTIFIER_ANY:
                    child_match_rows = child_match_rows.filter(Exists(nested_ok_pairs))
                    inner_filters_present = True
                elif nested_quantifier == QUANTIFIER_NONE:
                    child_match_rows = child_match_rows.filter(
                        Exists(nested_pairs) & ~Exists(nested_ok_pairs)
                    )
                    inner_filters_present = True
                else:
                    same_child_ok = nested_ok_pairs.filter(
                        **{nested_child_field: OuterRef(nested_child_field)}
                    )
                    violator_pairs = nested_pairs.filter(~Exists(same_child_ok))
                    child_match_rows = child_match_rows.filter(
                        Exists(nested_pairs) & ~Exists(violator_pairs)
                    )
                    inner_filters_present = True

        terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]
        terminal_node_alias = compiled_pair_info["terminal_node_alias"]

        for related_clause_payload in group_payload["clauses"]:
            if related_clause_payload["type"].upper() != CLAUSE_TYPE_RELATED:
                continue

            subject_graph_slug, subject_alias = related_clause_payload["subject"][0]
            operator_upper = related_clause_payload["operator"].upper()
            has_operands = bool(related_clause_payload["operands"])

            if (
                subject_graph_slug == terminal_graph_slug
                and subject_alias == terminal_node_alias
                and operator_upper == "HAS_ANY_VALUE"
                and not has_operands
            ):
                continue

            related_exists_queryset = self.clause_compiler.related_child_exists_qs(
                related_clause_payload, compiled_pair_info
            )
            if related_exists_queryset is None:
                continue

            if not has_operands:
                datatype_name = self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_alias
                )
                predicate_info = self.clause_compiler.facet_registry.predicate(
                    datatype_name,
                    related_clause_payload["operator"],
                    "value",
                    [True],
                )
                is_negated_template = predicate_info[1]
                if operator_upper == "HAS_NO_VALUE":
                    child_match_rows = child_match_rows.filter(
                        ~Exists(related_exists_queryset)
                    )
                elif operator_upper == "HAS_ANY_VALUE":
                    child_match_rows = child_match_rows.filter(
                        Exists(related_exists_queryset)
                    )
                else:
                    child_match_rows = child_match_rows.filter(
                        ~Exists(related_exists_queryset)
                        if is_negated_template
                        else Exists(related_exists_queryset)
                    )
            else:
                child_match_rows = child_match_rows.filter(
                    Exists(related_exists_queryset)
                )

        return child_match_rows, inner_filters_present
