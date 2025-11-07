from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet
from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.clause_compiler import ClauseCompiler
from arches_search.utils.advanced_search.path_navigator import PathNavigator
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

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"

CONTEXT_ANCHOR = "ANCHOR"
CONTEXT_CHILD = "CHILD"


class GroupCompiler:
    def __init__(
        self,
        clause_compiler: ClauseCompiler,
        path_navigator: PathNavigator,
        relationship_compiler: RelationshipCompiler,
    ) -> None:
        self.clause_compiler = clause_compiler
        self.path_navigator = path_navigator
        self.relationship_compiler = relationship_compiler

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
                use_or_logic=(group_payload.get("logic") or LOGIC_AND).upper()
                == LOGIC_OR,
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
                    (item.get("type") or "").upper() == CLAUSE_TYPE_RELATED
                    for item in (group_payload.get("clauses") or [])
                )
                if has_related_clause and traversal_quantifier == QUANTIFIER_ALL:
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
                    literal_ok_rows = (
                        self.relationship_compiler.child_ok_rows_from_literals(
                            group_payload, relationship_pairs_info
                        )
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

    def _compile_relationshipless_group_to_q(
        self, group_payload: Dict[str, Any]
    ) -> Optional[Q]:
        if ((group_payload.get("relationship")) or {}).get("path"):
            return None

        logic_token = (group_payload.get("logic") or LOGIC_AND).upper()
        scope_token = (group_payload.get("scope") or SCOPE_RESOURCE).upper()

        if scope_token == SCOPE_TILE:
            return self._compile_relationshipless_tile_group_to_q(
                group_payload=group_payload,
                use_and_logic=(logic_token == LOGIC_AND),
            )

        has_any_piece = False
        combined_q = Q()

        for clause_payload in group_payload.get("clauses") or []:
            clause_q = Q(
                self.clause_compiler.compile(
                    clause_payload=clause_payload, correlate_to_tile=False
                )
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

    # ---------- TILE-scope relationshipless logic (unchanged SQL shape)

    def _compile_relationshipless_tile_group_to_q(
        self, group_payload: Dict[str, Any], use_and_logic: bool
    ) -> Q:
        clause_payloads = group_payload.get("clauses") or []
        if not clause_payloads:
            return Q()

        tiles_for_anchor_resource = arches_models.Tile.objects.filter(
            resourceinstance_id=OuterRef("resourceinstanceid")
        )

        per_tile_exists_conditions: List[Q] = []
        resource_level_conditions: List[Q] = []

        for clause_payload in clause_payloads:
            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = (clause_payload["operator"] or "").upper()
            quantifier_token = (clause_payload["quantifier"] or "").upper()
            operand_items = clause_payload.get("operands") or []

            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
            )
            model_class = (
                self.clause_compiler.search_model_registry.get_model_for_datatype(
                    datatype_name
                )
            )
            subject_rows = model_class.objects.filter(
                graph_slug=subject_graph_slug, node_alias=subject_node_alias
            )

            rows_correlated_to_resource = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            )
            rows_correlated_to_tile_resource = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstance_id")
            )

            if not operand_items:
                presence_implies_match = (
                    self.clause_compiler.facet_registry.zero_arity_presence_is_match(
                        datatype_name, operator_token
                    )
                )

                if quantifier_token == QUANTIFIER_ANY:
                    condition = Q(
                        Exists(
                            rows_correlated_to_tile_resource.filter(
                                tileid=OuterRef("tileid")
                            )
                        )
                    )
                    per_tile_exists_conditions.append(
                        condition if presence_implies_match else ~condition
                    )
                    continue

                if quantifier_token == QUANTIFIER_NONE:
                    resource_level_conditions.append(
                        Q(~Exists(rows_correlated_to_resource))
                        if presence_implies_match
                        else Q(Exists(rows_correlated_to_resource))
                    )
                    continue

                tiles_missing_match = tiles_for_anchor_resource.filter(
                    ~Exists(
                        rows_correlated_to_tile_resource.filter(
                            tileid=OuterRef("tileid")
                        )
                    )
                )
                requires_all_tiles_match = Q(~Exists(tiles_missing_match))
                has_at_least_one_tile = Q(Exists(tiles_for_anchor_resource))
                resource_level_conditions.append(
                    (requires_all_tiles_match & has_at_least_one_tile)
                    if presence_implies_match
                    else Q(~Exists(tiles_for_anchor_resource))
                )
                continue

            predicate_expression, is_template_negated = (
                self.clause_compiler.operand_compiler.build_predicate(
                    datatype_name=datatype_name,
                    operator_token=operator_token,
                    operands=operand_items,
                    anchor_resource_id_annotation=None,
                )
            )

            if isinstance(predicate_expression, Q):
                matching_rows_resource = rows_correlated_to_resource.filter(
                    predicate_expression
                )
                matches_in_this_tile = rows_correlated_to_tile_resource.filter(
                    predicate_expression
                ).filter(tileid=OuterRef("tileid"))
            else:
                matching_rows_resource = rows_correlated_to_resource.filter(
                    **predicate_expression
                )
                matches_in_this_tile = rows_correlated_to_tile_resource.filter(
                    **predicate_expression
                ).filter(tileid=OuterRef("tileid"))

            if quantifier_token == QUANTIFIER_ANY:
                per_tile_exists_conditions.append(Q(Exists(matches_in_this_tile)))
                continue

            if quantifier_token == QUANTIFIER_NONE:
                resource_level_conditions.append(Q(~Exists(matching_rows_resource)))
                continue

            has_at_least_one_tile = Q(Exists(tiles_for_anchor_resource))

            if not is_template_negated:
                tiles_missing_match = tiles_for_anchor_resource.filter(
                    ~Exists(matches_in_this_tile)
                )
                resource_level_conditions.append(
                    Q(~Exists(tiles_missing_match)) & has_at_least_one_tile
                )
                continue

            positive_facet = self.clause_compiler.facet_registry.get_positive_facet_for(
                operator_token, datatype_name
            )
            if positive_facet is not None:
                positive_expression, _ = self.clause_compiler.facet_registry.predicate(
                    datatype_name,
                    positive_facet.operator,
                    "value",
                    self.clause_compiler.operand_compiler.literal_values_only(
                        operand_items
                    ),
                )
                if isinstance(positive_expression, Q):
                    positive_matches_in_this_tile = (
                        rows_correlated_to_tile_resource.filter(
                            positive_expression
                        ).filter(tileid=OuterRef("tileid"))
                    )
                else:
                    positive_matches_in_this_tile = (
                        rows_correlated_to_tile_resource.filter(
                            **positive_expression
                        ).filter(tileid=OuterRef("tileid"))
                    )
            elif isinstance(predicate_expression, Q) and getattr(
                predicate_expression, "negated", False
            ):
                positive_matches_in_this_tile = rows_correlated_to_tile_resource.filter(
                    ~predicate_expression
                ).filter(tileid=OuterRef("tileid"))
            else:
                if isinstance(predicate_expression, Q):
                    positive_matches_in_this_tile = (
                        rows_correlated_to_tile_resource.exclude(
                            predicate_expression
                        ).filter(tileid=OuterRef("tileid"))
                    )
                else:
                    positive_matches_in_this_tile = (
                        rows_correlated_to_tile_resource.exclude(
                            **predicate_expression
                        ).filter(tileid=OuterRef("tileid"))
                    )

            tiles_with_violations = tiles_for_anchor_resource.filter(
                Exists(positive_matches_in_this_tile)
            )
            resource_level_conditions.append(
                Q(~Exists(tiles_with_violations)) & has_at_least_one_tile
            )

        if not per_tile_exists_conditions:
            any_expression = Q()
        else:
            if use_and_logic:
                tiles_requiring_all = tiles_for_anchor_resource
                for condition in per_tile_exists_conditions:
                    tiles_requiring_all = tiles_requiring_all.filter(condition)
                any_expression = Q(Exists(tiles_requiring_all))
            else:
                combined_any = Q(pk__in=[])
                for condition in per_tile_exists_conditions:
                    combined_any |= condition
                tiles_with_any = tiles_for_anchor_resource.filter(combined_any)
                any_expression = Q(Exists(tiles_with_any))

        if not resource_level_conditions:
            return any_expression

        if use_and_logic:
            combined_all = Q()
            for condition in resource_level_conditions:
                combined_all &= condition
            return any_expression & combined_all

        combined_or = Q()
        for condition in resource_level_conditions:
            combined_or |= condition
        return any_expression | combined_or

    def _apply_group_constraints(
        self,
        group_payload: Dict[str, Any],
        compiled_pair_info: Dict[str, Any],
        base_pairs: QuerySet,
        use_or_logic: bool,
    ) -> Tuple[QuerySet, bool]:
        constrained_child_pairs = base_pairs
        had_any_inner_filters = False
        child_id_field_name = compiled_pair_info["child_id_field"]

        if not use_or_logic:
            for child_group_payload in group_payload.get("groups") or []:
                if ((child_group_payload.get("relationship")) or {}).get("path"):
                    continue
                working_pairs = constrained_child_pairs
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
                        working_pairs, applied_here = (
                            self.relationship_compiler.filter_pairs_by_clause(
                                pairs_queryset=working_pairs,
                                clause_payload=clause_payload,
                                correlate_field=child_id_field_name,
                            )
                        )
                        had_any_inner_filters = had_any_inner_filters or applied_here
                    for nested_group_payload in node_payload.get("groups") or []:
                        pending_nodes.append(nested_group_payload)
                constrained_child_pairs = working_pairs

        else:
            or_q = Q(pk__in=[])
            saw_any_ok_rows = False

            for child_group_payload in group_payload.get("groups") or []:
                if ((child_group_payload.get("relationship")) or {}).get("path"):
                    continue

                ok_rows = self.relationship_compiler.child_ok_rows_from_literals(
                    child_group_payload, compiled_pair_info
                )
                if ok_rows is None:
                    continue

                or_q |= Q(Exists(ok_rows))
                saw_any_ok_rows = True
                had_any_inner_filters = True

            if saw_any_ok_rows:
                constrained_child_pairs = base_pairs.filter(or_q)

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
                        self.relationship_compiler.filter_pairs_by_clause(
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
                presence_implies_match_skip = (
                    self.clause_compiler.facet_registry.zero_arity_presence_is_match(
                        datatype_name_skip, operator_token
                    )
                )
                if presence_implies_match_skip:
                    continue

            related_exists_qs = self.relationship_compiler.related_child_exists_qs(
                related_clause_payload, compiled_pair_info
            )
            if related_exists_qs is None:
                continue

            if not has_operands:
                datatype_name = self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
                presence_implies_match = (
                    self.clause_compiler.facet_registry.zero_arity_presence_is_match(
                        datatype_name, operator_token
                    )
                )
                constrained_child_pairs = (
                    constrained_child_pairs.filter(Exists(related_exists_qs))
                    if presence_implies_match
                    else constrained_child_pairs.filter(~Exists(related_exists_qs))
                )
                had_any_inner_filters = True
            else:
                constrained_child_pairs = constrained_child_pairs.filter(
                    Exists(related_exists_qs)
                )
                had_any_inner_filters = True

        return constrained_child_pairs, had_any_inner_filters
