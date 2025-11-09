from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet
from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.operand_compiler import OperandCompiler


QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"


class ClauseCompiler:
    def __init__(
        self,
        search_model_registry,
        facet_registry,
        path_navigator,
        operand_compiler: OperandCompiler,
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.operand_compiler = operand_compiler

    def compile(self, clause_payload: Dict[str, Any]) -> Exists:
        clause_type = (clause_payload.get("type") or "").upper()
        if clause_type == CLAUSE_TYPE_LITERAL:
            return self._compile_literal_clause(clause_payload)
        if clause_type == CLAUSE_TYPE_RELATED:
            return self._related_presence_exists(clause_payload)
        return Exists(arches_models.ResourceInstance.objects.none())

    def anchor_exists_for_group(self, group_payload: Dict[str, Any]) -> List[Exists]:
        existence_predicates: List[Exists] = []
        for clause_payload in group_payload.get("clauses") or []:
            clause_type = (clause_payload.get("type") or "").upper()
            if clause_type == CLAUSE_TYPE_RELATED:
                continue
            existence_predicates.append(self.compile(clause_payload=clause_payload))
        return existence_predicates

    def group_has_child_targeting_clause(self, group_payload: Dict[str, Any]) -> bool:
        for clause_payload in group_payload.get("clauses") or []:
            if (clause_payload.get("type") or "").upper() == CLAUSE_TYPE_RELATED:
                return True
        return False

    def constrain_pairs_for_group(
        self,
        *,
        base_pairs: QuerySet,
        compiled_pair_info: Dict[str, Any],
        group_payload: Dict[str, Any],
        use_or_logic: bool,
    ) -> Tuple[QuerySet, bool]:
        constrained_pairs = base_pairs
        had_any_inner_filters = False
        child_id_field_name = compiled_pair_info["child_id_field"]

        if not use_or_logic:
            constrained_pairs, applied_here = self._filter_pairs_by_group_literals(
                pairs_queryset=constrained_pairs,
                compiled_pair_info=compiled_pair_info,
                correlate_field=child_id_field_name,
                group_payload=group_payload,
            )
            had_any_inner_filters = had_any_inner_filters or applied_here
        else:
            or_q, saw_any_ok_rows = self._or_q_from_group_literals(
                group_payload, compiled_pair_info
            )
            if saw_any_ok_rows and or_q is not None:
                constrained_pairs = base_pairs.filter(or_q)
                had_any_inner_filters = True

        nested_group_payload = next(
            (
                nested
                for nested in group_payload.get("groups") or []
                if ((nested.get("relationship")) or {}).get("path")
            ),
            None,
        )
        if nested_group_payload:
            constrained_pairs, applied_nested = self._apply_nested_single_hop_literals(
                base_pairs_for_child=constrained_pairs,
                compiled_pair_info=compiled_pair_info,
                nested_group_payload=nested_group_payload,
            )
            had_any_inner_filters = had_any_inner_filters or applied_nested

        constrained_pairs, applied_related = self._apply_related_clauses_to_pairs(
            pairs_queryset=constrained_pairs,
            compiled_pair_info=compiled_pair_info,
            group_payload=group_payload,
        )
        had_any_inner_filters = had_any_inner_filters or applied_related

        return constrained_pairs, had_any_inner_filters

    def related_child_exists_qs(
        self, clause_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ):
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload["operator"] or "").upper()
        operand_items = clause_payload.get("operands") or []

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)
        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug, node_alias=subject_node_alias
        )

        correlated_subject_rows = subject_rows.filter(
            resourceinstanceid=OuterRef(compiled_pair_info["child_id_field"])
        ).annotate(_anchor_resource_id=OuterRef(compiled_pair_info["anchor_id_field"]))

        if not operand_items:
            return correlated_subject_rows

        predicate_expression, _ = self.operand_compiler.build_predicate(
            datatype_name=datatype_name,
            operator_token=operator_token,
            operands=operand_items,
            anchor_resource_id_annotation="_anchor_resource_id",
        )

        if isinstance(predicate_expression, Q):
            return correlated_subject_rows.filter(predicate_expression)
        return correlated_subject_rows.filter(**predicate_expression)

    def child_ok_rows_from_literals(
        self, group_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ):
        terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]
        child_id_field = compiled_pair_info["child_id_field"]

        literal_clauses: List[Dict[str, Any]] = []
        for child_group_payload in group_payload.get("groups") or []:
            if (child_group_payload.get("relationship") or {}).get("path"):
                continue
            if (child_group_payload.get("logic") or "AND").upper() != "AND":
                return None

            pending_nodes: List[Dict[str, Any]] = [child_group_payload]
            while pending_nodes:
                node_payload = pending_nodes.pop()
                if (node_payload.get("relationship") or {}).get("path"):
                    continue

                for clause_payload in node_payload.get("clauses") or []:
                    if (
                        clause_payload.get("type") or ""
                    ).upper() != CLAUSE_TYPE_LITERAL:
                        continue
                    subject_graph_slug, _ = clause_payload["subject"][0]
                    if subject_graph_slug != terminal_graph_slug:
                        return None
                    literal_clauses.append(clause_payload)

                for nested in node_payload.get("groups") or []:
                    pending_nodes.append(nested)

        if not literal_clauses:
            return None

        accumulated_rows = None

        for clause_payload in literal_clauses:
            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = (clause_payload["operator"] or "").upper()
            operand_items = clause_payload.get("operands") or []

            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
            )
            model_class = self.search_model_registry.get_model_for_datatype(
                datatype_name
            )
            subject_rows = model_class.objects.filter(
                graph_slug=subject_graph_slug, node_alias=subject_node_alias
            )
            correlated_rows = subject_rows.filter(
                resourceinstanceid=OuterRef(child_id_field)
            )

            if not operand_items:
                presence_implies_match = (
                    self.facet_registry.zero_arity_presence_is_match(
                        datatype_name, operator_token
                    )
                )
                predicate_rows = (
                    correlated_rows
                    if presence_implies_match
                    else correlated_rows.none()
                )
            else:
                predicate_expression, is_template_negated = (
                    self.operand_compiler.build_predicate(
                        datatype_name=datatype_name,
                        operator_token=operator_token,
                        operands=operand_items,
                        anchor_resource_id_annotation=None,
                    )
                )
                filtered_rows = (
                    correlated_rows.filter(predicate_expression)
                    if isinstance(predicate_expression, Q)
                    else correlated_rows.filter(**predicate_expression)
                )
                if not is_template_negated:
                    predicate_rows = filtered_rows
                else:
                    positive_facet = self.facet_registry.get_positive_facet_for(
                        operator_token, datatype_name
                    )
                    if positive_facet is not None:
                        positive_expression, _ = self.facet_registry.predicate(
                            datatype_name,
                            positive_facet.operator,
                            "value",
                            self.operand_compiler.literal_values_only(operand_items),
                        )
                        predicate_rows = (
                            correlated_rows.exclude(positive_expression)
                            if isinstance(positive_expression, Q)
                            else correlated_rows.exclude(**positive_expression)
                        )
                    elif isinstance(predicate_expression, Q) and getattr(
                        predicate_expression, "negated", False
                    ):
                        predicate_rows = correlated_rows.exclude(~predicate_expression)
                    else:
                        predicate_rows = (
                            correlated_rows.exclude(predicate_expression)
                            if isinstance(predicate_expression, Q)
                            else correlated_rows.exclude(**predicate_expression)
                        )

            if accumulated_rows is None:
                accumulated_rows = predicate_rows
            else:
                accumulated_rows = accumulated_rows.filter(
                    pk__in=predicate_rows.values("pk")
                )

        return accumulated_rows

    def tile_scope_q(
        self,
        *,
        group_payload: Dict[str, Any],
        tiles_for_anchor_resource: QuerySet,
    ) -> Q:
        if not (group_payload.get("clauses") or []) and not (
            group_payload.get("groups") or []
        ):
            return Q(~Exists(tiles_for_anchor_resource)) | Q(
                Exists(tiles_for_anchor_resource)
            )

        per_tile_exists_conditions: List[Q] = []
        resource_level_conditions: List[Q] = []

        if any(
            ((child.get("relationship") or {}).get("path"))
            for child in (group_payload.get("groups") or [])
        ):
            return Q(pk__in=[])

        use_and_logic = (group_payload.get("logic") or "AND").upper() == "AND"

        for clause_payload in group_payload.get("clauses") or []:
            clause_type = (clause_payload.get("type") or "").upper()
            if clause_type != CLAUSE_TYPE_LITERAL:
                continue

            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = (clause_payload["operator"] or "").upper()
            quantifier_token = (clause_payload["quantifier"] or "").upper()
            operand_items = clause_payload.get("operands") or []

            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
            )
            model_class = self.search_model_registry.get_model_for_datatype(
                datatype_name
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
                    self.facet_registry.zero_arity_presence_is_match(
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
                self.operand_compiler.build_predicate(
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

            positive_facet = self.facet_registry.get_positive_facet_for(
                operator_token, datatype_name
            )
            if positive_facet is not None:
                positive_expression, _ = self.facet_registry.predicate(
                    datatype_name,
                    positive_facet.operator,
                    "value",
                    self.operand_compiler.literal_values_only(operand_items),
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

    def _compile_literal_clause(self, clause_payload: Dict[str, Any]) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload.get("operator") or "").upper()
        quantifier_token = (clause_payload.get("quantifier") or "").upper()
        operand_items = clause_payload.get("operands")

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)
        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug, node_alias=subject_node_alias
        )

        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstanceid")
        )

        if not operand_items:
            presence_implies_match = self.facet_registry.zero_arity_presence_is_match(
                datatype_name, operator_token
            )
            if quantifier_token == QUANTIFIER_NONE:
                return (
                    ~Exists(correlated_rows)
                    if presence_implies_match
                    else Exists(correlated_rows)
                )
            if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
                return (
                    Exists(correlated_rows)
                    if presence_implies_match
                    else ~Exists(correlated_rows)
                )

        predicate_expression, is_template_negated = (
            self.operand_compiler.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=operand_items,
                anchor_resource_id_annotation=None,
            )
        )
        matching_rows = (
            correlated_rows.filter(predicate_expression)
            if isinstance(predicate_expression, Q)
            else correlated_rows.filter(**predicate_expression)
        )

        if quantifier_token == QUANTIFIER_ANY:
            return Exists(matching_rows)
        if quantifier_token == QUANTIFIER_NONE:
            return ~Exists(matching_rows)

        if not is_template_negated:
            violating_rows = (
                correlated_rows.exclude(predicate_expression)
                if isinstance(predicate_expression, Q)
                else correlated_rows.exclude(**predicate_expression)
            )
            return Exists(correlated_rows) & ~Exists(violating_rows)

        positive_facet = self.facet_registry.get_positive_facet_for(
            operator_token, datatype_name
        )
        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name,
                positive_facet.operator,
                "value",
                self.operand_compiler.literal_values_only(operand_items),
            )
            positive_rows = (
                correlated_rows.filter(positive_expression)
                if isinstance(positive_expression, Q)
                else correlated_rows.filter(**positive_expression)
            )
            return Exists(correlated_rows) & ~Exists(positive_rows)

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            return Exists(correlated_rows) & ~Exists(
                correlated_rows.filter(~predicate_expression)
            )

        return Exists(correlated_rows) & ~Exists(matching_rows)

    def _related_presence_exists(self, clause_payload: Dict[str, Any]) -> Exists:
        operator_token = (clause_payload["operator"] or "").upper()
        quantifier_token = (clause_payload["quantifier"] or "").upper()
        subject_path_sequence = clause_payload["subject"]

        compiled_pair_info, pairs_scoped_to_anchor_resource = (
            self.path_navigator.build_relationship_pairs(
                {"path": subject_path_sequence, "is_inverse": False}
            )
        )

        terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]
        terminal_node_alias = compiled_pair_info["terminal_node_alias"]
        terminal_datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                terminal_graph_slug, terminal_node_alias
            )
        )

        presence_implies_match = self.facet_registry.zero_arity_presence_is_match(
            terminal_datatype_name, operator_token
        )

        if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
            return (
                Exists(pairs_scoped_to_anchor_resource)
                if presence_implies_match
                else ~Exists(pairs_scoped_to_anchor_resource)
            )

        if quantifier_token == QUANTIFIER_NONE:
            return (
                ~Exists(pairs_scoped_to_anchor_resource)
                if presence_implies_match
                else Exists(pairs_scoped_to_anchor_resource)
            )

        return Exists(
            self.search_model_registry.get_model_for_datatype(
                terminal_datatype_name
            ).objects.none()
        )

    def _filter_pairs_by_group_literals(
        self,
        *,
        pairs_queryset: QuerySet,
        compiled_pair_info: Dict[str, Any],
        correlate_field: str,
        group_payload: Dict[str, Any],
    ) -> Tuple[QuerySet, bool]:
        working_pairs = pairs_queryset
        had_any_inner_filters = False

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
                working_pairs, applied_here = self._filter_pairs_by_clause(
                    pairs_queryset=working_pairs,
                    clause_payload=clause_payload,
                    correlate_field=correlate_field,
                )
                had_any_inner_filters = had_any_inner_filters or applied_here
            for deeper_group_payload in node_payload.get("groups") or []:
                if ((deeper_group_payload.get("relationship")) or {}).get("path"):
                    continue
                pending_nodes.append(deeper_group_payload)

        return working_pairs, had_any_inner_filters

    def _or_q_from_group_literals(
        self,
        group_payload: Dict[str, Any],
        compiled_pair_info: Dict[str, Any],
    ) -> Tuple[Optional[Q], bool]:
        or_q = Q(pk__in=[])
        saw_any_ok_rows = False

        for child_group_payload in group_payload.get("groups") or []:
            if ((child_group_payload.get("relationship")) or {}).get("path"):
                continue
            ok_rows = self.child_ok_rows_from_literals(
                child_group_payload, compiled_pair_info
            )
            if ok_rows is None:
                continue
            or_q |= Q(Exists(ok_rows))
            saw_any_ok_rows = True

        return (or_q if saw_any_ok_rows else None), saw_any_ok_rows

    def _apply_nested_single_hop_literals(
        self,
        *,
        base_pairs_for_child: QuerySet,
        compiled_pair_info: Dict[str, Any],
        nested_group_payload: Dict[str, Any],
    ) -> Tuple[QuerySet, bool]:
        nested_relationship = nested_group_payload.get("relationship") or {}
        nested_path = nested_relationship.get("path") or []
        if len(nested_path) != 1:
            return base_pairs_for_child, False

        parent_child_id_field_name = compiled_pair_info["child_id_field"]
        nested_quantifier = (
            (nested_relationship.get("traversal_quantifiers") or [QUANTIFIER_ANY])[0]
        ).upper()

        (
            _anchor_graph_slug_ignored,
            _nested_terminal_graph_slug,
            nested_pairs_for_child,
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
            if not ((node_payload.get("relationship")) or {}).get("path"):
                for clause_payload in node_payload.get("clauses") or []:
                    if (
                        clause_payload.get("type") or ""
                    ).upper() == CLAUSE_TYPE_LITERAL:
                        literal_clauses_all.append(clause_payload)
            for deeper_group_payload in node_payload.get("groups") or []:
                stack_for_collection.append(deeper_group_payload)

        nested_ok_pairs = nested_pairs_for_child
        had_any_inner_filters = False
        for clause_payload in literal_clauses_all:
            nested_ok_pairs, applied_here = self._filter_pairs_by_clause(
                pairs_queryset=nested_ok_pairs,
                clause_payload=clause_payload,
                correlate_field=nested_child_id_field_name,
            )
            had_any_inner_filters = had_any_inner_filters or applied_here

        if nested_quantifier == QUANTIFIER_ANY:
            return base_pairs_for_child.filter(Exists(nested_ok_pairs)), True

        if nested_quantifier == QUANTIFIER_NONE:
            return (
                base_pairs_for_child.filter(
                    Exists(nested_pairs_for_child) & ~Exists(nested_ok_pairs)
                ),
                True,
            )

        same_child_ok = nested_ok_pairs.filter(
            **{nested_child_id_field_name: OuterRef(nested_child_id_field_name)}
        )
        violating_pairs = nested_pairs_for_child.filter(~Exists(same_child_ok))
        return (
            base_pairs_for_child.filter(
                Exists(nested_pairs_for_child) & ~Exists(violating_pairs)
            ),
            True or had_any_inner_filters,
        )

    def _apply_related_clauses_to_pairs(
        self,
        *,
        pairs_queryset: QuerySet,
        compiled_pair_info: Dict[str, Any],
        group_payload: Dict[str, Any],
    ) -> Tuple[QuerySet, bool]:
        terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]
        terminal_node_alias = compiled_pair_info["terminal_node_alias"]

        constrained_child_pairs = pairs_queryset
        had_any_inner_filters = False

        for clause_payload in group_payload.get("clauses") or []:
            if (clause_payload.get("type") or "").upper() != CLAUSE_TYPE_RELATED:
                continue

            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = (clause_payload.get("operator") or "").upper()
            has_operands = bool(clause_payload.get("operands"))

            if (
                subject_graph_slug == terminal_graph_slug
                and subject_node_alias == terminal_node_alias
                and not has_operands
            ):
                if self._zero_arity_presence_is_match(
                    subject_graph_slug, subject_node_alias, operator_token
                ):
                    continue

            related_exists_qs = self.related_child_exists_qs(
                clause_payload, compiled_pair_info
            )
            if related_exists_qs is None:
                continue

            if not has_operands:
                presence_implies_match = self._zero_arity_presence_is_match(
                    subject_graph_slug, subject_node_alias, operator_token
                )
                constrained_child_pairs = (
                    constrained_child_pairs.filter(Exists(related_exists_qs))
                    if presence_implies_match
                    else constrained_child_pairs.filter(~Exists(related_exists_qs))
                )
            else:
                constrained_child_pairs = constrained_child_pairs.filter(
                    Exists(related_exists_qs)
                )

            had_any_inner_filters = True

        return constrained_child_pairs, had_any_inner_filters

    def _filter_pairs_by_clause(
        self,
        *,
        pairs_queryset: QuerySet,
        clause_payload: Dict[str, Any],
        correlate_field: str,
    ):
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload["operator"] or "").upper()
        operand_items = clause_payload.get("operands") or []

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)
        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug, node_alias=subject_node_alias
        )
        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef(correlate_field)
        )

        if not operand_items:
            presence_implies_match = self.facet_registry.zero_arity_presence_is_match(
                datatype_name, operator_token
            )
            return (
                (pairs_queryset.filter(Exists(correlated_rows)), True)
                if presence_implies_match
                else (pairs_queryset.filter(~Exists(correlated_rows)), True)
            )

        predicate_expression, is_template_negated = (
            self.operand_compiler.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=operand_items,
                anchor_resource_id_annotation=None,
            )
        )

        if not is_template_negated:
            if isinstance(predicate_expression, Q):
                return (
                    pairs_queryset.filter(
                        Exists(correlated_rows.filter(predicate_expression))
                    ),
                    True,
                )
            return (
                pairs_queryset.filter(
                    Exists(correlated_rows.filter(**predicate_expression))
                ),
                True,
            )

        positive_facet = self.facet_registry.get_positive_facet_for(
            operator_token, datatype_name
        )
        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name,
                positive_facet.operator,
                "value",
                self.operand_compiler.literal_values_only(operand_items),
            )
            if isinstance(positive_expression, Q):
                return (
                    pairs_queryset.filter(
                        ~Exists(correlated_rows.filter(positive_expression))
                    ),
                    True,
                )
            return (
                pairs_queryset.filter(
                    ~Exists(correlated_rows.filter(**positive_expression))
                ),
                True,
            )

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            return (
                pairs_queryset.filter(
                    ~Exists(correlated_rows.filter(~predicate_expression))
                ),
                True,
            )

        if isinstance(predicate_expression, Q):
            return (
                pairs_queryset.filter(
                    ~Exists(correlated_rows.filter(predicate_expression))
                ),
                True,
            )
        return (
            pairs_queryset.filter(
                ~Exists(correlated_rows.filter(**predicate_expression))
            ),
            True,
        )

    def _zero_arity_presence_is_match(
        self,
        subject_graph_slug: str,
        subject_node_alias: str,
        operator_token: str,
    ) -> bool:
        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug,
                subject_node_alias,
            )
        )
        return self.facet_registry.zero_arity_presence_is_match(
            datatype_name,
            (operator_token or "").upper(),
        )
