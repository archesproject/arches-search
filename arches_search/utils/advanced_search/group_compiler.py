from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q
from arches_search.utils.advanced_search.relationship_compiler import (
    RelationshipCompiler,
)
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
        relationship_compiler: RelationshipCompiler,
    ) -> None:
        self.clause_reducer = clause_reducer
        self.path_navigator = path_navigator
        self.relationship_compiler = relationship_compiler

    def compile(
        self,
        group_payload: Dict[str, Any],
        current_context_side: str = CONTEXT_ANCHOR,
        traversal_context_for_parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Q, List[Exists]]:
        group_scope = (group_payload.get("scope") or SCOPE_RESOURCE).upper()
        relationship_block = group_payload.get("relationship")
        path_segments = (relationship_block or {}).get("path")
        has_relationship = bool(path_segments)
        has_relationship_child = any(
            ((child_group_payload.get("relationship") or {}).get("path"))
            for child_group_payload in (group_payload.get("groups") or [])
        )
        group_logic = (group_payload.get("logic") or LOGIC_AND).upper()

        if (
            group_scope == SCOPE_TILE
            and not has_relationship
            and not has_relationship_child
        ):
            reduce_result = self.clause_reducer.reduce(
                group_payload=group_payload,
                traversal_context=None,
                child_rows=None,
                use_or_logic=(group_logic == LOGIC_OR),
            )
            return reduce_result.relationshipless_q or Q(), []

        if not has_relationship:
            reduce_result = self.clause_reducer.reduce(
                group_payload=group_payload,
                traversal_context=None,
                child_rows=None,
                use_or_logic=(group_logic == LOGIC_OR),
            )
            parent_q = reduce_result.relationshipless_q or Q()

            children_q, children_existence_predicates = self._compile_children(
                subgroups=group_payload.get("groups") or [],
                parent_has_relationship=False,
                current_context_side=current_context_side,
                traversal_context_for_parent=traversal_context_for_parent,
            )

            if group_logic == LOGIC_OR:
                combined_q = Q(pk__in=[])
                if parent_q:
                    combined_q |= parent_q
                if children_q:
                    combined_q |= children_q
                for existence_expression in children_existence_predicates:
                    combined_q |= Q(existence_expression)
                return combined_q, []

            combined_q = parent_q & (children_q or Q())
            return combined_q, children_existence_predicates

        existence_predicates: List[Exists] = []

        traversal_context, child_row_set = (
            self.relationship_compiler.build_relationship_context(relationship_block)
        )
        child_id_field_name = traversal_context["child_id_field"]
        is_inverse_relationship = traversal_context.get("is_inverse", False)

        if is_inverse_relationship:
            child_row_set_excluding_anchor = child_row_set
        else:
            child_row_set_excluding_anchor = child_row_set.exclude(
                **{child_id_field_name: OuterRef("resourceinstanceid")}
            )

        reduce_result = self.clause_reducer.reduce(
            group_payload=group_payload,
            traversal_context=traversal_context,
            child_rows=child_row_set_excluding_anchor,
            use_or_logic=(group_logic == LOGIC_OR),
        )

        qualifying_child_rows = (
            reduce_result.constrained_child_rows
            if reduce_result.constrained_child_rows is not None
            else child_row_set_excluding_anchor
        )

        normalized_relationship = (
            self.relationship_compiler.normalize_relationship_context(
                relationship_block
            )
        )
        traversal_quantifier = normalized_relationship["hop_quantifier"]
        is_single_inverse_hop = (
            normalized_relationship["is_inverse"]
            and len(normalized_relationship["path_segments"]) == 1
        )

        if is_single_inverse_hop and traversal_quantifier == QUANTIFIER_ALL:
            traversal_quantifier = QUANTIFIER_ANY

        if traversal_quantifier == QUANTIFIER_ANY:
            existence_predicates.append(Exists(qualifying_child_rows))
        elif traversal_quantifier == QUANTIFIER_NONE:
            if reduce_result.had_inner_filters:
                none_predicate = Exists(child_row_set_excluding_anchor) & ~Exists(
                    qualifying_child_rows
                )
            else:
                none_predicate = ~Exists(child_row_set_excluding_anchor)
            existence_predicates.append(none_predicate)
        else:
            same_child_ok = qualifying_child_rows.filter(
                **{child_id_field_name: OuterRef(child_id_field_name)}
            )
            violators = child_row_set_excluding_anchor.filter(~Exists(same_child_ok))
            existence_predicates.append(
                Exists(child_row_set_excluding_anchor) & ~Exists(violators)
            )

        children_q, children_existence_predicates = self._compile_children(
            subgroups=group_payload.get("groups") or [],
            parent_has_relationship=True,
            current_context_side=CONTEXT_CHILD,
            traversal_context_for_parent=traversal_context,
        )

        all_existence_predicates: List[Exists] = [
            *existence_predicates,
            *children_existence_predicates,
        ]

        if group_logic == LOGIC_OR:
            combined_q = children_q if children_q is not None else Q(pk__in=[])
            for existence_expression in all_existence_predicates:
                combined_q = combined_q | Q(existence_expression)
            return combined_q, []

        combined_q = children_q if children_q is not None else Q()
        return combined_q, all_existence_predicates

    def _compile_children(
        self,
        subgroups: List[Dict[str, Any]],
        parent_has_relationship: bool,
        current_context_side: str,
        traversal_context_for_parent: Optional[Dict[str, Any]],
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
                traversal_context_for_parent=traversal_context_for_parent,
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
