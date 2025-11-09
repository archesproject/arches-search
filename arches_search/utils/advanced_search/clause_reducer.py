from typing import Any, Dict, List, Optional, Tuple, NamedTuple
from django.db.models import Exists, OuterRef, Q, QuerySet
from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.literal_clause_evaluator import (
    LiteralClauseEvaluator,
)
from arches_search.utils.advanced_search.related_clause_evaluator import (
    RelatedClauseEvaluator,
)
from arches_search.utils.advanced_search.resource_scope_evaluator import (
    ResourceScopeEvaluator,
)
from arches_search.utils.advanced_search.tile_scope_evaluator import (
    TileScopeEvaluator,
)

LOGIC_AND = "AND"
LOGIC_OR = "OR"

SCOPE_RESOURCE = "RESOURCE"
SCOPE_TILE = "TILE"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"

QUANTIFIER_ANY = "ANY"
QUANTIFIER_NONE = "NONE"


class ReduceResult(NamedTuple):
    relationshipless_q: Optional[Q]
    anchor_exists: List[Exists]
    constrained_child_rows: Optional[QuerySet]
    had_inner_filters: bool
    has_child_targeting_clause: bool
    literal_ok_rows: Optional[QuerySet]


class ClauseReducer:
    def __init__(
        self,
        *,
        literal_evaluator: LiteralClauseEvaluator,
        related_evaluator: RelatedClauseEvaluator,
        facet_registry,
        path_navigator,
    ) -> None:
        self.literal_evaluator = literal_evaluator
        self.related_evaluator = related_evaluator
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.resource_scope_evaluator = ResourceScopeEvaluator(
            literal_evaluator=self.literal_evaluator,
            related_evaluator=self.related_evaluator,
        )
        self.tile_scope_evaluator = TileScopeEvaluator(
            literal_evaluator=self.literal_evaluator,
            facet_registry=self.facet_registry,
            path_navigator=self.path_navigator,
        )

    def reduce(
        self,
        *,
        group_payload: Dict[str, Any],
        traversal_context: Optional[Dict[str, Any]] = None,
        child_rows: Optional[QuerySet] = None,
        logic: str = LOGIC_AND,
    ) -> ReduceResult:
        relationship_block = group_payload.get("relationship") or {}
        path_for_group = relationship_block.get("path")
        is_relationshipless = not bool(path_for_group)

        relationshipless_q: Optional[Q] = None
        anchor_exists: List[Exists] = []
        constrained_child_rows: Optional[QuerySet] = None
        had_inner_filters = False
        has_child_targeting_clause = False
        literal_ok_rows: Optional[QuerySet] = None

        if is_relationshipless and child_rows is None and traversal_context is None:
            group_scope = (group_payload.get("scope") or SCOPE_RESOURCE).upper()
            if group_scope == SCOPE_TILE:
                relationshipless_q = self.relationshipless_tile_q(group_payload)
            else:
                relationshipless_q = self.resource_scope_evaluator.q_for_group(
                    group_payload
                )
            if group_scope == SCOPE_RESOURCE:
                anchor_exists = self._anchor_exists_for_group(group_payload)

            return ReduceResult(
                relationshipless_q=relationshipless_q,
                anchor_exists=anchor_exists,
                constrained_child_rows=None,
                had_inner_filters=False,
                has_child_targeting_clause=False,
                literal_ok_rows=None,
            )

        if child_rows is not None and traversal_context is not None:
            constrained_child_rows = child_rows

            if logic == LOGIC_AND:
                constrained_child_rows, applied_here = (
                    self._filter_children_by_group_literals(
                        constrained_child_rows, traversal_context, group_payload
                    )
                )
                had_inner_filters = had_inner_filters or applied_here
            else:
                or_q, saw_any_ok_rows = self._or_q_from_group_literals(
                    group_payload, traversal_context
                )
                if saw_any_ok_rows and or_q is not None:
                    constrained_child_rows = child_rows.filter(or_q)
                    had_inner_filters = True

            nested_group_payload = next(
                (
                    nested
                    for nested in group_payload.get("groups") or []
                    if ((nested.get("relationship")) or {}).get("path")
                ),
                None,
            )
            if nested_group_payload:
                constrained_child_rows, applied_nested = (
                    self._apply_nested_single_hop_literals(
                        constrained_child_rows, traversal_context, nested_group_payload
                    )
                )
                had_inner_filters = had_inner_filters or applied_nested

            constrained_child_rows, applied_related = (
                self._apply_related_clauses_to_children(
                    constrained_child_rows, traversal_context, group_payload
                )
            )
            had_inner_filters = had_inner_filters or applied_related

            has_child_targeting_clause = any(
                (clause.get("type") or "").upper() == CLAUSE_TYPE_RELATED
                for clause in (group_payload.get("clauses") or [])
            )

            if (
                traversal_context.get("is_inverse")
                and len(traversal_context.get("path_segments") or []) == 1
            ):
                literal_ok_rows = self.literal_evaluator.ok_child_rows_from_literals(
                    group_payload=group_payload,
                    correlate_field=traversal_context["child_id_field"],
                    terminal_graph_slug=traversal_context["terminal_graph_slug"],
                )

        return ReduceResult(
            relationshipless_q=relationshipless_q,
            anchor_exists=anchor_exists,
            constrained_child_rows=constrained_child_rows,
            had_inner_filters=had_inner_filters,
            has_child_targeting_clause=has_child_targeting_clause,
            literal_ok_rows=literal_ok_rows,
        )

    def relationshipless_tile_q(self, group_payload: Dict[str, Any]) -> Q:
        tiles_for_anchor_resource = arches_models.Tile.objects.filter(
            resourceinstance_id=OuterRef("resourceinstanceid")
        )
        return self.tile_scope_evaluator.q_for_group(
            group_payload=group_payload,
            tiles_for_anchor_resource=tiles_for_anchor_resource,
        )

    def _anchor_exists_for_group(self, group_payload: Dict[str, Any]) -> List[Exists]:
        existence_predicates: List[Exists] = []
        for clause_payload in group_payload.get("clauses") or []:
            clause_type = (clause_payload.get("type") or "").upper()
            if clause_type == CLAUSE_TYPE_LITERAL:
                existence_predicates.append(
                    self.literal_evaluator.exists_for_anchor(clause_payload)
                )
            elif clause_type == CLAUSE_TYPE_RELATED:
                existence_predicates.append(
                    self.related_evaluator.presence_for_anchor(clause_payload)
                )
        return existence_predicates

    def _filter_children_by_group_literals(
        self,
        child_rows: QuerySet,
        traversal_context: Dict[str, Any],
        group_payload: Dict[str, Any],
    ) -> Tuple[QuerySet, bool]:
        working_rows = child_rows
        applied_any = False

        pending_nodes: List[Dict[str, Any]] = [
            g
            for g in (group_payload.get("groups") or [])
            if not ((g.get("relationship") or {}).get("path"))
        ]
        while pending_nodes:
            node_payload = pending_nodes.pop()
            for clause_payload in node_payload.get("clauses") or []:
                if (clause_payload.get("type") or "").upper() != CLAUSE_TYPE_LITERAL:
                    continue
                exists_expression = self.literal_evaluator.exists_for_child(
                    clause_payload, correlate_field=traversal_context["child_id_field"]
                )
                working_rows = working_rows.filter(exists_expression)
                applied_any = True
            for deeper_group_payload in node_payload.get("groups") or []:
                if ((deeper_group_payload.get("relationship")) or {}).get("path"):
                    continue
                pending_nodes.append(deeper_group_payload)

        return working_rows, applied_any

    def _or_q_from_group_literals(
        self,
        group_payload: Dict[str, Any],
        traversal_context: Dict[str, Any],
    ) -> Tuple[Optional[Q], bool]:
        or_q = Q(pk__in=[])
        saw_any_ok_rows = False

        for child_group_payload in group_payload.get("groups") or []:
            if ((child_group_payload.get("relationship")) or {}).get("path"):
                continue
            ok_rows = self.literal_evaluator.ok_child_rows_from_literals(
                child_group_payload,
                correlate_field=traversal_context["child_id_field"],
                terminal_graph_slug=traversal_context["terminal_graph_slug"],
            )
            if ok_rows is None:
                continue
            or_q |= Q(Exists(ok_rows))
            saw_any_ok_rows = True

        return (or_q if saw_any_ok_rows else None), saw_any_ok_rows

    def _apply_nested_single_hop_literals(
        self,
        base_child_rows: QuerySet,
        traversal_context: Dict[str, Any],
        nested_group_payload: Dict[str, Any],
    ) -> Tuple[QuerySet, bool]:
        nested_relationship = nested_group_payload.get("relationship") or {}
        nested_path = nested_relationship.get("path") or []
        if len(nested_path) != 1:
            return base_child_rows, False

        parent_child_id_field_name = traversal_context["child_id_field"]
        nested_quantifier = (
            (nested_relationship.get("traversal_quantifiers") or [QUANTIFIER_ANY])[0]
        ).upper()

        (
            _ignored_anchor_slug,
            nested_terminal_graph_slug,
            nested_child_rows,
            nested_child_id_field_name,
        ) = self.path_navigator.build_scoped_pairs_for_path(
            path_segments=nested_path,
            is_inverse_relationship=bool(nested_relationship.get("is_inverse")),
            correlate_on_field=parent_child_id_field_name,
        )

        literal_clauses_all: List[Dict[str, Any]] = []
        stack_for_collection: List[Dict[str, Any]] = [nested_group_payload]
        while stack_for_collection:
            node_payload = stack_for_collection.pop()
            if not ((node_payload.get("relationship") or {}).get("path")):
                for clause_payload in node_payload.get("clauses") or []:
                    if (
                        clause_payload.get("type") or ""
                    ).upper() == CLAUSE_TYPE_LITERAL:
                        literal_clauses_all.append(clause_payload)
            for deeper_group_payload in node_payload.get("groups") or []:
                stack_for_collection.append(deeper_group_payload)

        nested_ok_rows = nested_child_rows
        applied_any = False
        for clause_payload in literal_clauses_all:
            exists_expression = self.literal_evaluator.exists_for_child(
                clause_payload, correlate_field=nested_child_id_field_name
            )
            nested_ok_rows = nested_ok_rows.filter(exists_expression)
            applied_any = True

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
            True or applied_any,
        )

    def _apply_related_clauses_to_children(
        self,
        child_rows: QuerySet,
        traversal_context: Dict[str, Any],
        group_payload: Dict[str, Any],
    ) -> Tuple[QuerySet, bool]:
        constrained = child_rows
        applied_any = False

        for clause_payload in group_payload.get("clauses") or []:
            if (clause_payload.get("type") or "").upper() != CLAUSE_TYPE_RELATED:
                continue

            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = (clause_payload.get("operator") or "").upper()
            has_operands = bool(clause_payload.get("operands"))

            if (
                not has_operands
                and subject_graph_slug == traversal_context["terminal_graph_slug"]
                and subject_node_alias == traversal_context["terminal_node_alias"]
            ):
                datatype_name = self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
                if self.facet_registry.zero_arity_presence_is_match(
                    datatype_name, operator_token
                ):
                    continue

            presence_expression = self.related_evaluator.presence_for_child(
                clause_payload, traversal_context
            )
            constrained = constrained.filter(presence_expression)
            applied_any = True

        return constrained, applied_any
