from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, NamedTuple

from django.db.models import Exists, OuterRef, Q, QuerySet
from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.clause_compiler import ClauseCompiler


LOGIC_AND = "AND"
LOGIC_OR = "OR"


class ReduceResult(NamedTuple):
    relationshipless_q: Optional[Q]
    anchor_exists: List[Exists]
    constrained_pairs: Optional[QuerySet]
    had_inner_filters: bool
    has_related_clause: bool


class ClauseReducer:
    def __init__(
        self,
        clause_compiler: ClauseCompiler,
    ) -> None:
        self.clause_compiler = clause_compiler

    def reduce(
        self,
        *,
        group_payload: Dict[str, Any],
        compiled_pair_info: Optional[Dict[str, Any]] = None,
        base_pairs: Optional[QuerySet] = None,
        use_or_logic: bool = False,
    ) -> ReduceResult:
        relationship_block = group_payload.get("relationship") or {}
        path_for_group = relationship_block.get("path")
        is_relationshipless = not bool(path_for_group)
        has_relationship_child = any(
            ((child.get("relationship") or {}).get("path"))
            for child in (group_payload.get("groups") or [])
        )

        relationshipless_q: Optional[Q] = None
        if (
            is_relationshipless
            and not has_relationship_child
            and compiled_pair_info is None
            and base_pairs is None
        ):
            relationshipless_q = self._relationshipless_resource_q(
                group_payload=group_payload,
                use_and_logic=(group_payload.get("logic") or LOGIC_AND).upper()
                == LOGIC_AND,
            )

        anchor_exists: List[Exists] = []
        if compiled_pair_info is None and base_pairs is None:
            anchor_exists = self.clause_compiler.anchor_exists_for_group(group_payload)

        constrained_pairs: Optional[QuerySet] = None
        had_inner_filters = False
        has_related_clause = self.clause_compiler.group_has_child_targeting_clause(
            group_payload
        )

        if compiled_pair_info is not None and base_pairs is not None:
            constrained_pairs, had_inner_filters = (
                self.clause_compiler.constrain_pairs_for_group(
                    base_pairs=base_pairs,
                    compiled_pair_info=compiled_pair_info,
                    group_payload=group_payload,
                    use_or_logic=use_or_logic,
                )
            )

        return ReduceResult(
            relationshipless_q=relationshipless_q,
            anchor_exists=anchor_exists,
            constrained_pairs=constrained_pairs,
            had_inner_filters=had_inner_filters,
            has_related_clause=has_related_clause,
        )

    def relationshipless_tile_q(self, group_payload: Dict[str, Any]) -> Q:
        tiles_for_anchor_resource = arches_models.Tile.objects.filter(
            resourceinstance_id=OuterRef("resourceinstanceid")
        )
        return self.clause_compiler.tile_scope_q(
            group_payload=group_payload,
            tiles_for_anchor_resource=tiles_for_anchor_resource,
        )

    def _relationshipless_resource_q(
        self, *, group_payload: Dict[str, Any], use_and_logic: bool
    ) -> Optional[Q]:
        has_any_piece = False
        combined_q = Q()

        for clause_payload in group_payload.get("clauses") or []:
            clause_exists = self.clause_compiler.compile(clause_payload=clause_payload)
            clause_q = Q(clause_exists)
            if not has_any_piece:
                combined_q = clause_q
                has_any_piece = True
            else:
                combined_q = (
                    combined_q & clause_q if use_and_logic else combined_q | clause_q
                )

        for child_group_payload in group_payload.get("groups") or []:
            if (child_group_payload.get("relationship") or {}).get("path"):
                return None
            child_q = self._relationshipless_resource_q(
                group_payload=child_group_payload, use_and_logic=use_and_logic
            )
            if child_q is None:
                return None
            if not has_any_piece:
                combined_q = child_q
                has_any_piece = True
            else:
                combined_q = (
                    combined_q & child_q if use_and_logic else combined_q | child_q
                )

        if not has_any_piece:
            return Q() if use_and_logic else Q(pk__in=[])
        return combined_q
