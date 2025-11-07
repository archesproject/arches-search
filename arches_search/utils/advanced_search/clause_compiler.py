from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet, Subquery
from arches.app.models import models as arches_models


SCOPE_RESOURCE = "RESOURCE"
SCOPE_TILE = "TILE"

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"


class ClauseCompiler:
    def __init__(self, search_model_registry, facet_registry, path_navigator) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator

    def _presence_means_match_for_zero_operands(
        self, datatype_name: str, operator_token: str
    ) -> bool:
        facet = self.facet_registry.get_facet(datatype_name, operator_token)
        accepts_no_operands = not bool(getattr(facet, "operand_types", None))
        if not accepts_no_operands:
            return False
        return bool(getattr(facet, "is_orm_template_negated", False))

    def _predicate_for(
        self, datatype_name: str, operator_token: str, parameters: List[Any]
    ) -> Tuple[Any, bool]:
        return self.facet_registry.predicate(
            datatype_name, operator_token, "value", parameters
        )

    def compile(
        self,
        clause_payload: Dict[str, Any],
        correlate_to_tile: bool = False,
    ) -> Exists:
        clause_type = (clause_payload["type"] or "").upper()
        if clause_type == CLAUSE_TYPE_LITERAL:
            return self._compile_literal(clause_payload, correlate_to_tile)
        if clause_type == CLAUSE_TYPE_RELATED:
            return self._compile_related_presence(clause_payload)
        return Exists(arches_models.ResourceInstance.objects.none())

    def _compile_literal(
        self,
        clause_payload: Dict[str, Any],
        correlate_to_tile: bool,
    ) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload["operator"] or "").upper()
        quantifier_token = (clause_payload["quantifier"] or "").upper()
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

        if correlate_to_tile:
            correlated_rows = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstance_id"),
                tileid=OuterRef("tileid"),
            )
        else:
            correlated_rows = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            )

        if not operand_items:
            presence_means_match = self._presence_means_match_for_zero_operands(
                datatype_name, operator_token
            )
            if quantifier_token == QUANTIFIER_NONE:
                return (
                    ~Exists(correlated_rows)
                    if presence_means_match
                    else Exists(correlated_rows)
                )
            if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
                return (
                    Exists(correlated_rows)
                    if presence_means_match
                    else ~Exists(correlated_rows)
                )

        literal_values = [
            (i["value"] if isinstance(i, dict) else i) for i in operand_items
        ]
        predicate_expression, is_template_negated = self._predicate_for(
            datatype_name, operator_token, literal_values
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
            positive_expression, _ = self._predicate_for(
                datatype_name, positive_facet.operator, literal_values
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

    def _compile_related_presence(self, clause_payload: Dict[str, Any]) -> Exists:
        operator_token = (clause_payload["operator"] or "").upper()
        quantifier_token = (clause_payload["quantifier"] or "").upper()
        subject_path_sequence = clause_payload["subject"]

        anchor_id_field, child_id_field, pairs_queryset = (
            self.path_navigator.build_path_queryset(subject_path_sequence)
        )
        correlated_pairs = pairs_queryset.filter(
            **{anchor_id_field: OuterRef("resourceinstanceid")}
        )

        terminal_graph_slug, terminal_node_alias = subject_path_sequence[-1]
        terminal_datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                terminal_graph_slug, terminal_node_alias
            )
        )
        presence_means_match = self._presence_means_match_for_zero_operands(
            terminal_datatype_name, operator_token
        )

        if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
            return (
                Exists(correlated_pairs)
                if presence_means_match
                else ~Exists(correlated_pairs)
            )
        if quantifier_token == QUANTIFIER_NONE:
            return (
                ~Exists(correlated_pairs)
                if presence_means_match
                else Exists(correlated_pairs)
            )
        return Exists(arches_models.ResourceInstance.objects.none())

    def compile_literal_to_q(
        self,
        clause_payload: Dict[str, Any],
        scope: str,
    ) -> Optional[Q]:
        if (scope or "").upper() == SCOPE_TILE:
            return self.compile_relationshipless_tile_group_to_q(
                {"clauses": [clause_payload], "logic": "AND"},
                use_and_logic=True,
            )
        return Q(self.compile(clause_payload, correlate_to_tile=False))

    def compile_relationshipless_tile_group_to_q(
        self,
        group_payload: Dict[str, Any],
        use_and_logic: bool,
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
                presence_means_match = self._presence_means_match_for_zero_operands(
                    datatype_name, operator_token
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
                        condition if presence_means_match else ~condition
                    )
                    continue

                if quantifier_token == QUANTIFIER_NONE:
                    resource_level_conditions.append(
                        Q(~Exists(rows_correlated_to_resource))
                        if presence_means_match
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
                    if presence_means_match
                    else Q(~Exists(tiles_for_anchor_resource))
                )
                continue

            literal_values = [
                (i["value"] if isinstance(i, dict) else i) for i in operand_items
            ]
            predicate_expression, is_template_negated = self._predicate_for(
                datatype_name, operator_token, literal_values
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
                positive_expression, _ = self._predicate_for(
                    datatype_name, positive_facet.operator, literal_values
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

    def filter_pairs_by_clause(
        self,
        pairs_queryset: QuerySet,
        clause_payload: Dict[str, Any],
        correlate_field: str,
    ) -> Tuple[QuerySet, bool]:
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
            presence_means_match = self._presence_means_match_for_zero_operands(
                datatype_name, operator_token
            )
            return (
                (pairs_queryset.filter(Exists(correlated_rows)), True)
                if presence_means_match
                else (pairs_queryset.filter(~Exists(correlated_rows)), True)
            )

        literal_values = [
            (i["value"] if isinstance(i, dict) else i) for i in operand_items
        ]
        predicate_expression, is_template_negated = self._predicate_for(
            datatype_name, operator_token, literal_values
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
            positive_expression, _ = self._predicate_for(
                datatype_name, positive_facet.operator, literal_values
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

    def related_child_exists_qs(
        self, clause_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ) -> Optional[QuerySet]:
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

        rhs_path_operand = next(
            (
                i
                for i in operand_items
                if isinstance(i, dict) and (i.get("type") or "").upper() == "PATH"
            ),
            None,
        )

        if rhs_path_operand:
            rhs_path_sequence = rhs_path_operand["value"]
            _, _, rhs_rows = self.path_navigator.build_path_queryset(rhs_path_sequence)
            rhs_scalar_value = rhs_rows.filter(
                resourceinstanceid=OuterRef("_anchor_resource_id")
            ).values("value")[:1]
            predicate_parameters = [Subquery(rhs_scalar_value)]
        else:
            predicate_parameters = [
                (i["value"] if isinstance(i, dict) else i) for i in operand_items
            ]

        predicate_expression, _ = self._predicate_for(
            datatype_name, operator_token, predicate_parameters
        )
        if isinstance(predicate_expression, Q):
            return correlated_subject_rows.filter(predicate_expression)
        return correlated_subject_rows.filter(**predicate_expression)

    def child_ok_rows_from_literals(
        self, group_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ) -> Optional[QuerySet]:
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

        accumulated_rows: Optional[QuerySet] = None

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
                presence_means_match = self._presence_means_match_for_zero_operands(
                    datatype_name, operator_token
                )
                predicate_rows = (
                    correlated_rows if presence_means_match else correlated_rows.none()
                )
            else:
                literal_values = [
                    (i["value"] if isinstance(i, dict) else i) for i in operand_items
                ]
                predicate_expression, is_template_negated = self._predicate_for(
                    datatype_name, operator_token, literal_values
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
                        positive_expression, _ = self._predicate_for(
                            datatype_name, positive_facet.operator, literal_values
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

    def fetch_subject_rows(
        self, graph_slug: str, node_alias: str
    ) -> Optional[QuerySet]:
        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                graph_slug, node_alias
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)
        return model_class.objects.filter(graph_slug=graph_slug, node_alias=node_alias)
