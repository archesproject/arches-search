from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet, Subquery
from arches.app.models import models as arches_models  # noqa: F401

from arches_search.utils.advanced_search.clause_compiler import ClauseCompiler
from arches_search.utils.advanced_search.path_navigator import PathNavigator


class GroupCompiler:
    def __init__(
        self, clause_compiler: ClauseCompiler, path_navigator: PathNavigator
    ) -> None:
        self.clause_compiler = clause_compiler
        self.path_navigator = self._require_path_navigator(path_navigator)

    def compile(
        self,
        group_payload: Dict[str, Any],
        anchor_graph_slug: str,
        current_context_side: str = "ANCHOR",
        relationship_context_for_parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Q, List[Exists]]:
        relationship_context = group_payload.get("relationship") or None
        has_relationship = bool(
            relationship_context and relationship_context.get("path")
        )

        if not has_relationship:
            relationshipless_q = self._compile_relationshipless_group_to_q(
                group_payload, anchor_graph_slug
            )
            if relationshipless_q is not None:
                return relationshipless_q, []

        exists_filters: List[Exists] = []
        compiled_pair_info: Optional[Dict[str, Any]] = None
        pairs_scoped_to_anchor: Optional[QuerySet] = None

        if has_relationship:
            compiled_pair_info, pairs_scoped_to_anchor = (
                self.path_navigator.build_relationship_pairs(relationship_context)
            )
            child_id_field = compiled_pair_info["child_id_field"]
            original_pairs_no_self = pairs_scoped_to_anchor.exclude(
                **{child_id_field: OuterRef("resourceinstanceid")}
            )

            matches_per_child, inner_filters_present = self._apply_group_constraints(
                group_payload=group_payload,
                compiled_pair_info=compiled_pair_info,
                base_pairs=original_pairs_no_self,
            )

            hop_info = self.path_navigator.normalize_relationship_context(
                relationship_context
            )
            hop_mode = hop_info["hop_quantifier"]
            is_inverse = hop_info["is_inverse"]
            path_segments = hop_info["path_segments"]
            inverse_single_hop = is_inverse and len(path_segments) == 1

            if is_inverse and len(path_segments) == 1:
                has_related_clause = any(
                    (clause.get("type") or "").upper() == "RELATED"
                    for clause in (group_payload.get("clauses") or [])
                )
                if has_related_clause and hop_mode == "ALL":
                    hop_mode = "ANY"

            if hop_mode == "ANY":
                exists_filters.append(Exists(matches_per_child))
            elif hop_mode == "NONE":
                if inner_filters_present:
                    exists_filters.append(
                        Exists(original_pairs_no_self) & ~Exists(matches_per_child)
                    )
                else:
                    exists_filters.append(~Exists(original_pairs_no_self))
            else:
                if inverse_single_hop:
                    child_ok_rows = self.path_navigator.child_ok_rows_from_literals(
                        group_payload, compiled_pair_info
                    )
                else:
                    child_ok_rows = None

                if inverse_single_hop and child_ok_rows is not None:
                    violator_rows = original_pairs_no_self.filter(
                        ~Exists(child_ok_rows)
                    )
                    all_expression = Exists(original_pairs_no_self) & ~Exists(
                        violator_rows
                    )
                    exists_filters.append(all_expression)
                else:
                    same_child_ok = matches_per_child.filter(
                        **{child_id_field: OuterRef(child_id_field)}
                    )
                    violator_rows = original_pairs_no_self.filter(
                        ~Exists(same_child_ok)
                    )
                    all_expression = Exists(original_pairs_no_self) & ~Exists(
                        violator_rows
                    )
                    exists_filters.append(all_expression)

        group_scope = (group_payload.get("scope") or "RESOURCE").upper()
        correlate_to_tile = group_scope == "TILE"

        for clause_payload in group_payload.get("clauses") or []:
            if (clause_payload.get("type") or "").upper() == "RELATED":
                continue
            exists_filters.append(
                self.clause_compiler.compile(
                    clause_payload,
                    anchor_graph_slug,
                    correlate_to_tile=correlate_to_tile,
                )
            )

        child_q_expression, child_exists_filters = self._compile_children(
            subgroups=(group_payload.get("groups") or []),
            anchor_graph_slug=anchor_graph_slug,
            parent_has_relationship=has_relationship,
            current_context_side=(
                "CHILD" if has_relationship else current_context_side
            ),
            relationship_context_for_parent=(
                compiled_pair_info
                if has_relationship
                else relationship_context_for_parent
            ),
        )

        group_logic = (group_payload.get("logic") or "AND").upper()
        combined_exists_filters: List[Exists] = [*exists_filters, *child_exists_filters]

        if group_logic == "OR":
            or_expression = (
                child_q_expression if child_q_expression is not None else Q()
            )
            for exists_piece in combined_exists_filters:
                or_expression = or_expression | Q(exists_piece)
            return or_expression, []

        and_expression = child_q_expression if child_q_expression is not None else Q()
        return and_expression, combined_exists_filters

    def _compile_children(
        self,
        subgroups: List[Dict[str, Any]],
        anchor_graph_slug: str,
        parent_has_relationship: bool,
        current_context_side: str,
        relationship_context_for_parent: Optional[Dict[str, Any]],
    ) -> Tuple[Q, List[Exists]]:
        combined_q_expression = Q()
        exists_filters: List[Exists] = []

        for subgroup_payload in subgroups:
            subgroup_has_relationship = bool(
                (subgroup_payload.get("relationship") or {}).get("path")
            )
            if parent_has_relationship and subgroup_has_relationship:
                continue

            subgroup_q_expression, subgroup_exists_filters = self.compile(
                group_payload=subgroup_payload,
                anchor_graph_slug=anchor_graph_slug,
                current_context_side=(
                    "CHILD"
                    if parent_has_relationship and not subgroup_has_relationship
                    else current_context_side
                ),
                relationship_context_for_parent=relationship_context_for_parent,
            )

            if (
                parent_has_relationship
                and not subgroup_has_relationship
                and current_context_side == "CHILD"
            ):
                continue

            combined_q_expression &= subgroup_q_expression
            exists_filters.extend(subgroup_exists_filters)

        return combined_q_expression, exists_filters

    def _compile_relationshipless_group_to_q(
        self, group_payload: Dict[str, Any], anchor_graph_slug: str
    ) -> Optional[Q]:
        if (group_payload.get("relationship") or {}).get("path"):
            return None

        logic = (group_payload.get("logic") or "AND").upper()
        if logic not in ("AND", "OR"):
            return None

        scope = (group_payload.get("scope") or "RESOURCE").upper()
        if scope == "TILE":
            return self.clause_compiler.compile_relationshipless_tile_group_to_q(
                group_payload=group_payload,
                anchor_graph_slug=anchor_graph_slug,
                logic=logic,
            )

        combined_q_expression = Q()
        has_any_piece = False

        for clause_payload in group_payload.get("clauses") or []:
            clause_q_expression = self.clause_compiler.compile_literal_to_q(
                clause_payload=clause_payload,
                anchor_graph_slug=anchor_graph_slug,
                scope="RESOURCE",
            )
            if clause_q_expression is None:
                return None
            combined_q_expression = (
                clause_q_expression
                if not has_any_piece
                else (
                    (combined_q_expression & clause_q_expression)
                    if logic == "AND"
                    else (combined_q_expression | clause_q_expression)
                )
            )
            has_any_piece = True

        for child_group_payload in group_payload.get("groups") or []:
            child_q_expression = self._compile_relationshipless_group_to_q(
                child_group_payload, anchor_graph_slug
            )
            if child_q_expression is None:
                return None
            combined_q_expression = (
                child_q_expression
                if not has_any_piece
                else (
                    (combined_q_expression & child_q_expression)
                    if logic == "AND"
                    else (combined_q_expression | child_q_expression)
                )
            )
            has_any_piece = True

        if not has_any_piece:
            return Q() if logic == "AND" else Q(pk__in=[])
        return combined_q_expression

    def _apply_group_constraints(
        self,
        group_payload: Dict[str, Any],
        compiled_pair_info: Dict[str, Any],
        base_pairs: QuerySet,
    ) -> Tuple[QuerySet, bool]:
        matches_per_child = base_pairs
        touched_any = False
        child_id_field = compiled_pair_info["child_id_field"]

        for child_group_payload in group_payload.get("groups") or []:
            if (child_group_payload.get("relationship") or {}).get("path"):
                continue
            if (child_group_payload.get("logic") or "AND").upper() != "AND":
                continue

            child_group_graph_slug = (
                child_group_payload.get("graph_slug") or ""
            ).strip()

            stack: List[Dict[str, Any]] = [child_group_payload]
            while stack:
                node_payload = stack.pop()
                if (node_payload.get("relationship") or {}).get("path"):
                    continue
                for clause_payload in node_payload.get("clauses") or []:
                    if (clause_payload.get("type") or "").upper() != "LITERAL":
                        continue
                    subject_path = clause_payload.get("subject") or []
                    subject_graph_slug, _subject_alias = (
                        subject_path[0] if subject_path else ("", "")
                    )
                    if (
                        child_group_graph_slug
                        and subject_graph_slug
                        and subject_graph_slug != child_group_graph_slug
                    ):
                        continue
                    matches_per_child, did_apply = (
                        self.clause_compiler.filter_pairs_by_clause(
                            pairs_queryset=matches_per_child,
                            clause_payload=clause_payload,
                            correlate_field=child_id_field,
                        )
                    )
                    touched_any = touched_any or did_apply
                for nested_group_payload in node_payload.get("groups") or []:
                    stack.append(nested_group_payload)

        nested_group_payload = next(
            (
                nested
                for nested in (group_payload.get("groups") or [])
                if ((nested.get("relationship") or {}).get("path"))
            ),
            None,
        )
        if nested_group_payload:
            nested_relationship = nested_group_payload.get("relationship") or {}
            nested_path = nested_relationship.get("path") or []
            if len(nested_path) == 1:
                nested_quantifier = (
                    (nested_relationship.get("traversal_quantifiers") or ["ANY"])[0]
                    or "ANY"
                ).upper()
                (
                    _datatype_ignore,
                    nested_terminal_graph,
                    nested_pairs,
                    nested_child_field,
                ) = self.path_navigator.build_scoped_pairs_for_path(
                    path_segments=nested_path,
                    is_inverse_relationship=bool(nested_relationship.get("is_inverse")),
                    correlate_on_field=child_id_field,
                )

                literal_clauses_all: List[Dict[str, Any]] = []
                stack_nested: List[Dict[str, Any]] = [nested_group_payload]
                while stack_nested:
                    node_payload = stack_nested.pop()
                    if not (node_payload.get("relationship") or {}).get("path"):
                        for clause_payload in node_payload.get("clauses") or []:
                            if (clause_payload.get("type") or "").upper() == "LITERAL":
                                literal_clauses_all.append(clause_payload)
                    for deeper_group_payload in node_payload.get("groups") or []:
                        stack_nested.append(deeper_group_payload)

                nested_literal_clauses = [
                    clause_payload
                    for clause_payload in literal_clauses_all
                    if ((clause_payload.get("subject") or [("", "")])[0])[0]
                    == nested_terminal_graph
                ]
                if not nested_literal_clauses:
                    filtered_literals: List[Dict[str, Any]] = []
                    for clause_payload in literal_clauses_all:
                        subject_path = clause_payload.get("subject") or []
                        subject_graph_slug, subject_alias = (
                            subject_path[0] if subject_path else ("", "")
                        )
                        if not subject_graph_slug:
                            continue
                        rows_model = self.clause_compiler.rows_for(
                            subject_graph_slug, subject_alias
                        )
                        if rows_model is not None:
                            filtered_literals.append(clause_payload)
                    nested_literal_clauses = filtered_literals

                nested_ok_pairs = nested_pairs
                for clause_payload in nested_literal_clauses:
                    nested_ok_pairs, did_apply = (
                        self.clause_compiler.filter_pairs_by_clause(
                            pairs_queryset=nested_ok_pairs,
                            clause_payload=clause_payload,
                            correlate_field=nested_child_field,
                        )
                    )
                    touched_any = touched_any or did_apply

                if nested_quantifier == "ANY":
                    matches_per_child = matches_per_child.filter(
                        Exists(nested_ok_pairs)
                    )
                    touched_any = True
                elif nested_quantifier == "NONE":
                    matches_per_child = matches_per_child.filter(
                        Exists(nested_pairs) & ~Exists(nested_ok_pairs)
                    )
                    touched_any = True
                else:
                    same_child_ok = nested_ok_pairs.filter(
                        **{nested_child_field: OuterRef(nested_child_field)}
                    )
                    violator_pairs = nested_pairs.filter(~Exists(same_child_ok))
                    matches_per_child = matches_per_child.filter(
                        Exists(nested_pairs) & ~Exists(violator_pairs)
                    )
                    touched_any = True

        terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]
        terminal_node_alias = compiled_pair_info["terminal_node_alias"]
        for related_clause_payload in group_payload.get("clauses") or []:
            if (related_clause_payload.get("type") or "").upper() != "RELATED":
                continue

            subject_path = related_clause_payload.get("subject") or []
            subject_graph_slug, subject_alias = (
                subject_path[0] if subject_path else ("", "")
            )
            operator_upper = (related_clause_payload.get("operator") or "").upper()
            has_operands = bool(related_clause_payload.get("operands"))

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
                    related_clause_payload.get("operator"),
                    "value",
                    [True],
                )
                is_negated_template = predicate_info[1]
                if operator_upper == "HAS_NO_VALUE":
                    matches_per_child = matches_per_child.filter(
                        ~Exists(related_exists_queryset)
                    )
                elif operator_upper == "HAS_ANY_VALUE":
                    matches_per_child = matches_per_child.filter(
                        Exists(related_exists_queryset)
                    )
                else:
                    matches_per_child = matches_per_child.filter(
                        ~Exists(related_exists_queryset)
                        if is_negated_template
                        else Exists(related_exists_queryset)
                    )
            else:
                matches_per_child = matches_per_child.filter(
                    Exists(related_exists_queryset)
                )
            touched_any = True

        return matches_per_child, touched_any

    def _require_path_navigator(self, path_navigator: PathNavigator) -> PathNavigator:
        if not hasattr(path_navigator, "search_model_registry") or not hasattr(
            path_navigator, "node_alias_datatype_registry"
        ):
            raise AttributeError(
                "PathNavigator must expose search_model_registry and node_alias_datatype_registry."
            )
        return path_navigator
