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
        current_context_side: str = CONTEXT_ANCHOR,
        relationship_context_for_parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Q, List[Exists]]:
        relationship_block = group_payload.get("relationship")
        path_segments = (relationship_block or {}).get("path")
        has_relationship = bool(path_segments)

        if not has_relationship:
            relationshipless_q = self._compile_relationshipless_group_to_q(
                group_payload
            )
            if relationshipless_q is not None:
                return relationshipless_q, []

        existence_predicates: List[Exists] = []
        relationship_pairs_info: Optional[Dict[str, Any]] = None
        pairs_scoped_to_anchor_resource: Optional[QuerySet] = None

        if has_relationship:
            relationship_pairs_info, pairs_scoped_to_anchor_resource = (
                self.path_navigator.build_relationship_pairs(relationship_block)
            )
            child_id_field_name = relationship_pairs_info["child_id_field"]

            pairs_excluding_self = pairs_scoped_to_anchor_resource.exclude(
                **{child_id_field_name: OuterRef("resourceinstanceid")}
            )

            qualifying_child_pairs, had_inner_filters = self._apply_group_constraints(
                group_payload=group_payload,
                compiled_pair_info=relationship_pairs_info,
                base_pairs=pairs_excluding_self,
            )

            normalized_relationship = (
                self.path_navigator.normalize_relationship_context(relationship_block)
            )
            traversal_quantifier = normalized_relationship["hop_quantifier"]
            is_inverse_relationship = normalized_relationship["is_inverse"]
            is_single_inverse_hop = (
                is_inverse_relationship
                and len(normalized_relationship["path_segments"]) == 1
            )

            if is_single_inverse_hop:
                has_related_clause = any(
                    clause_item.get("type", "").upper() == CLAUSE_TYPE_RELATED
                    for clause_item in group_payload.get("clauses") or []
                )
                if has_related_clause and traversal_quantifier == QUANTIFIER_ALL:
                    traversal_quantifier = QUANTIFIER_ANY

            if traversal_quantifier == QUANTIFIER_ANY:
                existence_predicates.append(Exists(qualifying_child_pairs))
            elif traversal_quantifier == QUANTIFIER_NONE:
                if had_inner_filters:
                    existence_predicates.append(
                        Exists(pairs_excluding_self) & ~Exists(qualifying_child_pairs)
                    )
                else:
                    existence_predicates.append(~Exists(pairs_excluding_self))
            else:
                if is_single_inverse_hop:
                    literal_ok_rows = self.clause_compiler.child_ok_rows_from_literals(
                        group_payload, relationship_pairs_info
                    )
                else:
                    literal_ok_rows = None

                if is_single_inverse_hop and literal_ok_rows is not None:
                    violating_pairs = pairs_excluding_self.filter(
                        ~Exists(literal_ok_rows)
                    )
                    existence_predicates.append(
                        Exists(pairs_excluding_self) & ~Exists(violating_pairs)
                    )
                else:
                    same_child_ok = qualifying_child_pairs.filter(
                        **{child_id_field_name: OuterRef(child_id_field_name)}
                    )
                    violating_pairs = pairs_excluding_self.filter(
                        ~Exists(same_child_ok)
                    )
                    existence_predicates.append(
                        Exists(pairs_excluding_self) & ~Exists(violating_pairs)
                    )

        correlate_to_tile_scope = (
            group_payload.get("scope") or ""
        ).upper() == SCOPE_TILE

        for clause_payload in group_payload.get("clauses") or []:
            if (clause_payload.get("type") or "").upper() == CLAUSE_TYPE_RELATED:
                continue
            existence_predicates.append(
                self.clause_compiler.compile(
                    clause_payload,
                    correlate_to_tile=correlate_to_tile_scope,
                )
            )

        children_q, children_existence_predicates = self._compile_children(
            subgroups=group_payload.get("groups") or [],
            parent_has_relationship=has_relationship,
            current_context_side=(
                CONTEXT_CHILD if has_relationship else current_context_side
            ),
            relationship_context_for_parent=(
                relationship_pairs_info
                if has_relationship
                else relationship_context_for_parent
            ),
        )

        group_logic = (group_payload.get("logic") or LOGIC_AND).upper()
        all_existence_predicates: List[Exists] = [
            *existence_predicates,
            *children_existence_predicates,
        ]

        if group_logic == LOGIC_OR:
            combined_q = children_q if children_q is not None else Q()
            for exists_expr in all_existence_predicates:
                combined_q = combined_q | Q(exists_expr)
            return combined_q, []

        combined_q = children_q if children_q is not None else Q()
        return combined_q, all_existence_predicates

    def _compile_children(
        self,
        subgroups: List[Dict[str, Any]],
        parent_has_relationship: bool,
        current_context_side: str,
        relationship_context_for_parent: Optional[Dict[str, Any]],
    ) -> Tuple[Q, List[Exists]]:
        combined_children_q = Q()
        accumulated_existence_predicates: List[Exists] = []

        for subgroup_payload in subgroups:
            subgroup_has_relationship = bool(
                ((subgroup_payload.get("relationship")) or {}).get("path")
            )
            if parent_has_relationship and subgroup_has_relationship:
                continue

            subgroup_q, subgroup_existence_predicates = self.compile(
                group_payload=subgroup_payload,
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

            combined_children_q &= subgroup_q
            accumulated_existence_predicates.extend(subgroup_existence_predicates)

        return combined_children_q, accumulated_existence_predicates

    def _compile_relationshipless_group_to_q(
        self, group_payload: Dict[str, Any]
    ) -> Optional[Q]:
        if ((group_payload.get("relationship")) or {}).get("path"):
            return None

        logic_token = (group_payload.get("logic") or LOGIC_AND).upper()
        scope_token = (group_payload.get("scope") or SCOPE_RESOURCE).upper()

        if scope_token == SCOPE_TILE:
            return self.clause_compiler.compile_relationshipless_tile_group_to_q(
                group_payload=group_payload,
                use_and_logic=(logic_token == LOGIC_AND),
            )

        has_any_piece = False
        combined_q = Q()

        for clause_payload in group_payload.get("clauses") or []:
            clause_q = self.clause_compiler.compile_literal_to_q(
                clause_payload=clause_payload,
                scope=SCOPE_RESOURCE,
            )
            combined_q = (
                clause_q
                if not has_any_piece
                else (
                    combined_q & clause_q
                    if logic_token == LOGIC_AND
                    else combined_q | clause_q
                )
            )
            has_any_piece = True

        for child_group_payload in group_payload.get("groups") or []:
            child_q = self._compile_relationshipless_group_to_q(child_group_payload)
            if child_q is None:
                return None
            combined_q = (
                child_q
                if not has_any_piece
                else (
                    combined_q & child_q
                    if logic_token == LOGIC_AND
                    else combined_q | child_q
                )
            )
            has_any_piece = True

        if not has_any_piece:
            return Q() if logic_token == LOGIC_AND else Q(pk__in=[])
        return combined_q

    def _apply_group_constraints(
        self,
        group_payload: Dict[str, Any],
        compiled_pair_info: Dict[str, Any],
        base_pairs: QuerySet,
    ) -> Tuple[QuerySet, bool]:
        constrained_child_pairs = base_pairs
        had_any_inner_filters = False
        child_id_field_name = compiled_pair_info["child_id_field"]

        for child_group_payload in group_payload.get("groups") or []:
            if ((child_group_payload.get("relationship")) or {}).get("path"):
                continue
            if (child_group_payload.get("logic") or LOGIC_AND).upper() != LOGIC_AND:
                continue

            enforced_graph_slug = (child_group_payload.get("graph_slug") or "").strip()
            pending_nodes: List[Dict[str, Any]] = [child_group_payload]

            while pending_nodes:
                node_payload = pending_nodes.pop()
                if ((node_payload.get("relationship")) or {}).get("path"):
                    continue

                for clause_payload in node_payload.get("clauses") or []:
                    if (
                        clause_payload.get("type") or ""
                    ).upper() != CLAUSE_TYPE_LITERAL:
                        continue

                    subject_graph_slug, _subject_alias = clause_payload["subject"][0]
                    if (
                        enforced_graph_slug
                        and subject_graph_slug
                        and subject_graph_slug != enforced_graph_slug
                    ):
                        continue

                    constrained_child_pairs, applied_here = (
                        self.clause_compiler.filter_pairs_by_clause(
                            pairs_queryset=constrained_child_pairs,
                            clause_payload=clause_payload,
                            correlate_field=child_id_field_name,
                        )
                    )
                    had_any_inner_filters = had_any_inner_filters or applied_here

                for nested_group_payload in node_payload.get("groups") or []:
                    pending_nodes.append(nested_group_payload)

        nested_group_payload = next(
            (
                nested
                for nested in group_payload.get("groups") or []
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

                (
                    _anchor_graph_slug_ignored,
                    _nested_terminal_graph_slug,
                    nested_pairs_for_child,
                    nested_child_id_field_name,
                ) = self.path_navigator.build_scoped_pairs_for_path(
                    path_segments=nested_path,
                    is_inverse_relationship=bool(nested_relationship.get("is_inverse")),
                    correlate_on_field=child_id_field_name,
                )

                literal_clauses_all: List[Dict[str, Any]] = []
                stack_for_collection: List[Dict[str, Any]] = [nested_group_payload]
                while stack_for_collection:
                    node_payload = stack_for_collection.pop()
                    if not ((node_payload.get("relationship")) or {}).get("path"):
                        for clause_payload in node_payload.get("clauses") or []:
                            if (
                                clause_payload.get("type") or ""
                            ).upper() == CLAUSE_TYPE_LITERAL:
                                literal_clauses_all.append(clause_payload)
                    for deeper_group_payload in node_payload.get("groups") or []:
                        stack_for_collection.append(deeper_group_payload)

                nested_ok_pairs = nested_pairs_for_child
                for clause_payload in literal_clauses_all:
                    nested_ok_pairs, applied_here = (
                        self.clause_compiler.filter_pairs_by_clause(
                            pairs_queryset=nested_ok_pairs,
                            clause_payload=clause_payload,
                            correlate_field=nested_child_id_field_name,
                        )
                    )
                    had_any_inner_filters = had_any_inner_filters or applied_here

                if nested_quantifier == QUANTIFIER_ANY:
                    constrained_child_pairs = constrained_child_pairs.filter(
                        Exists(nested_ok_pairs)
                    )
                    had_any_inner_filters = True
                elif nested_quantifier == QUANTIFIER_NONE:
                    constrained_child_pairs = constrained_child_pairs.filter(
                        Exists(nested_pairs_for_child) & ~Exists(nested_ok_pairs)
                    )
                    had_any_inner_filters = True
                else:
                    same_child_ok = nested_ok_pairs.filter(
                        **{
                            nested_child_id_field_name: OuterRef(
                                nested_child_id_field_name
                            )
                        }
                    )
                    violating_pairs = nested_pairs_for_child.filter(
                        ~Exists(same_child_ok)
                    )
                    constrained_child_pairs = constrained_child_pairs.filter(
                        Exists(nested_pairs_for_child) & ~Exists(violating_pairs)
                    )
                    had_any_inner_filters = True

        terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]
        terminal_node_alias = compiled_pair_info["terminal_node_alias"]

        for related_clause_payload in group_payload.get("clauses") or []:
            if (
                related_clause_payload.get("type") or ""
            ).upper() != CLAUSE_TYPE_RELATED:
                continue

            subject_graph_slug, subject_node_alias = related_clause_payload["subject"][
                0
            ]
            operator_token = (related_clause_payload.get("operator") or "").upper()
            has_operands = bool(related_clause_payload.get("operands"))

            if (
                subject_graph_slug == terminal_graph_slug
                and subject_node_alias == terminal_node_alias
                and not has_operands
            ):
                datatype_name_skip = self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
                presence_means_match_skip = (
                    self.clause_compiler._presence_means_match_for_zero_operands(
                        datatype_name_skip, operator_token
                    )
                )
                if presence_means_match_skip:
                    continue

            related_exists_qs = self.clause_compiler.related_child_exists_qs(
                related_clause_payload, compiled_pair_info
            )
            if related_exists_qs is None:
                continue

            if not has_operands:
                datatype_name = self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
                presence_means_match = (
                    self.clause_compiler._presence_means_match_for_zero_operands(
                        datatype_name, operator_token
                    )
                )
                constrained_child_pairs = (
                    constrained_child_pairs.filter(Exists(related_exists_qs))
                    if presence_means_match
                    else constrained_child_pairs.filter(~Exists(related_exists_qs))
                )
                had_any_inner_filters = True
            else:
                constrained_child_pairs = constrained_child_pairs.filter(
                    Exists(related_exists_qs)
                )
                had_any_inner_filters = True

        return constrained_child_pairs, had_any_inner_filters
