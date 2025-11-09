from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q
from arches_search.utils.advanced_search.path_navigator import PathNavigator
from arches_search.utils.advanced_search.clause_reducer import ClauseReducer
from arches_search.utils.advanced_search.clause_compiler import ClauseCompiler
from arches_search.utils.advanced_search.relationship_compiler import (
    RelationshipCompiler,
)


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
        path_navigator: PathNavigator,
        relationship_compiler: RelationshipCompiler,
        clause_compiler: ClauseCompiler,
    ) -> None:
        self.clause_reducer = clause_reducer
        self.path_navigator = path_navigator
        self.relationship_compiler = relationship_compiler
        self.clause_compiler = clause_compiler

    def compile(
        self,
        group_payload: Dict[str, Any],
        current_context_side: str = CONTEXT_ANCHOR,
        relationship_context_for_parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Q, List[Exists]]:
        group_scope = (group_payload.get("scope") or SCOPE_RESOURCE).upper()
        relationship_block = group_payload.get("relationship")
        path_segments = (relationship_block or {}).get("path")
        has_relationship = bool(path_segments)
        has_relationship_child = any(
            ((child.get("relationship") or {}).get("path"))
            for child in (group_payload.get("groups") or [])
        )

        if (
            group_scope == SCOPE_TILE
            and not has_relationship
            and not has_relationship_child
        ):
            return self.clause_reducer.relationshipless_tile_q(group_payload), []

        reduce_result = self.clause_reducer.reduce(
            group_payload=group_payload,
            compiled_pair_info=None,
            base_pairs=None,
            use_or_logic=(group_payload.get("logic") or LOGIC_AND).upper() == LOGIC_OR,
        )
        if reduce_result.relationshipless_q is not None:
            return reduce_result.relationshipless_q, []

        existence_predicates: List[Exists] = []
        relationship_pairs_info: Optional[Dict[str, Any]] = None

        if has_relationship:
            relationship_pairs_info, pairs_scoped_to_anchor_resource = (
                self.relationship_compiler.build_relationship_pairs(relationship_block)
            )
            child_id_field_name = relationship_pairs_info["child_id_field"]

            pairs_excluding_self = pairs_scoped_to_anchor_resource.exclude(
                **{child_id_field_name: OuterRef("resourceinstanceid")}
            )

            constraints_result = self.clause_reducer.reduce(
                group_payload=group_payload,
                compiled_pair_info=relationship_pairs_info,
                base_pairs=pairs_excluding_self,
                use_or_logic=(group_payload.get("logic") or LOGIC_AND).upper()
                == LOGIC_OR,
            )

            qualifying_child_pairs = (
                constraints_result.constrained_pairs
                if constraints_result.constrained_pairs is not None
                else pairs_excluding_self
            )
            had_inner_filters = constraints_result.had_inner_filters

            normalized_relationship = (
                self.relationship_compiler.normalize_relationship_context(
                    relationship_block
                )
            )
            traversal_quantifier = normalized_relationship["hop_quantifier"]
            is_inverse_relationship = normalized_relationship["is_inverse"]
            is_single_inverse_hop = (
                is_inverse_relationship
                and len(normalized_relationship["path_segments"]) == 1
            )

            if is_single_inverse_hop:
                has_child_targeting_clause = constraints_result.has_related_clause
                if (
                    has_child_targeting_clause
                    and traversal_quantifier == QUANTIFIER_ALL
                ):
                    traversal_quantifier = QUANTIFIER_ANY

            if traversal_quantifier == QUANTIFIER_ANY:
                existence_predicates.append(Exists(qualifying_child_pairs))
            elif traversal_quantifier == QUANTIFIER_NONE:
                existence_predicates.append(
                    Exists(pairs_excluding_self) & ~Exists(qualifying_child_pairs)
                    if had_inner_filters
                    else ~Exists(pairs_excluding_self)
                )
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

        if (group_payload.get("scope") or SCOPE_RESOURCE).upper() == SCOPE_RESOURCE:
            anchor_exists_result = self.clause_reducer.reduce(
                group_payload=group_payload,
                compiled_pair_info=None,
                base_pairs=None,
                use_or_logic=False,
            )
            existence_predicates.extend(anchor_exists_result.anchor_exists)

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
            for exists_expression in all_existence_predicates:
                combined_q = combined_q | Q(exists_expression)
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
