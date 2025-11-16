from typing import Any, Dict, List, Optional, Tuple
from django.db.models import Exists, OuterRef, Q

from arches_search.utils.advanced_search.clause_reducer import ClauseReducer

LOGIC_AND = "AND"
LOGIC_OR = "OR"

SCOPE_RESOURCE = "RESOURCE"
SCOPE_TILE = "TILE"

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CONTEXT_ANCHOR = "ANCHOR"
CONTEXT_CHILD = "CHILD"


class GroupCompiler:
    def __init__(
        self,
        clause_reducer: ClauseReducer,
        path_navigator,
    ) -> None:
        self.clause_reducer = clause_reducer
        self.path_navigator = path_navigator

    def compile(
        self,
        group_payload: Dict[str, Any],
        current_context_side: str = CONTEXT_ANCHOR,
        traversal_context_for_parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Q, List[Exists]]:
        scope_token = group_payload["scope"].upper()
        group_logic_token = group_payload["logic"].upper()
        relationship_block = group_payload["relationship"]

        path_segments = (relationship_block or {}).get("path")
        has_relationship = bool(path_segments)

        if scope_token == SCOPE_TILE and not has_relationship:
            return self._compile_tile_scope_without_relationship(
                group_payload=group_payload,
                group_logic_token=group_logic_token,
            )

        if not has_relationship:
            return self._compile_resource_scope_without_relationship(
                group_payload=group_payload,
                group_logic_token=group_logic_token,
                current_context_side=current_context_side,
                traversal_context_for_parent=traversal_context_for_parent,
            )

        return self._compile_with_relationship(
            group_payload=group_payload,
            group_logic_token=group_logic_token,
        )

    def _group_has_any_relationship(self, group_payload: Dict[str, Any]) -> bool:
        relationship_block = group_payload.get("relationship") or {}
        if bool((relationship_block.get("path") or [])):
            return True

        for subgroup_payload in group_payload.get("groups") or []:
            if self._group_has_any_relationship(group_payload=subgroup_payload):
                return True

        return False

    def _compile_tile_scope_without_relationship(
        self,
        group_payload: Dict[str, Any],
        group_logic_token: str,
    ) -> Tuple[Q, List[Exists]]:
        reduce_result = self.clause_reducer.reduce(
            group_payload=group_payload,
            traversal_context=None,
            child_rows=None,
            logic=group_logic_token,
        )
        return reduce_result.relationshipless_q or Q(), []

    def _compile_resource_scope_without_relationship(
        self,
        group_payload: Dict[str, Any],
        group_logic_token: str,
        current_context_side: str,
        traversal_context_for_parent: Optional[Dict[str, Any]],
    ) -> Tuple[Q, List[Exists]]:
        reduce_result = self.clause_reducer.reduce(
            group_payload=group_payload,
            traversal_context=None,
            child_rows=None,
            logic=group_logic_token,
        )
        parent_q = reduce_result.relationshipless_q or Q()

        has_relationship_anywhere = self._group_has_any_relationship(
            group_payload=group_payload
        )

        if not has_relationship_anywhere:
            return parent_q, []

        children_q, children_existence_predicates = self._compile_children(
            subgroups=group_payload["groups"],
            parent_has_relationship=False,
            current_context_side=current_context_side,
            traversal_context_for_parent=traversal_context_for_parent,
        )

        if group_logic_token == LOGIC_OR:
            combined_or_q = None
            combined_or_q = (
                parent_q if combined_or_q is None else (combined_or_q | parent_q)
            )
            if children_q is not None:
                combined_or_q = (
                    children_q
                    if combined_or_q is None
                    else (combined_or_q | children_q)
                )
            for existence_expression in children_existence_predicates:
                existence_q = Q(existence_expression)
                combined_or_q = (
                    existence_q
                    if combined_or_q is None
                    else (combined_or_q | existence_q)
                )
            return combined_or_q or Q(), []

        combined_and_q = parent_q & (children_q or Q())
        return combined_and_q, children_existence_predicates

    def _compile_with_relationship(
        self,
        group_payload: Dict[str, Any],
        group_logic_token: str,
    ) -> Tuple[Q, List[Exists]]:
        relationship_block = group_payload["relationship"]

        traversal_context, child_row_set = self.path_navigator.build_relationship_pairs(
            relationship_block
        )
        child_id_field_name = traversal_context["child_id_field"]
        is_inverse_relationship = traversal_context.get("is_inverse", False)

        child_row_set_excluding_anchor = (
            child_row_set
            if is_inverse_relationship
            else child_row_set.exclude(
                **{child_id_field_name: OuterRef("resourceinstanceid")}
            )
        )

        reduce_result = self.clause_reducer.reduce(
            group_payload=group_payload,
            traversal_context=traversal_context,
            child_rows=child_row_set_excluding_anchor,
            logic=group_logic_token,
        )

        qualifying_child_rows = (
            reduce_result.constrained_child_rows
            if reduce_result.constrained_child_rows is not None
            else child_row_set_excluding_anchor
        )

        normalized_relationship = self.path_navigator.normalize_relationship_context(
            relationship_block
        )
        traversal_quantifier_token = normalized_relationship["traversal_quantifier"]
        is_single_inverse_hop = (
            normalized_relationship["is_inverse"]
            and len(normalized_relationship["path_segments"]) == 1
        )
        if is_single_inverse_hop and traversal_quantifier_token == QUANTIFIER_ALL:
            traversal_quantifier_token = QUANTIFIER_ANY

        existence_predicates = self._build_existence_predicates_for_quantifier(
            traversal_quantifier=traversal_quantifier_token,
            had_inner_filters=reduce_result.had_inner_filters,
            child_row_set_excluding_anchor=child_row_set_excluding_anchor,
            qualifying_child_rows=qualifying_child_rows,
            child_id_field_name=child_id_field_name,
        )

        children_q, children_existence_predicates = self._compile_children(
            subgroups=group_payload["groups"],
            parent_has_relationship=True,
            current_context_side=CONTEXT_CHILD,
            traversal_context_for_parent=traversal_context,
        )

        all_existence_predicates: List[Exists] = [
            *existence_predicates,
            *children_existence_predicates,
        ]

        if group_logic_token == LOGIC_OR:
            combined_or_q = children_q
            for existence_expression in all_existence_predicates:
                existence_q = Q(existence_expression)
                combined_or_q = (
                    existence_q
                    if combined_or_q is None
                    else (combined_or_q | existence_q)
                )
            return combined_or_q or Q(), []

        combined_and_q = children_q or Q()
        return combined_and_q, all_existence_predicates

    def _build_existence_predicates_for_quantifier(
        self,
        traversal_quantifier: str,
        had_inner_filters: bool,
        child_row_set_excluding_anchor,
        qualifying_child_rows,
        child_id_field_name: str,
    ) -> List[Exists]:
        if traversal_quantifier == QUANTIFIER_ANY:
            return [Exists(qualifying_child_rows)]

        if traversal_quantifier == QUANTIFIER_NONE:
            if had_inner_filters:
                none_predicate = Exists(child_row_set_excluding_anchor) & ~Exists(
                    qualifying_child_rows
                )
            else:
                none_predicate = ~Exists(child_row_set_excluding_anchor)
            return [none_predicate]

        same_child_ok = qualifying_child_rows.filter(
            **{child_id_field_name: OuterRef(child_id_field_name)}
        )
        violating_child_rows = child_row_set_excluding_anchor.filter(
            ~Exists(same_child_ok)
        )
        return [Exists(child_row_set_excluding_anchor) & ~Exists(violating_child_rows)]

    def _compile_children(
        self,
        subgroups: List[Dict[str, Any]],
        parent_has_relationship: bool,
        current_context_side: str,
        traversal_context_for_parent: Optional[Dict[str, Any]],
    ) -> Tuple[Optional[Q], List[Exists]]:
        combined_children_q: Optional[Q] = None
        accumulated_existence_predicates: List[Exists] = []

        for subgroup_payload in subgroups:
            subgroup_has_relationship = bool(
                (subgroup_payload["relationship"] or {}).get("path")
            )
            if parent_has_relationship and subgroup_has_relationship:
                continue

            next_context_side = (
                CONTEXT_CHILD
                if parent_has_relationship and not subgroup_has_relationship
                else current_context_side
            )

            subgroup_q, subgroup_existence_predicates = self.compile(
                group_payload=subgroup_payload,
                current_context_side=next_context_side,
                traversal_context_for_parent=traversal_context_for_parent,
            )

            if (
                parent_has_relationship
                and not subgroup_has_relationship
                and current_context_side == CONTEXT_CHILD
            ):
                continue

            combined_children_q = (
                subgroup_q
                if combined_children_q is None
                else (combined_children_q & subgroup_q)
            )
            accumulated_existence_predicates.extend(subgroup_existence_predicates)

        return combined_children_q, accumulated_existence_predicates
