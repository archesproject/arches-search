# group_compiler.py
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

            hop_mode = (
                (relationship_context.get("traversal_quantifiers") or ["ANY"])[0]
                or "ANY"
            ).upper()

            # Normalize: inverse single-hop + RELATED present -> treat ALL as ANY
            if (
                relationship_context.get("is_inverse")
                and len((relationship_context.get("path") or [])) == 1
            ):
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
                    none_expression = Exists(original_pairs_no_self) & ~Exists(
                        matches_per_child
                    )
                    exists_filters.append(none_expression)
                else:
                    exists_filters.append(~Exists(original_pairs_no_self))

            else:
                # ALL
                is_inverse = bool(relationship_context.get("is_inverse"))
                path_segments = relationship_context.get("path") or []
                inverse_single_hop = is_inverse and len(path_segments) == 1

                def build_child_ok_rows_from_literals() -> Optional[QuerySet]:
                    terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]

                    literal_clauses: List[Dict[str, Any]] = []
                    for child_group_payload in group_payload.get("groups") or []:
                        if (child_group_payload.get("relationship") or {}).get("path"):
                            continue
                        if (child_group_payload.get("logic") or "AND").upper() != "AND":
                            return None

                        child_group_graph_slug = (
                            child_group_payload.get("graph_slug") or ""
                        ).strip()

                        stack: List[Dict[str, Any]] = [child_group_payload]
                        while stack:
                            node_payload = stack.pop()
                            if (node_payload.get("relationship") or {}).get("path"):
                                continue
                            for clause_payload in node_payload.get("clauses") or []:
                                if (
                                    clause_payload.get("type") or ""
                                ).upper() != "LITERAL":
                                    continue
                                subject_graph_slug, subject_alias = (
                                    self.clause_compiler._unpack_single_path(
                                        clause_payload.get("subject") or []
                                    )
                                )
                                if not subject_graph_slug or (
                                    child_group_graph_slug
                                    and subject_graph_slug != child_group_graph_slug
                                ):
                                    continue
                                if subject_graph_slug != terminal_graph_slug:
                                    return None
                                literal_clauses.append(clause_payload)
                            for nested_group_payload in (
                                node_payload.get("groups") or []
                            ):
                                stack.append(nested_group_payload)

                    if not literal_clauses:
                        return None

                    child_ok_rows: Optional[QuerySet] = None
                    for clause_payload in literal_clauses:
                        subject_graph_slug, subject_alias = (
                            self.clause_compiler._unpack_single_path(
                                clause_payload.get("subject") or []
                            )
                        )
                        subject_rows = self.clause_compiler._search_rows(
                            subject_graph_slug, subject_alias
                        )
                        if subject_rows is None:
                            continue

                        datatype_name = self.clause_compiler._datatype_for_alias(
                            subject_graph_slug, subject_alias
                        )
                        facet = self.clause_compiler._facet(
                            datatype_name, clause_payload.get("operator")
                        )
                        operand_items = clause_payload.get("operands") or []

                        correlated = subject_rows.filter(
                            resourceinstanceid=OuterRef(child_id_field)
                        ).order_by()

                        if not operand_items:
                            operator_upper = (
                                clause_payload.get("operator") or ""
                            ).upper()
                            is_negated_template = bool(
                                getattr(facet, "is_orm_template_negated", False)
                            )
                            if operator_upper == "HAS_NO_VALUE":
                                predicate_queryset = correlated.none()
                            elif operator_upper == "HAS_ANY_VALUE":
                                predicate_queryset = correlated
                            else:
                                predicate_queryset = (
                                    correlated.none()
                                    if is_negated_template
                                    else correlated
                                )
                        else:
                            predicate = self.clause_compiler._predicate_from_facet(
                                facet=facet,
                                column_name="value",
                                params=self.clause_compiler._literal_params(
                                    operand_items
                                ),
                            )
                            is_negated_template = bool(
                                getattr(facet, "is_orm_template_negated", False)
                            )
                            filtered = (
                                correlated.filter(predicate)
                                if isinstance(predicate, Q)
                                else correlated.filter(**predicate)
                            )
                            if not is_negated_template:
                                predicate_queryset = filtered
                            else:
                                positive_facet = None
                                facet_registry = getattr(
                                    self.clause_compiler, "facet_registry", None
                                )
                                if facet_registry and hasattr(
                                    facet_registry, "get_positive_facet_for"
                                ):
                                    positive_facet = (
                                        facet_registry.get_positive_facet_for(
                                            clause_payload.get("operator"),
                                            datatype_name,
                                        )
                                    )

                                if positive_facet is not None:
                                    positive_predicate = (
                                        self.clause_compiler._predicate_from_facet(
                                            facet=positive_facet,
                                            column_name="value",
                                            params=self.clause_compiler._literal_params(
                                                operand_items
                                            ),
                                        )
                                    )
                                    positive_filtered = (
                                        correlated.filter(positive_predicate)
                                        if isinstance(positive_predicate, Q)
                                        else correlated.filter(**positive_predicate)
                                    )
                                    predicate_queryset = correlated.exclude(
                                        pk__in=positive_filtered.values("pk")
                                    )
                                elif isinstance(predicate, Q) and getattr(
                                    predicate, "negated", False
                                ):
                                    predicate_queryset = correlated.exclude(
                                        pk__in=correlated.filter(~predicate).values(
                                            "pk"
                                        )
                                    )
                                else:
                                    predicate_queryset = correlated.exclude(
                                        pk__in=filtered.values("pk")
                                    )

                        child_ok_rows = (
                            predicate_queryset
                            if child_ok_rows is None
                            else child_ok_rows.filter(
                                pk__in=predicate_queryset.values("pk")
                            )
                        )

                    return child_ok_rows

                if inverse_single_hop:
                    child_ok_rows = build_child_ok_rows_from_literals()
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
            literal_exists_expression = self.clause_compiler.compile(
                clause_payload,
                anchor_graph_slug,
                correlate_to_tile=correlate_to_tile,
            )
            exists_filters.append(literal_exists_expression)

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
            return self._compile_relationshipless_tile_scoped_group_to_q(
                group_payload=group_payload,
                anchor_graph_slug=anchor_graph_slug,
                logic=logic,
            )

        combined_q_expression = Q()
        has_any_piece = False

        for clause_payload in group_payload.get("clauses") or []:
            clause_q_expression = self._q_for_relationshipless_in_graph_literal(
                clause_payload, anchor_graph_slug
            )
            if clause_q_expression is None:
                return None
            if not has_any_piece:
                combined_q_expression = clause_q_expression
            else:
                combined_q_expression = (
                    (combined_q_expression & clause_q_expression)
                    if logic == "AND"
                    else (combined_q_expression | clause_q_expression)
                )
            has_any_piece = True

        for child_group_payload in group_payload.get("groups") or []:
            child_q_expression = self._compile_relationshipless_group_to_q(
                child_group_payload, anchor_graph_slug
            )
            if child_q_expression is None:
                return None
            if not has_any_piece:
                combined_q_expression = child_q_expression
            else:
                combined_q_expression = (
                    (combined_q_expression & child_q_expression)
                    if logic == "AND"
                    else (combined_q_expression | child_q_expression)
                )
            has_any_piece = True

        if not has_any_piece:
            return Q() if logic == "AND" else Q(pk__in=[])
        return combined_q_expression

    def _compile_relationshipless_tile_scoped_group_to_q(
        self,
        *,
        group_payload: Dict[str, Any],
        anchor_graph_slug: str,
        logic: str,
    ) -> Q:
        clauses = group_payload.get("clauses") or []
        if not clauses:
            return Q()

        tileid_subqueries_for_any: List[Subquery] = []
        resource_level_conditions: List[Q] = []

        tiles_base = arches_models.Tile.objects.filter(
            resourceinstance_id=OuterRef("resourceinstanceid")
        ).order_by()

        for clause_index, clause_payload in enumerate(clauses, start=1):
            subject_graph_slug, subject_alias = (
                self.clause_compiler._unpack_single_path(
                    clause_payload.get("subject") or []
                )
            )
            if subject_graph_slug != anchor_graph_slug:
                empty_tile_subquery = arches_models.Tile.objects.none().values(
                    "tileid"
                )[:1]
                tileid_subqueries_for_any.append(Subquery(empty_tile_subquery))
                continue

            subject_rows = self.clause_compiler._search_rows(
                subject_graph_slug, subject_alias
            )
            if subject_rows is None:
                empty_tile_subquery = arches_models.Tile.objects.none().values(
                    "tileid"
                )[:1]
                tileid_subqueries_for_any.append(Subquery(empty_tile_subquery))
                continue

            datatype_name = self.clause_compiler._datatype_for_alias(
                subject_graph_slug, subject_alias
            )
            facet = self.clause_compiler._facet(
                datatype_name, clause_payload.get("operator")
            )
            operator_upper = (clause_payload.get("operator") or "").upper()
            operand_items = clause_payload.get("operands") or []
            is_negated_template = bool(getattr(facet, "is_orm_template_negated", False))
            quantifier = (clause_payload.get("quantifier") or "ANY").upper()
            if quantifier not in ("ANY", "ALL", "NONE"):
                quantifier = "ANY"

            subject_rows_correlated_to_tile = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstance_id")
            ).order_by()

            subject_rows_correlated_to_resource = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            ).order_by()

            if not operand_items:
                if operator_upper == "HAS_NO_VALUE":
                    matches_rows_tile = subject_rows_correlated_to_tile.none()
                    matches_rows_resource = subject_rows_correlated_to_resource.none()
                elif operator_upper == "HAS_ANY_VALUE":
                    matches_rows_tile = subject_rows_correlated_to_tile
                    matches_rows_resource = subject_rows_correlated_to_resource
                else:
                    matches_rows_tile = (
                        subject_rows_correlated_to_tile.none()
                        if is_negated_template
                        else subject_rows_correlated_to_tile
                    )
                    matches_rows_resource = (
                        subject_rows_correlated_to_resource.none()
                        if is_negated_template
                        else subject_rows_correlated_to_resource
                    )
            else:
                params = self.clause_compiler._literal_params(operand_items)
                predicate = self.clause_compiler._predicate_from_facet(
                    facet=facet, column_name="value", params=params
                )
                matches_rows_tile = (
                    subject_rows_correlated_to_tile.filter(predicate)
                    if isinstance(predicate, Q)
                    else subject_rows_correlated_to_tile.filter(**predicate)
                )
                matches_rows_resource = (
                    subject_rows_correlated_to_resource.filter(predicate)
                    if isinstance(predicate, Q)
                    else subject_rows_correlated_to_resource.filter(**predicate)
                )

            matches_on_tile = matches_rows_tile.filter(tileid=OuterRef("tileid"))

            if quantifier == "ANY":
                if not is_negated_template:
                    subquery_this_tile_if_match = matches_on_tile.values("tileid")[:1]
                    tileid_subqueries_for_any.append(
                        Subquery(subquery_this_tile_if_match)
                    )
                else:
                    this_tile_no_match = (
                        arches_models.Tile.objects.filter(tileid=OuterRef("tileid"))
                        .filter(~Exists(matches_on_tile))
                        .values("tileid")[:1]
                    )
                    tileid_subqueries_for_any.append(Subquery(this_tile_no_match))

            elif quantifier == "NONE":
                resource_level_conditions.append(Q(~Exists(matches_rows_resource)))

            else:
                # ALL
                if not is_negated_template:
                    tiles_without_match = tiles_base.filter(
                        ~Exists(matches_on_tile)
                    ).values("tileid")
                    resource_condition = Q(
                        ~Exists(
                            tiles_base.filter(
                                tileid__in=Subquery(tiles_without_match)
                            ).values("tileid")[:1]
                        )
                    ) & Q(Exists(tiles_base.values("tileid")[:1]))
                    resource_level_conditions.append(resource_condition)
                else:
                    params = self.clause_compiler._literal_params(operand_items)
                    positive_facet = None
                    facet_registry = getattr(
                        self.clause_compiler, "facet_registry", None
                    )
                    if facet_registry and hasattr(
                        facet_registry, "get_positive_facet_for"
                    ):
                        positive_facet = facet_registry.get_positive_facet_for(
                            clause_payload.get("operator"), datatype_name
                        )

                    if positive_facet is not None:
                        positive_predicate = self.clause_compiler._predicate_from_facet(
                            facet=positive_facet, column_name="value", params=params
                        )
                        positive_matches_resource = (
                            subject_rows_correlated_to_resource.filter(
                                positive_predicate
                            )
                            if isinstance(positive_predicate, Q)
                            else subject_rows_correlated_to_resource.filter(
                                **positive_predicate
                            )
                        )
                    else:
                        positive_matches_resource = (
                            subject_rows_correlated_to_resource.exclude(
                                pk__in=matches_rows_resource.values("pk")
                            )
                        )

                    resource_condition = Q(~Exists(positive_matches_resource)) & Q(
                        Exists(tiles_base.values("tileid")[:1])
                    )
                    resource_level_conditions.append(resource_condition)

        if tileid_subqueries_for_any:
            if logic.upper() == "AND":
                combined_tiles_queryset = tiles_base
                for subquery_item in tileid_subqueries_for_any:
                    combined_tiles_queryset = combined_tiles_queryset.filter(
                        tileid__in=subquery_item
                    )
                any_exists_expression = Q(
                    Exists(combined_tiles_queryset.values("tileid")[:1])
                )
            else:
                or_expression = Q(pk__in=[])
                for subquery_item in tileid_subqueries_for_any:
                    or_expression = or_expression | Q(tileid__in=subquery_item)
                any_exists_expression = Q(
                    Exists(tiles_base.filter(or_expression).values("tileid")[:1])
                )
        else:
            any_exists_expression = Q()

        if resource_level_conditions:
            if logic.upper() == "AND":
                resource_expression = Q()
                for condition_expression in resource_level_conditions:
                    resource_expression &= condition_expression
                final_expression = any_exists_expression & resource_expression
            else:
                resource_expression = Q()
                for condition_expression in resource_level_conditions:
                    resource_expression |= condition_expression
                final_expression = any_exists_expression | resource_expression
            return final_expression

        return any_exists_expression

    def _q_for_relationshipless_in_graph_literal(
        self, clause_payload: Dict[str, Any], anchor_graph_slug: str
    ) -> Optional[Q]:
        if (clause_payload.get("type") or "").upper() != "LITERAL":
            return None

        subject_graph_slug, subject_alias = self.clause_compiler._unpack_single_path(
            clause_payload.get("subject") or []
        )
        if subject_graph_slug != anchor_graph_slug:
            return Q(pk__in=[])

        subject_rows = self.clause_compiler._search_rows(
            subject_graph_slug, subject_alias
        )
        if subject_rows is None:
            return Q(pk__in=[])

        datatype_name = self.clause_compiler._datatype_for_alias(
            subject_graph_slug, subject_alias
        )
        facet = self.clause_compiler._facet(
            datatype_name, clause_payload.get("operator")
        )
        operator_upper = (clause_payload.get("operator") or "").upper()
        operand_items = clause_payload.get("operands") or []
        is_negated_template = bool(getattr(facet, "is_orm_template_negated", False))

        quantifier = (clause_payload.get("quantifier") or "ANY").upper()
        if quantifier not in ("ANY", "ALL", "NONE"):
            quantifier = "ANY"

        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstanceid")
        ).order_by()

        if not operand_items:
            if operator_upper == "HAS_NO_VALUE":
                return (
                    Q(~Exists(correlated_rows))
                    if quantifier in ("ANY", "ALL")
                    else Q(Exists(correlated_rows))
                )
            if operator_upper == "HAS_ANY_VALUE":
                return (
                    Q(Exists(correlated_rows))
                    if quantifier in ("ANY", "ALL")
                    else Q(~Exists(correlated_rows))
                )
            if not is_negated_template:
                return (
                    Q(Exists(correlated_rows))
                    if quantifier in ("ANY", "ALL")
                    else Q(~Exists(correlated_rows))
                )
            return (
                Q(~Exists(correlated_rows))
                if quantifier in ("ANY", "ALL")
                else Q(Exists(correlated_rows))
            )

        params = self.clause_compiler._literal_params(operand_items)
        raw_predicate = self.clause_compiler._predicate_from_facet(
            facet=facet, column_name="value", params=params
        )

        matches = (
            correlated_rows.filter(raw_predicate)
            if isinstance(raw_predicate, Q)
            else correlated_rows.filter(**raw_predicate)
        )

        if not is_negated_template:
            violators = correlated_rows.exclude(pk__in=matches.values("pk"))
        else:
            positive_facet = None
            facet_registry = getattr(self.clause_compiler, "facet_registry", None)
            if facet_registry and hasattr(facet_registry, "get_positive_facet_for"):
                positive_facet = facet_registry.get_positive_facet_for(
                    clause_payload.get("operator"), datatype_name
                )

            if positive_facet is not None:
                positive_predicate = self.clause_compiler._predicate_from_facet(
                    facet=positive_facet, column_name="value", params=params
                )
                violators = (
                    correlated_rows.filter(positive_predicate)
                    if isinstance(positive_predicate, Q)
                    else correlated_rows.filter(**positive_predicate)
                )
            elif isinstance(raw_predicate, Q) and getattr(
                raw_predicate, "negated", False
            ):
                violators = correlated_rows.filter(~raw_predicate)
            else:
                violators = correlated_rows.exclude(pk__in=matches.values("pk"))

        if quantifier == "ANY":
            return Q(Exists(matches))
        if quantifier == "NONE":
            return Q(~Exists(matches))
        return Q(Exists(correlated_rows) & ~Exists(violators))

    def _apply_group_constraints(
        self,
        group_payload: Dict[str, Any],
        compiled_pair_info: Dict[str, Any],
        base_pairs: QuerySet,
    ) -> Tuple[QuerySet, bool]:
        """
        Push constraints from relationship-less AND child groups and one nested leg (single hop)
        down onto the leg's pairs queryset. Also handle RELATED clauses aimed at the terminal child.
        """
        matches_per_child = base_pairs
        touched_any = False

        child_id_field = compiled_pair_info["child_id_field"]

        def apply_literal_clause_to_pairs(
            pairs_queryset: QuerySet,
            clause_payload: Dict[str, Any],
            correlate_field: str,
        ) -> Tuple[QuerySet, bool]:
            subject_graph_slug, subject_alias = (
                self.clause_compiler._unpack_single_path(
                    clause_payload.get("subject") or []
                )
            )
            subject_rows = self.clause_compiler._search_rows(
                subject_graph_slug, subject_alias
            )
            if subject_rows is None:
                return pairs_queryset, False

            datatype_name = self.clause_compiler._datatype_for_alias(
                subject_graph_slug, subject_alias
            )
            facet = self.clause_compiler._facet(
                datatype_name, clause_payload.get("operator")
            )
            operand_items = clause_payload.get("operands") or []
            correlated = subject_rows.filter(
                resourceinstanceid=OuterRef(correlate_field)
            ).order_by()

            if not operand_items:
                operator_upper = (clause_payload.get("operator") or "").upper()
                if operator_upper == "HAS_NO_VALUE":
                    return pairs_queryset.filter(~Exists(correlated)), True
                if operator_upper == "HAS_ANY_VALUE":
                    return pairs_queryset.filter(Exists(correlated)), True
                is_negated_template = bool(
                    getattr(facet, "is_orm_template_negated", False)
                )
                return (
                    pairs_queryset.filter(~Exists(correlated))
                    if is_negated_template
                    else pairs_queryset.filter(Exists(correlated))
                ), True

            predicate = self.clause_compiler._predicate_from_facet(
                facet=facet,
                column_name="value",
                params=self.clause_compiler._literal_params(operand_items),
            )
            is_negated_template = bool(getattr(facet, "is_orm_template_negated", False))
            filtered = (
                correlated.filter(predicate)
                if isinstance(predicate, Q)
                else correlated.filter(**predicate)
            )

            if not is_negated_template:
                return pairs_queryset.filter(Exists(filtered)), True

            positive_facet = None
            facet_registry = getattr(self.clause_compiler, "facet_registry", None)
            if facet_registry and hasattr(facet_registry, "get_positive_facet_for"):
                positive_facet = facet_registry.get_positive_facet_for(
                    clause_payload.get("operator"), datatype_name
                )

            if positive_facet is not None:
                positive_predicate = self.clause_compiler._predicate_from_facet(
                    facet=positive_facet,
                    column_name="value",
                    params=self.clause_compiler._literal_params(operand_items),
                )
                positive_filtered = (
                    correlated.filter(positive_predicate)
                    if isinstance(positive_predicate, Q)
                    else correlated.filter(**positive_predicate)
                )
                return pairs_queryset.filter(~Exists(positive_filtered)), True

            if isinstance(predicate, Q) and getattr(predicate, "negated", False):
                return (
                    pairs_queryset.filter(~Exists(correlated.filter(~predicate))),
                    True,
                )

            return pairs_queryset.filter(~Exists(filtered)), True

        # 1) Relationship-less AND child groups
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
                    subject_graph_slug, _subject_alias = (
                        self.clause_compiler._unpack_single_path(
                            clause_payload.get("subject") or []
                        )
                    )
                    if (
                        child_group_graph_slug
                        and subject_graph_slug
                        and subject_graph_slug != child_group_graph_slug
                    ):
                        continue
                    matches_per_child, did_apply = apply_literal_clause_to_pairs(
                        matches_per_child, clause_payload, child_id_field
                    )
                    touched_any = touched_any or did_apply
                for nested_group_payload in node_payload.get("groups") or []:
                    stack.append(nested_group_payload)

        # 2) One nested leg (single hop) directly under this relationship-bearing group
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
                    if self.clause_compiler._unpack_single_path(
                        clause_payload.get("subject") or []
                    )[0]
                    == nested_terminal_graph
                ]
                if not nested_literal_clauses:
                    filtered_literals: List[Dict[str, Any]] = []
                    for clause_payload in literal_clauses_all:
                        subject_graph_slug, subject_alias = (
                            self.clause_compiler._unpack_single_path(
                                clause_payload.get("subject") or []
                            )
                        )
                        if not subject_graph_slug:
                            continue
                        rows_model = self.clause_compiler._search_rows(
                            subject_graph_slug, subject_alias
                        )
                        if rows_model is not None:
                            filtered_literals.append(clause_payload)
                    nested_literal_clauses = filtered_literals

                nested_ok_pairs = nested_pairs
                for clause_payload in nested_literal_clauses:
                    nested_ok_pairs, did_apply = apply_literal_clause_to_pairs(
                        nested_ok_pairs, clause_payload, nested_child_field
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

        # 3) RELATED clauses aimed at the terminal child
        terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]
        terminal_node_alias = compiled_pair_info["terminal_node_alias"]
        for related_clause_payload in group_payload.get("clauses") or []:
            if (related_clause_payload.get("type") or "").upper() != "RELATED":
                continue

            subject_graph_slug, subject_alias = (
                self.clause_compiler._unpack_single_path(
                    related_clause_payload.get("subject") or []
                )
            )
            operator_upper = (related_clause_payload.get("operator") or "").upper()
            has_operands = bool(related_clause_payload.get("operands"))

            # Skip trivial HAS_ANY_VALUE on the terminal node (leg existence already enforces it)
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
                facet = self.clause_compiler._facet(
                    self.clause_compiler._datatype_for_alias(
                        subject_graph_slug, subject_alias
                    ),
                    related_clause_payload.get("operator"),
                )
                is_negated_template = bool(
                    getattr(facet, "is_orm_template_negated", False)
                )
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
