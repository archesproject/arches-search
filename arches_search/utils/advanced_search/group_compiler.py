from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q

from arches.app.models import models as arches_models
from arches_search.utils.advanced_search.clause_reducer import ClauseReducer
from arches_search.utils.advanced_search.literal_clause_evaluator import (
    LiteralClauseEvaluator,
)
from arches_search.utils.advanced_search.related_clause_evaluator import (
    RelatedClauseEvaluator,
)
from arches_search.utils.advanced_search.tile_scope_evaluator import TileScopeEvaluator
from arches_search.utils.advanced_search.relationship_utils import (
    has_relationship_path,
)

from arches_search.utils.advanced_search.constants import (
    CLAUSE_TYPE_LITERAL,
    LOGIC_AND,
    LOGIC_OR,
    QUANTIFIER_ALL,
    QUANTIFIER_ANY,
    QUANTIFIER_NONE,
    SCOPE_TILE,
)


class GroupCompiler:
    def __init__(
        self,
        clause_reducer: ClauseReducer,
        literal_clause_evaluator: LiteralClauseEvaluator,
        related_clause_evaluator: RelatedClauseEvaluator,
        tile_scope_evaluator: TileScopeEvaluator,
        path_navigator,
    ) -> None:
        self.clause_reducer = clause_reducer
        self.literal_clause_evaluator = literal_clause_evaluator
        self.related_clause_evaluator = related_clause_evaluator
        self.tile_scope_evaluator = tile_scope_evaluator
        self.path_navigator = path_navigator

    def compile(
        self,
        group_payload: Dict[str, Any],
    ) -> Tuple[Q, List[Any]]:
        scope_token = group_payload["scope"].upper()
        group_logic_token = group_payload["logic"].upper()
        relationship_block = group_payload["relationship"]

        has_relationship = has_relationship_path(relationship_block)

        if scope_token == SCOPE_TILE and not has_relationship:
            return self._compile_tile_scope_without_relationship(
                group_payload=group_payload,
            )

        if not has_relationship:
            return self._compile_resource_scope_without_relationship(
                group_payload=group_payload,
                group_logic_token=group_logic_token,
            )

        return self._compile_with_relationship(
            group_payload=group_payload,
            group_logic_token=group_logic_token,
        )

    def _group_has_any_relationship(self, group_payload: Dict[str, Any]) -> bool:
        relationship_block = group_payload.get("relationship") or {}
        if has_relationship_path(relationship_block):
            return True

        for subgroup_payload in group_payload.get("groups") or []:
            if self._group_has_any_relationship(group_payload=subgroup_payload):
                return True

        return False

    def _compile_tile_scope_without_relationship(
        self,
        group_payload: Dict[str, Any],
    ) -> Tuple[Q, List[Any]]:
        tiles_for_anchor_resource = arches_models.Tile.objects.filter(
            resourceinstance_id=OuterRef("resourceinstanceid")
        )
        tile_q = self.tile_scope_evaluator.compose_group_predicate(
            group_payload=group_payload,
            tiles_for_anchor_resource=tiles_for_anchor_resource,
        )
        return tile_q, []

    def _compile_resource_scope_without_relationship(
        self,
        group_payload: Dict[str, Any],
        group_logic_token: str,
    ) -> Tuple[Q, List[Any]]:
        group_has_any_relationship = self._group_has_any_relationship(
            group_payload=group_payload
        )

        if group_has_any_relationship:
            group_payload_for_compose: Dict[str, Any] = {
                **group_payload,
                "groups": [],
            }
        else:
            group_payload_for_compose = group_payload

        parent_q = self._compose_resource_scope_group_predicate(
            group_payload_for_compose
        )

        if not group_has_any_relationship:
            return parent_q, []

        children_q, children_existence_predicates = self._compile_children(
            subgroups=group_payload["groups"],
        )

        if group_logic_token == LOGIC_OR:
            combined_or_q = parent_q
            if children_q is not None:
                combined_or_q = combined_or_q | children_q
            for existence_expression in children_existence_predicates:
                combined_or_q = combined_or_q | Q(existence_expression)
            return combined_or_q, []

        combined_and_q = parent_q & (children_q or Q())
        return combined_and_q, children_existence_predicates

    def _compose_resource_scope_group_predicate(
        self,
        group_payload: Dict[str, Any],
    ) -> Q:
        predicate_fragments: List[Q] = []

        for clause_payload in group_payload["clauses"]:
            if clause_payload["type"] == CLAUSE_TYPE_LITERAL:
                exists_expression = self.literal_clause_evaluator.build_anchor_exists(
                    clause_payload
                )
            else:
                exists_expression = self.related_clause_evaluator.evaluate_at_anchor(
                    clause_payload=clause_payload,
                )
            predicate_fragments.append(Q(exists_expression))

        for child_group_payload in group_payload["groups"]:
            predicate_fragments.append(
                self._compose_resource_scope_group_predicate(child_group_payload)
            )

        if group_payload["logic"] == LOGIC_AND:
            combined_predicate = Q()
            for predicate_fragment in predicate_fragments:
                combined_predicate &= predicate_fragment
            return combined_predicate

        combined_predicate = Q(pk__in=[])
        for predicate_fragment in predicate_fragments:
            combined_predicate |= predicate_fragment
        return combined_predicate

    def _compile_with_relationship(
        self,
        group_payload: Dict[str, Any],
        group_logic_token: str,
    ) -> Tuple[Q, List[Any]]:
        relationship_block = group_payload["relationship"]

        anchor_q, has_anchor_literals = self.clause_reducer.build_anchor_literal_q(
            group_payload=group_payload,
            logic=group_logic_token,
        )

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

        group_payload_for_reducer: Dict[str, Any] = {
            **group_payload,
            "groups": [],
        }

        reduce_result = self.clause_reducer.reduce(
            group_payload=group_payload_for_reducer,
            traversal_context=traversal_context,
            child_rows=child_row_set_excluding_anchor,
            logic=group_logic_token,
        )

        qualifying_child_rows = (
            reduce_result.constrained_child_rows
            if reduce_result.constrained_child_rows is not None
            else child_row_set_excluding_anchor
        )

        child_resource_predicate_q, had_child_group_filters = (
            self._build_child_resource_predicate_for_relationship_group(
                subgroups=group_payload.get("groups") or [],
                child_id_field_name=child_id_field_name,
                logic_token=group_logic_token,
            )
        )
        if child_resource_predicate_q is not None:
            qualifying_child_rows = qualifying_child_rows.filter(
                child_resource_predicate_q
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

        had_inner_filters = bool(
            reduce_result.had_inner_filters or had_child_group_filters
        )

        existence_predicates = self._build_existence_predicates_for_quantifier(
            traversal_quantifier=traversal_quantifier_token,
            had_inner_filters=had_inner_filters,
            child_row_set_excluding_anchor=child_row_set_excluding_anchor,
            qualifying_child_rows=qualifying_child_rows,
            child_id_field_name=child_id_field_name,
        )

        if group_logic_token == LOGIC_OR:
            combined_or_q: Optional[Q] = None

            if has_anchor_literals:
                combined_or_q = anchor_q

            for existence_expression in existence_predicates:
                existence_q = Q(existence_expression)
                combined_or_q = (
                    existence_q
                    if combined_or_q is None
                    else (combined_or_q | existence_q)
                )

            return combined_or_q or Q(), []

        combined_and_q = anchor_q
        return combined_and_q, existence_predicates

    def _build_child_resource_predicate_for_relationship_group(
        self,
        subgroups: List[Dict[str, Any]],
        child_id_field_name: str,
        logic_token: str,
    ) -> Tuple[Optional[Q], bool]:
        if not subgroups:
            return None, False

        combined_child_predicate_q: Optional[Q] = None
        had_any_filters = False

        for subgroup_payload in subgroups:
            subgroup_q, subgroup_existence_predicates = self.compile(
                group_payload=subgroup_payload,
            )

            if not subgroup_q and not subgroup_existence_predicates:
                continue

            child_resource_queryset = arches_models.ResourceInstance.objects.filter(
                resourceinstanceid=OuterRef(child_id_field_name)
            ).filter(subgroup_q)

            for existence_expression in subgroup_existence_predicates:
                child_resource_queryset = child_resource_queryset.filter(
                    Q(existence_expression)
                )

            subgroup_as_child_predicate_q = Q(Exists(child_resource_queryset))
            had_any_filters = True

            if combined_child_predicate_q is None:
                combined_child_predicate_q = subgroup_as_child_predicate_q
                continue

            if logic_token == LOGIC_OR:
                combined_child_predicate_q = (
                    combined_child_predicate_q | subgroup_as_child_predicate_q
                )
            else:
                combined_child_predicate_q = (
                    combined_child_predicate_q & subgroup_as_child_predicate_q
                )

        if combined_child_predicate_q is None:
            return None, False

        return combined_child_predicate_q, had_any_filters

    def _build_existence_predicates_for_quantifier(
        self,
        traversal_quantifier: str,
        had_inner_filters: bool,
        child_row_set_excluding_anchor,
        qualifying_child_rows,
        child_id_field_name: str,
    ) -> List[Any]:
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
    ) -> Tuple[Optional[Q], List[Any]]:
        combined_children_q: Optional[Q] = None
        accumulated_existence_predicates: List[Any] = []

        for subgroup_payload in subgroups:
            subgroup_q, subgroup_existence_predicates = self.compile(
                group_payload=subgroup_payload,
            )

            combined_children_q = (
                subgroup_q
                if combined_children_q is None
                else (combined_children_q & subgroup_q)
            )
            accumulated_existence_predicates.extend(subgroup_existence_predicates)

        return combined_children_q, accumulated_existence_predicates
