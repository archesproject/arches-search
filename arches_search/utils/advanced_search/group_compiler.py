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
        def _dbg_qs(label: str, queryset: Optional[QuerySet]) -> None:
            try:
                if queryset is None:
                    print(f"[ADV][DBG] {label}: <None>")
                    return
                print(f"[ADV][DBG] {label}.model={getattr(queryset, 'model', None)}")
                print(
                    f"[ADV][DBG] {label}: <unavailable> (This queryset contains a reference to an outer query and may only be used in a subquery.)"
                )
            except Exception as exc:
                print(f"[ADV][DBG] {label}: <unavailable> ({exc})")

        def _dbg_exists(label: str, queryset: QuerySet) -> None:
            _dbg_qs(f"{label} (Exists subquery)", queryset)

        relationship_context = group_payload.get("relationship") or None
        has_relationship = bool(
            relationship_context and relationship_context.get("path")
        )

        if not has_relationship:
            q_for_leaf = self._compile_relationshipless_group_to_q(
                group_payload, anchor_graph_slug
            )
            if q_for_leaf is not None:
                print("[ADV][DBG] relationshipless group -> returning Q only")
                return q_for_leaf, []

        exists_filters: List[Exists] = []
        compiled_pair_info: Optional[Dict[str, Any]] = None
        pairs_scoped_to_anchor: Optional[QuerySet] = None

        if has_relationship:
            compiled_pair_info, pairs_scoped_to_anchor = (
                self.path_navigator.build_relationship_pairs(relationship_context)
            )
            _dbg_qs("[ADV][DBG] pairs_scoped_to_anchor", pairs_scoped_to_anchor)

            child_id_field = compiled_pair_info["child_id_field"]
            original_pairs_no_self = pairs_scoped_to_anchor.exclude(
                **{child_id_field: OuterRef("resourceinstanceid")}
            )
            _dbg_qs("[ADV][DBG] base_pairs_no_self", original_pairs_no_self)

            matches_per_child, inner_filters_present = self._apply_group_constraints(
                group_payload=group_payload,
                compiled_pair_info=compiled_pair_info,
                base_pairs=original_pairs_no_self,
            )
            _dbg_qs("[ADV][DBG] matches_per_child", matches_per_child)

            hop_mode = (
                (relationship_context.get("hop_modes") or ["ANY"])[0] or "ANY"
            ).upper()

            # ---------- NORMALIZE: inverse single-hop + RELATED present -> ALL behaves like ANY ----------
            if (
                relationship_context.get("is_inverse")
                and len((relationship_context.get("path") or [])) == 1
            ):
                has_related_clause = any(
                    (c.get("type") or "").upper() == "RELATED"
                    for c in (group_payload.get("clauses") or [])
                )
                if has_related_clause and hop_mode == "ALL":
                    print(
                        "[ADV][DBG] normalize: ALL -> ANY on inverse single-hop with RELATED"
                    )
                    hop_mode = "ANY"
            # ---------------------------------------------------------------------------------------------

            if hop_mode == "ANY":
                _dbg_exists(
                    "[ADV][DBG] ANY -> exists(matches_per_child)", matches_per_child
                )
                exists_filters.append(Exists(matches_per_child))

            elif hop_mode == "NONE":
                if inner_filters_present:
                    none_q_expression = Exists(original_pairs_no_self) & ~Exists(
                        matches_per_child
                    )
                    print(
                        "[ADV][DBG] NONE (constrained) -> Exists(base_pairs) & ~Exists(matches_per_child)"
                    )
                    exists_filters.append(none_q_expression)
                else:
                    none_q_expression = ~Exists(original_pairs_no_self)
                    print("[ADV][DBG] NONE (no inner filters) -> ~Exists(base_pairs)")
                    exists_filters.append(none_q_expression)

            else:
                # -------------------------- ALL --------------------------
                # Fast-path: inverse single-hop + child LITERALs only.
                # Build "ok child" directly from the child's search rows so violators
                # don’t re-walk the UUID leg.
                is_inverse = bool(relationship_context.get("is_inverse"))
                path_segments = relationship_context.get("path") or []
                inverse_single_hop = is_inverse and len(path_segments) == 1

                def _child_ok_rows_from_literals() -> Optional[QuerySet]:
                    """
                    If the immediate relationship-less AND child groups constrain ONLY the child graph
                    via LITERALs, build a correlated child-rows queryset:
                        rows.filter(resourceinstanceid=OuterRef(child_id_field)).filter(<AND of predicates>)
                    Return None if we can’t safely build it.
                    """
                    term_graph = compiled_pair_info["terminal_graph_slug"]

                    # Gather LITERALs from immediate relationship-less AND child groups, gated by their graph_slug
                    literals: List[Dict[str, Any]] = []
                    for child in group_payload.get("groups") or []:
                        if (child.get("relationship") or {}).get("path"):
                            continue
                        if (child.get("logic") or "AND").upper() != "AND":
                            return None  # not safe to AND-fold
                        child_graph_slug = (child.get("graph_slug") or "").strip()

                        stack = [child]
                        while stack:
                            node = stack.pop()
                            if (node.get("relationship") or {}).get("path"):
                                continue
                            for clause in node.get("clauses") or []:
                                if (clause.get("type") or "").upper() != "LITERAL":
                                    continue
                                sg, sa = self.clause_compiler._unpack_single_path(
                                    clause.get("subject") or []
                                )
                                if not sg or (
                                    child_graph_slug and sg != child_graph_slug
                                ):
                                    continue
                                if sg != term_graph:
                                    return None  # contains non-child-graph literals → bail out
                                literals.append(clause)
                            for g in node.get("groups") or []:
                                stack.append(g)

                    if not literals:
                        return None

                    # Build the child rows with all predicates AND-ed
                    child_rows: Optional[QuerySet] = None
                    for clause in literals:
                        sg, sa = self.clause_compiler._unpack_single_path(
                            clause.get("subject") or []
                        )
                        rows = self.clause_compiler._search_rows(sg, sa)
                        if rows is None:
                            # skip rather than fail; if we skip everything, return None
                            continue
                        dtype = self.clause_compiler._datatype_for_alias(sg, sa)
                        facet = self.clause_compiler._facet(
                            dtype, clause.get("operator")
                        )
                        ops = clause.get("operands") or []

                        correlated = rows.filter(
                            resourceinstanceid=OuterRef(child_id_field)
                        ).order_by()

                        if not ops:
                            op_upper = (clause.get("operator") or "").upper()
                            is_neg = bool(
                                getattr(facet, "is_orm_template_negated", False)
                            )
                            if op_upper == "HAS_NO_VALUE":
                                pred_qs = correlated.none()
                            elif op_upper == "HAS_ANY_VALUE":
                                pred_qs = correlated
                            else:
                                pred_qs = correlated.none() if is_neg else correlated
                        else:
                            pred = self.clause_compiler._predicate_from_facet(
                                facet=facet,
                                column_name="value",
                                params=self.clause_compiler._literal_params(ops),
                            )
                            is_neg = bool(
                                getattr(facet, "is_orm_template_negated", False)
                            )
                            filt = (
                                correlated.filter(pred)
                                if isinstance(pred, Q)
                                else correlated.filter(**pred)
                            )
                            if not is_neg:
                                pred_qs = filt
                            else:
                                pos_facet = self._positive_facet_for(
                                    dtype, clause.get("operator")
                                )
                                if pos_facet is not None:
                                    pos_pred = (
                                        self.clause_compiler._predicate_from_facet(
                                            facet=pos_facet,
                                            column_name="value",
                                            params=self.clause_compiler._literal_params(
                                                ops
                                            ),
                                        )
                                    )
                                    pos_filt = (
                                        correlated.filter(pos_pred)
                                        if isinstance(pos_pred, Q)
                                        else correlated.filter(**pos_pred)
                                    )
                                    pred_qs = correlated.exclude(
                                        pk__in=pos_filt.values("pk")
                                    )
                                elif isinstance(pred, Q) and getattr(
                                    pred, "negated", False
                                ):
                                    pred_qs = correlated.exclude(
                                        pk__in=correlated.filter(~pred).values("pk")
                                    )
                                else:
                                    pred_qs = correlated.exclude(
                                        pk__in=filt.values("pk")
                                    )

                        # AND-fold by successive filters on the same base rows
                        child_rows = (
                            pred_qs
                            if child_rows is None
                            else child_rows.filter(pk__in=pred_qs.values("pk"))
                        )

                    return child_rows

                if inverse_single_hop:
                    child_ok_rows = _child_ok_rows_from_literals()
                else:
                    child_ok_rows = None

                if inverse_single_hop and child_ok_rows is not None:
                    # ALL = has any child AND no violator child (child that fails predicates)
                    violators = original_pairs_no_self.filter(~Exists(child_ok_rows))
                    _dbg_exists(
                        "[ADV][DBG] ALL (fast inverse single-hop) -> violators",
                        violators,
                    )
                    all_q_expression = Exists(original_pairs_no_self) & ~Exists(
                        violators
                    )
                    exists_filters.append(all_q_expression)
                else:
                    # General ALL (multi-child universal) using matches_per_child
                    same_child_ok = matches_per_child.filter(
                        **{child_id_field: OuterRef(child_id_field)}
                    )
                    violators = original_pairs_no_self.filter(~Exists(same_child_ok))
                    _dbg_exists("[ADV][DBG] ALL -> violators", violators)
                    all_q_expression = Exists(original_pairs_no_self) & ~Exists(
                        violators
                    )
                    exists_filters.append(all_q_expression)
                # ------------------------ /ALL --------------------------

        group_scope = (group_payload.get("scope") or "RESOURCE").upper()
        correlate_to_tile = group_scope == "TILE"

        for clause_payload in group_payload.get("clauses") or []:
            if (clause_payload.get("type") or "").upper() == "RELATED":
                continue
            exists_expression = self.clause_compiler.compile(
                clause_payload,
                anchor_graph_slug,
                correlate_to_tile=correlate_to_tile,
            )
            print(
                f"[ADV][DBG] top-level literal -> Exists added (op={clause_payload.get('operator')})"
            )
            exists_filters.append(exists_expression)

        child_q, child_exists_filters = self._compile_children(
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
            or_q = child_q if child_q is not None else Q()
            for exists_piece in combined_exists_filters:
                or_q = or_q | Q(exists_piece)
            return or_q, []

        and_q = child_q if child_q is not None else Q()
        return and_q, combined_exists_filters

    def _compile_children(
        self,
        subgroups: List[Dict[str, Any]],
        anchor_graph_slug: str,
        parent_has_relationship: bool,
        current_context_side: str,
        relationship_context_for_parent: Optional[Dict[str, Any]],
    ) -> Tuple[Q, List[Exists]]:
        combined_q = Q()
        exists_filters: List[Exists] = []
        for subgroup_payload in subgroups:
            subgroup_has_relationship = bool(
                (subgroup_payload.get("relationship") or {}).get("path")
            )
            if parent_has_relationship and subgroup_has_relationship:
                continue

            subgroup_q, subgroup_exists = self.compile(
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

            combined_q &= subgroup_q
            exists_filters.extend(subgroup_exists)

        return combined_q, exists_filters

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

        combined_q = Q()
        has_any_piece = False

        for clause_payload in group_payload.get("clauses") or []:
            clause_q = self._q_for_relationshipless_in_graph_literal(
                clause_payload, anchor_graph_slug
            )
            if clause_q is None:
                return None
            if not has_any_piece:
                combined_q = clause_q
            else:
                combined_q = (
                    (combined_q & clause_q)
                    if logic == "AND"
                    else (combined_q | clause_q)
                )
            has_any_piece = True

        for child_payload in group_payload.get("groups") or []:
            child_q = self._compile_relationshipless_group_to_q(
                child_payload, anchor_graph_slug
            )
            if child_q is None:
                return None
            if not has_any_piece:
                combined_q = child_q
            else:
                combined_q = (
                    (combined_q & child_q) if logic == "AND" else (combined_q | child_q)
                )
            has_any_piece = True

        if not has_any_piece:
            return Q() if logic == "AND" else Q(pk__in=[])
        return combined_q

    def _compile_relationshipless_tile_scoped_group_to_q(
        self,
        *,
        group_payload: Dict[str, Any],
        anchor_graph_slug: str,
        logic: str,
    ) -> Q:
        clauses = group_payload.get("clauses") or []
        if not clauses:
            print("[ADV][GRP][TILE] no clauses -> Q()")
            return Q()

        print(f"[ADV][GRP][TILE] begin logic={logic} clauses={len(clauses)}")

        from django.db.models import Subquery, Exists

        tileid_subqueries_for_any: List[Subquery] = []
        resource_level_conditions: List[Q] = []

        tiles_base = arches_models.Tile.objects.filter(
            resourceinstance_id=OuterRef("resourceinstanceid")
        ).order_by()

        for index, clause_payload in enumerate(clauses, start=1):
            subject_graph_slug, subject_alias = (
                self.clause_compiler._unpack_single_path(
                    clause_payload.get("subject") or []
                )
            )
            if subject_graph_slug != anchor_graph_slug:
                print(
                    f"[ADV][GRP][TILE][{index}] wrong graph on subject ({subject_graph_slug} != {anchor_graph_slug}) -> FALSE subquery"
                )
                empty = arches_models.Tile.objects.none().values("tileid")[:1]
                tileid_subqueries_for_any.append(Subquery(empty))
                continue

            subject_rows = self.clause_compiler._search_rows(
                subject_graph_slug, subject_alias
            )
            if subject_rows is None:
                print(
                    f"[ADV][GRP][TILE][{index}] no search rows model for {subject_graph_slug}.{subject_alias} -> FALSE subquery"
                )
                empty = arches_models.Tile.objects.none().values("tileid")[:1]
                tileid_subqueries_for_any.append(Subquery(empty))
                continue

            datatype_name = self.clause_compiler._datatype_for_alias(
                subject_graph_slug, subject_alias
            )
            facet = self.clause_compiler._facet(
                datatype_name, clause_payload.get("operator")
            )
            operator_upper = (clause_payload.get("operator") or "").upper()
            operands = clause_payload.get("operands") or []
            is_negated_template = bool(getattr(facet, "is_orm_template_negated", False))
            quantifier = (clause_payload.get("quantifier") or "ANY").upper()
            if quantifier not in ("ANY", "ALL", "NONE"):
                quantifier = "ANY"

            print(
                f"[ADV][GRP][TILE][{index}] op={operator_upper} alias={subject_alias} "
                f"quantifier={quantifier} orm_template={getattr(facet,'orm_template',None)} "
                f"facet.neg={is_negated_template} ops={len(operands)}"
            )

            subject_rows_correlated_to_tile = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstance_id")
            ).order_by()

            subject_rows_correlated_to_resource = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            ).order_by()

            if not operands:
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
                params = self.clause_compiler._literal_params(operands)
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
                    subq_this_tile_if_match = matches_on_tile.values("tileid")[:1]
                    tileid_subqueries_for_any.append(Subquery(subq_this_tile_if_match))
                    print(
                        f"[ADV][GRP][TILE][{index}] ANY + POS -> tileids(this tile if match)"
                    )
                else:
                    this_tile_no_match = (
                        arches_models.Tile.objects.filter(tileid=OuterRef("tileid"))
                        .filter(~Exists(matches_on_tile))
                        .values("tileid")[:1]
                    )
                    tileid_subqueries_for_any.append(Subquery(this_tile_no_match))
                    print(
                        f"[ADV][GRP][TILE][{index}] ANY + NEG -> tileids(this tile if no match)"
                    )

            elif quantifier == "NONE":
                resource_condition = Q(~Exists(matches_rows_resource))
                resource_level_conditions.append(resource_condition)
                print(
                    f"[ADV][GRP][TILE][{index}] NONE -> resource-level ~Exists(matches_rows_resource)"
                )

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
                    print(
                        f"[ADV][GRP][TILE][{index}] ALL + POS -> resource-level no tile without match (and has tiles)"
                    )
                else:
                    # FIX: for ALL + NEG, assert there are NO POSITIVE matches anywhere (and has tiles).
                    # Prefer the facet registry's positive counterpart; otherwise derive by complement.
                    params = self.clause_compiler._literal_params(operands)
                    positive_facet = self._positive_facet_for(
                        datatype_name, clause_payload.get("operator")
                    )
                    if positive_facet is not None:
                        pos_predicate = self.clause_compiler._predicate_from_facet(
                            facet=positive_facet, column_name="value", params=params
                        )
                        positive_matches_resource = (
                            subject_rows_correlated_to_resource.filter(pos_predicate)
                            if isinstance(pos_predicate, Q)
                            else subject_rows_correlated_to_resource.filter(
                                **pos_predicate
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
                    print(
                        f"[ADV][GRP][TILE][{index}] ALL + NEG -> resource-level no POSITIVE matches (and has tiles)"
                    )

        if tileid_subqueries_for_any:
            if logic.upper() == "AND":
                combined_tiles = tiles_base
                for idx, subquery in enumerate(tileid_subqueries_for_any, start=1):
                    combined_tiles = combined_tiles.filter(tileid__in=subquery)
                    print(f"[ADV][GRP][TILE] AND intersect with subquery[{idx}]")
                any_exists_q = Q(Exists(combined_tiles.values("tileid")[:1]))
            else:
                or_q = Q(pk__in=[])
                for idx, subquery in enumerate(tileid_subqueries_for_any, start=1):
                    or_q = or_q | Q(tileid__in=subquery)
                    print(f"[ADV][GRP][TILE] OR union with subquery[{idx}]")
                any_exists_q = Q(Exists(tiles_base.filter(or_q).values("tileid")[:1]))
        else:
            any_exists_q = Q()

        if resource_level_conditions:
            if logic.upper() == "AND":
                resource_q = Q()
                for condition in resource_level_conditions:
                    resource_q &= condition
                final_q = any_exists_q & resource_q
            else:
                resource_q = Q()
                for condition in resource_level_conditions:
                    resource_q |= condition
                final_q = any_exists_q | resource_q
            print(
                "[ADV][GRP][TILE] return -> Q(combined ANY-tiles) composed with resource-level quantifier conditions"
            )
            return final_q

        print("[ADV][GRP][TILE] return -> Q(exists combined tile set)")
        return any_exists_q

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
        operands = clause_payload.get("operands") or []
        is_negated_template = bool(getattr(facet, "is_orm_template_negated", False))

        quantifier = (clause_payload.get("quantifier") or "ANY").upper()
        if quantifier not in ("ANY", "ALL", "NONE"):
            quantifier = "ANY"

        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstanceid")
        ).order_by()

        if not operands:
            if operator_upper == "HAS_NO_VALUE":
                if quantifier in (
                    "ANY",
                    "ALL",
                ):
                    return Q(~Exists(correlated_rows))
                return Q(Exists(correlated_rows))
            if operator_upper == "HAS_ANY_VALUE":
                if quantifier in (
                    "ANY",
                    "ALL",
                ):
                    return Q(Exists(correlated_rows))
                return Q(~Exists(correlated_rows))
            if not is_negated_template:
                if quantifier in (
                    "ANY",
                    "ALL",
                ):
                    return Q(Exists(correlated_rows))
                return Q(~Exists(correlated_rows))
            else:
                if quantifier in (
                    "ANY",
                    "ALL",
                ):
                    return Q(~Exists(correlated_rows))
                return Q(Exists(correlated_rows))

        params = self.clause_compiler._literal_params(operands)
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
            positive_facet = self._positive_facet_for(
                datatype_name, clause_payload.get("operator")
            )
            if positive_facet is not None:
                pos_pred = self.clause_compiler._predicate_from_facet(
                    facet=positive_facet, column_name="value", params=params
                )
                violators = (
                    correlated_rows.filter(pos_pred)
                    if isinstance(pos_pred, Q)
                    else correlated_rows.filter(**pos_pred)
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
        Push constraints that live inside the relationship-bearing group's immediate children
        down onto the leg's pairs queryset.

        Key rules:
        - Only push down from relationship-less child groups whose logic is AND.
        - Correlate literals to the CHILD side using compiled_pair_info['child_id_field'].
        - Gate pushdown by the child group's graph_slug to avoid cross-graph leakage.
        - If a subject lacks a search table, SKIP (do not empty pairs).
        - RELATED clauses aimed at the terminal CHILD node are also pushed.
        - One nested leg (single hop) supported with the same pushdown rules.
        """
        matches_per_child = base_pairs
        touched = False

        child_id_field = compiled_pair_info["child_id_field"]

        def _apply_literal_clause_to_pairs(
            pairs_queryset: QuerySet,
            clause_payload: Dict[str, Any],
            correlate_field: str,
        ) -> Tuple[QuerySet, bool]:
            subj_graph, subj_alias = self.clause_compiler._unpack_single_path(
                clause_payload.get("subject") or []
            )
            subj_rows = self.clause_compiler._search_rows(subj_graph, subj_alias)
            if subj_rows is None:
                print(
                    f"[ADV][DBG] pushdown skip (no rows model) -> {subj_graph}.{subj_alias}"
                )
                return (
                    pairs_queryset,
                    False,
                )  # IMPORTANT: don't annihilate pairs; just skip

            dtype = self.clause_compiler._datatype_for_alias(subj_graph, subj_alias)
            facet = self.clause_compiler._facet(dtype, clause_payload.get("operator"))
            operands = clause_payload.get("operands") or []
            correlated = subj_rows.filter(
                resourceinstanceid=OuterRef(correlate_field)
            ).order_by()

            # No-operand operators / presence checks
            if not operands:
                op_upper = (clause_payload.get("operator") or "").upper()
                if op_upper == "HAS_NO_VALUE":
                    return pairs_queryset.filter(~Exists(correlated)), True
                if op_upper == "HAS_ANY_VALUE":
                    return pairs_queryset.filter(Exists(correlated)), True
                is_neg = bool(getattr(facet, "is_orm_template_negated", False))
                return (
                    pairs_queryset.filter(~Exists(correlated))
                    if is_neg
                    else pairs_queryset.filter(Exists(correlated))
                ), True

            # Value-bearing predicates
            pred = self.clause_compiler._predicate_from_facet(
                facet=facet,
                column_name="value",
                params=self.clause_compiler._literal_params(operands),
            )
            is_neg = bool(getattr(facet, "is_orm_template_negated", False))
            filt = (
                correlated.filter(pred)
                if isinstance(pred, Q)
                else correlated.filter(**pred)
            )

            if not is_neg:
                return pairs_queryset.filter(Exists(filt)), True

            # Negated: prefer positive-counterpart if available
            pos_facet = self._positive_facet_for(dtype, clause_payload.get("operator"))
            if pos_facet is not None:
                pos_pred = self.clause_compiler._predicate_from_facet(
                    facet=pos_facet,
                    column_name="value",
                    params=self.clause_compiler._literal_params(operands),
                )
                pos_filt = (
                    correlated.filter(pos_pred)
                    if isinstance(pos_pred, Q)
                    else correlated.filter(**pos_pred)
                )
                return pairs_queryset.filter(~Exists(pos_filt)), True

            if isinstance(pred, Q) and getattr(pred, "negated", False):
                return pairs_queryset.filter(~Exists(correlated.filter(~pred))), True

            return pairs_queryset.filter(~Exists(filt)), True

        # ---------- 1) Relationship-less AND child groups (push down by child group graph) ----------
        for child_group in group_payload.get("groups") or []:
            # Only immediate children with no relationship and AND logic
            if (child_group.get("relationship") or {}).get("path"):
                continue
            if (child_group.get("logic") or "AND").upper() != "AND":
                print(
                    "[ADV][DBG] skip pushdown: relationship-less child group with non-AND logic"
                )
                continue

            child_group_graph = (child_group.get("graph_slug") or "").strip()
            # Collect literals from this child group and its relationship-less descendants
            stack = [child_group]
            while stack:
                node = stack.pop()
                if (node.get("relationship") or {}).get("path"):
                    continue
                for clause in node.get("clauses") or []:
                    if (clause.get("type") or "").upper() != "LITERAL":
                        continue
                    subj_graph, _ = self.clause_compiler._unpack_single_path(
                        clause.get("subject") or []
                    )
                    # Gate by the child group's graph to avoid cross-graph bleed
                    if (
                        child_group_graph
                        and subj_graph
                        and subj_graph != child_group_graph
                    ):
                        continue
                    matches_per_child, did = _apply_literal_clause_to_pairs(
                        matches_per_child, clause, child_id_field
                    )
                    if did:
                        print(
                            f"[ADV][DBG] pushdown apply -> child[{child_id_field}] {subj_graph} literal"
                        )
                        touched = True
                for g in node.get("groups") or []:
                    stack.append(g)

        # ---------- 2) One nested leg (single hop) under this relationship group ----------
        nested_group = next(
            (
                g
                for g in (group_payload.get("groups") or [])
                if ((g.get("relationship") or {}).get("path"))
            ),
            None,
        )
        if nested_group:
            nested_rel = nested_group.get("relationship") or {}
            nested_path = nested_rel.get("path") or []
            if len(nested_path) == 1:
                nested_mode = (
                    (nested_rel.get("hop_modes") or ["ANY"])[0] or "ANY"
                ).upper()
                _dt, nested_term_graph, nested_pairs, nested_child_field = (
                    self.path_navigator.build_scoped_pairs_for_path(
                        path_segments=nested_path,
                        is_inverse_relationship=bool(nested_rel.get("is_inverse")),
                        correlate_on_field=child_id_field,
                    )
                )

                # Collect literals under the nested subtree, but prefer those matching the nested terminal graph
                literals_all: List[Dict[str, Any]] = []
                stack = [nested_group]
                while stack:
                    node = stack.pop()
                    # Traverse through relationship groups; only collect LITERALs from relationship-less nodes
                    if not (node.get("relationship") or {}).get("path"):
                        for clause in node.get("clauses") or []:
                            if (clause.get("type") or "").upper() == "LITERAL":
                                literals_all.append(clause)
                    for g in node.get("groups") or []:
                        stack.append(g)

                def _by_graph(
                    lits: List[Dict[str, Any]], gslug: str
                ) -> List[Dict[str, Any]]:
                    out = []
                    for c in lits:
                        sg, _ = self.clause_compiler._unpack_single_path(
                            c.get("subject") or []
                        )
                        if sg == gslug:
                            out.append(c)
                    return out

                nested_literals = (
                    _by_graph(literals_all, nested_term_graph)
                    if nested_term_graph
                    else []
                )
                if not nested_literals:
                    # Fallback: keep literals whose subject rows exist and are not the parent terminal
                    filtered = []
                    for c in literals_all:
                        sg, sa = self.clause_compiler._unpack_single_path(
                            c.get("subject") or []
                        )
                        if not sg:
                            continue
                        rows = self.clause_compiler._search_rows(sg, sa)
                        if rows is not None:
                            filtered.append(c)
                    nested_literals = filtered

                print(
                    f"[ADV][DBG] nested pushdown literals={len(nested_literals)} target_field={nested_child_field}"
                )

                nested_ok = nested_pairs
                for c in nested_literals:
                    nested_ok, did = _apply_literal_clause_to_pairs(
                        nested_ok, c, nested_child_field
                    )
                    if did:
                        touched = True

                if nested_mode == "ANY":
                    matches_per_child = matches_per_child.filter(Exists(nested_ok))
                    touched = True
                elif nested_mode == "NONE":
                    matches_per_child = matches_per_child.filter(
                        Exists(nested_pairs) & ~Exists(nested_ok)
                    )
                    touched = True
                else:
                    # ALL for nested hop
                    same_child_ok = nested_ok.filter(
                        **{nested_child_field: OuterRef(nested_child_field)}
                    )
                    violators = nested_pairs.filter(~Exists(same_child_ok))
                    matches_per_child = matches_per_child.filter(
                        Exists(nested_pairs) & ~Exists(violators)
                    )
                    touched = True

        # ---------- 3) RELATED clauses aimed at the child terminal node ----------
        term_graph = compiled_pair_info["terminal_graph_slug"]
        term_alias = compiled_pair_info["terminal_node_alias"]
        for rel_clause in group_payload.get("clauses") or []:
            if (rel_clause.get("type") or "").upper() != "RELATED":
                continue
            subj_graph, subj_alias = self.clause_compiler._unpack_single_path(
                rel_clause.get("subject") or []
            )
            op_upper = (rel_clause.get("operator") or "").upper()
            has_ops = bool(rel_clause.get("operands"))

            # Skip the trivial HAS_ANY_VALUE on the terminal node (leg existence already enforces it)
            if (
                subj_graph == term_graph
                and subj_alias == term_alias
                and op_upper == "HAS_ANY_VALUE"
                and not has_ops
            ):
                continue

            rel_qs = self.clause_compiler.related_child_exists_qs(
                rel_clause, compiled_pair_info
            )
            if rel_qs is None:
                continue

            if not has_ops:
                facet = self.clause_compiler._facet(
                    self.clause_compiler._datatype_for_alias(subj_graph, subj_alias),
                    rel_clause.get("operator"),
                )
                if op_upper == "HAS_NO_VALUE":
                    matches_per_child = matches_per_child.filter(~Exists(rel_qs))
                elif op_upper == "HAS_ANY_VALUE":
                    matches_per_child = matches_per_child.filter(Exists(rel_qs))
                else:
                    is_neg = bool(getattr(facet, "is_orm_template_negated", False))
                    matches_per_child = matches_per_child.filter(
                        ~Exists(rel_qs) if is_neg else Exists(rel_qs)
                    )
            else:
                matches_per_child = matches_per_child.filter(Exists(rel_qs))
            touched = True

        return matches_per_child, touched

    def _filter_pairs_by_and_block(
        self,
        pairs_scoped_to_anchor: QuerySet,
        group_payload_and_block: Dict[str, Any],
        target_graph_slug: str,
        correlate_on_field: str,
    ) -> QuerySet:
        if (group_payload_and_block.get("logic") or "AND").upper() != "AND":
            return pairs_scoped_to_anchor

        filtered_pairs = pairs_scoped_to_anchor

        for clause_payload in group_payload_and_block.get("clauses") or []:
            if (clause_payload.get("type") or "").upper() != "LITERAL":
                continue
            subject_graph_slug, subject_alias = (
                self.clause_compiler._unpack_single_path(
                    clause_payload.get("subject") or []
                )
            )
            if subject_graph_slug != target_graph_slug:
                continue

            subject_rows = self.clause_compiler._search_rows(
                subject_graph_slug, subject_alias
            )
            if subject_rows is None:
                continue

            datatype_name = self.clause_compiler._datatype_for_alias(
                subject_graph_slug, subject_alias
            )
            facet = self._facet_for(datatype_name, clause_payload.get("operator"))
            operands = clause_payload.get("operands") or []
            correlated_subject_rows = subject_rows.filter(
                resourceinstanceid=OuterRef(correlate_on_field)
            )

            if not operands:
                operator_upper = (clause_payload.get("operator") or "").upper()
                if operator_upper == "HAS_NO_VALUE":
                    filtered_pairs = filtered_pairs.filter(
                        ~Exists(correlated_subject_rows)
                    )
                elif operator_upper == "HAS_ANY_VALUE":
                    filtered_pairs = filtered_pairs.filter(
                        Exists(correlated_subject_rows)
                    )
                else:
                    is_negated = bool(getattr(facet, "is_orm_template_negated", False))
                    filtered_pairs = filtered_pairs.filter(
                        ~Exists(correlated_subject_rows)
                        if is_negated
                        else Exists(correlated_subject_rows)
                    )
            else:
                predicate = self.clause_compiler._predicate_from_facet(
                    facet=facet,
                    column_name="value",
                    params=self.clause_compiler._literal_params(operands),
                )
                filtered = (
                    correlated_subject_rows.filter(predicate)
                    if isinstance(predicate, Q)
                    else correlated_subject_rows.filter(**predicate)
                )
                is_negated = bool(getattr(facet, "is_orm_template_negated", False))
                if is_negated:
                    pos_facet = self._positive_facet_for(
                        datatype_name, clause_payload.get("operator")
                    )
                    if pos_facet is not None:
                        pos_pred = self.clause_compiler._predicate_from_facet(
                            facet=pos_facet,
                            column_name="value",
                            params=self.clause_compiler._literal_params(operands),
                        )
                        pos_filt = (
                            correlated_subject_rows.filter(pos_pred)
                            if isinstance(pos_pred, Q)
                            else correlated_subject_rows.filter(**pos_pred)
                        )
                        filtered_pairs = filtered_pairs.filter(~Exists(pos_filt))
                    elif isinstance(predicate, Q) and getattr(
                        predicate, "negated", False
                    ):
                        filtered_pairs = filtered_pairs.filter(
                            ~Exists(correlated_subject_rows.filter(~predicate))
                        )
                    else:
                        filtered_pairs = filtered_pairs.filter(~Exists(filtered))
                else:
                    filtered_pairs = filtered_pairs.filter(Exists(filtered))

        for child_payload in group_payload_and_block.get("groups") or []:
            if (child_payload.get("relationship") or {}).get("path"):
                continue
            filtered_pairs = self._filter_pairs_by_and_block(
                pairs_scoped_to_anchor=filtered_pairs,
                group_payload_and_block=child_payload,
                target_graph_slug=target_graph_slug,
                correlate_on_field=correlate_on_field,
            )

        return filtered_pairs

    def _positive_facet_for(self, datatype_name: str, operator_token: Optional[str]):
        try:
            reg = getattr(self.clause_compiler, "facet_registry", None)
            if reg and hasattr(reg, "get_positive_facet_for"):
                return reg.get_positive_facet_for(operator_token, datatype_name)
        except Exception:
            pass
        try:
            facet = self.clause_compiler._facet(datatype_name, operator_token)
            return getattr(facet, "positive_counterpart", None)
        except Exception:
            return None

    def _facet_for(self, datatype_name: str, operator_token: Optional[str]):
        return self.clause_compiler._facet(datatype_name, operator_token)

    def _require_path_navigator(self, path_navigator: PathNavigator) -> PathNavigator:
        if not hasattr(path_navigator, "search_model_registry") or not hasattr(
            path_navigator, "node_alias_datatype_registry"
        ):
            raise AttributeError(
                "PathNavigator must expose search_model_registry and node_alias_datatype_registry."
            )
        return path_navigator
