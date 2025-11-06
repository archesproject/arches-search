from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet, Subquery
from arches.app.models import models as arches_models


LOGIC_AND = "AND"
SCOPE_RESOURCE = "RESOURCE"
SCOPE_TILE = "TILE"

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"

OPERATOR_HAS_ANY_VALUE = "HAS_ANY_VALUE"
OPERATOR_HAS_NO_VALUE = "HAS_NO_VALUE"


class ClauseCompiler:
    def __init__(self, search_model_registry, facet_registry, path_navigator) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator

    def compile(
        self,
        clause_payload: Dict[str, Any],
        anchor_graph_slug: str,
        correlate_to_tile: bool = False,
    ) -> Exists:
        if not clause_payload:
            return Exists(arches_models.ResourceInstance.objects.none())
        if (clause_payload.get("type") or "").upper() == CLAUSE_TYPE_RELATED:
            return Exists(arches_models.ResourceInstance.objects.none())

        subject_path = clause_payload.get("subject") or []
        if not subject_path:
            return Exists(arches_models.ResourceInstance.objects.none())

        subject_graph_slug, subject_node_alias = subject_path[0]
        if subject_graph_slug != anchor_graph_slug:
            return Exists(arches_models.ResourceInstance.objects.none())

        subject_rows = self.fetch_subject_rows(subject_graph_slug, subject_node_alias)
        if subject_rows is None:
            return Exists(arches_models.ResourceInstance.objects.none())

        correlated_rows = (
            subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstance_id"),
                tileid=OuterRef("tileid"),
            ).order_by()
            if correlate_to_tile
            else subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            ).order_by()
        )

        operator_token = (clause_payload.get("operator") or "").upper()
        quantifier_token = (clause_payload.get("quantifier") or QUANTIFIER_ANY).upper()
        operand_items = clause_payload.get("operands") or []

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )

        if not operand_items:
            if operator_token == OPERATOR_HAS_ANY_VALUE:
                presence_means_match = True
            elif operator_token == OPERATOR_HAS_NO_VALUE:
                presence_means_match = False
            else:
                facet = self.facet_registry.get_facet(datatype_name, operator_token)
                presence_means_match = not bool(
                    getattr(facet, "is_orm_template_negated", False)
                )
            if quantifier_token == QUANTIFIER_NONE:
                return (
                    ~Exists(correlated_rows)
                    if presence_means_match
                    else Exists(correlated_rows)
                )
            if quantifier_token == QUANTIFIER_ANY or quantifier_token == QUANTIFIER_ALL:
                return (
                    Exists(correlated_rows)
                    if presence_means_match
                    else ~Exists(correlated_rows)
                )
            return Exists(arches_models.ResourceInstance.objects.none())

        literal_values = [
            (item["value"] if isinstance(item, dict) and "value" in item else item)
            for item in operand_items
        ]
        predicate_expression, is_template_negated = self.facet_registry.predicate(
            datatype_name, operator_token, "value", literal_values
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
            violating_rows = correlated_rows.exclude(pk__in=matching_rows.values("pk"))
            return Exists(correlated_rows) & ~Exists(violating_rows)

        positive_facet = self.facet_registry.get_positive_facet_for(
            operator_token, datatype_name
        )
        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name, positive_facet.operator, "value", literal_values
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

    def compile_literal_to_q(
        self,
        clause_payload: Dict[str, Any],
        anchor_graph_slug: str,
        scope: str,
    ) -> Optional[Q]:
        if (clause_payload.get("type") or "").upper() != CLAUSE_TYPE_LITERAL:
            return None

        subject_path = clause_payload.get("subject") or []
        if not subject_path:
            return Q(pk__in=[])

        subject_graph_slug, _ = subject_path[0]
        if subject_graph_slug != anchor_graph_slug:
            return Q(pk__in=[])

        if (scope or "").upper() == SCOPE_TILE:
            return self.compile_relationshipless_tile_group_to_q(
                {"clauses": [clause_payload], "logic": LOGIC_AND},
                anchor_graph_slug,
                LOGIC_AND,
            )

        return Q(
            self.compile(clause_payload, anchor_graph_slug, correlate_to_tile=False)
        )

    def compile_relationshipless_tile_group_to_q(
        self,
        group_payload: Dict[str, Any],
        anchor_graph_slug: str,
        logic: str,
    ) -> Q:
        clause_payloads = group_payload.get("clauses") or []
        if not clause_payloads:
            return Q()

        tiles_for_anchor_resource = arches_models.Tile.objects.filter(
            resourceinstance_id=OuterRef("resourceinstanceid")
        ).order_by()

        tileid_subqueries_for_any: List[Subquery] = []
        resource_level_conditions: List[Q] = []

        for clause_payload in clause_payloads:
            subject_path = clause_payload.get("subject") or []
            if not subject_path:
                empty_tileids = arches_models.Tile.objects.none().values("tileid")[:1]
                tileid_subqueries_for_any.append(Subquery(empty_tileids))
                continue

            subject_graph_slug, subject_node_alias = subject_path[0]
            if subject_graph_slug != anchor_graph_slug:
                empty_tileids = arches_models.Tile.objects.none().values("tileid")[:1]
                tileid_subqueries_for_any.append(Subquery(empty_tileids))
                continue

            subject_rows = self.fetch_subject_rows(
                subject_graph_slug, subject_node_alias
            )
            if subject_rows is None:
                empty_tileids = arches_models.Tile.objects.none().values("tileid")[:1]
                tileid_subqueries_for_any.append(Subquery(empty_tileids))
                continue

            operator_token = (clause_payload.get("operator") or "").upper()
            quantifier_token = (
                clause_payload.get("quantifier") or QUANTIFIER_ANY
            ).upper()
            operand_items = clause_payload.get("operands") or []

            rows_correlated_to_resource = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            ).order_by()
            rows_correlated_to_tile_resource = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstance_id")
            ).order_by()

            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
            )

            if not operand_items:
                if operator_token == OPERATOR_HAS_ANY_VALUE:
                    presence_means_match = True
                elif operator_token == OPERATOR_HAS_NO_VALUE:
                    presence_means_match = False
                else:
                    facet = self.facet_registry.get_facet(datatype_name, operator_token)
                    presence_means_match = not bool(
                        getattr(facet, "is_orm_template_negated", False)
                    )

                if quantifier_token == QUANTIFIER_ANY:
                    subquery_tile_if_match = rows_correlated_to_tile_resource.filter(
                        tileid=OuterRef("tileid")
                    ).values("tileid")[:1]
                    tileid_subqueries_for_any.append(
                        Subquery(subquery_tile_if_match)
                        if presence_means_match
                        else Subquery(
                            arches_models.Tile.objects.filter(tileid=OuterRef("tileid"))
                            .filter(
                                ~Exists(
                                    rows_correlated_to_tile_resource.filter(
                                        tileid=OuterRef("tileid")
                                    )
                                )
                            )
                            .values("tileid")[:1]
                        )
                    )
                elif quantifier_token == QUANTIFIER_NONE:
                    resource_level_conditions.append(
                        Q(~Exists(rows_correlated_to_resource))
                        if presence_means_match
                        else Q(Exists(rows_correlated_to_resource))
                    )
                else:
                    if presence_means_match:
                        tiles_missing_match = tiles_for_anchor_resource.filter(
                            ~Exists(
                                rows_correlated_to_tile_resource.filter(
                                    tileid=OuterRef("tileid")
                                )
                            )
                        ).values("tileid")
                        requires_all_tiles_match = Q(
                            ~Exists(
                                tiles_for_anchor_resource.filter(
                                    tileid__in=Subquery(tiles_missing_match)
                                ).values("tileid")[:1]
                            )
                        )
                        has_at_least_one_tile = Q(
                            Exists(tiles_for_anchor_resource.values("tileid")[:1])
                        )
                        resource_level_conditions.append(
                            requires_all_tiles_match & has_at_least_one_tile
                        )
                    else:
                        has_at_least_one_tile = Q(
                            Exists(tiles_for_anchor_resource.values("tileid")[:1])
                        )
                        resource_level_conditions.append(has_at_least_one_tile)
                continue

            literal_values = [
                (item["value"] if isinstance(item, dict) and "value" in item else item)
                for item in operand_items
            ]
            predicate_expression, is_template_negated = self.facet_registry.predicate(
                datatype_name, operator_token, "value", literal_values
            )

            matching_rows_resource = (
                rows_correlated_to_resource.filter(predicate_expression)
                if isinstance(predicate_expression, Q)
                else rows_correlated_to_resource.filter(**predicate_expression)
            )
            matches_in_this_tile = (
                rows_correlated_to_tile_resource.filter(predicate_expression)
                if isinstance(predicate_expression, Q)
                else rows_correlated_to_tile_resource.filter(**predicate_expression)
            ).filter(tileid=OuterRef("tileid"))

            if quantifier_token == QUANTIFIER_ANY:
                if not is_template_negated:
                    tileid_subqueries_for_any.append(
                        Subquery(matches_in_this_tile.values("tileid")[:1])
                    )
                else:
                    tileid_subqueries_for_any.append(
                        Subquery(
                            arches_models.Tile.objects.filter(tileid=OuterRef("tileid"))
                            .filter(~Exists(matches_in_this_tile))
                            .values("tileid")[:1]
                        )
                    )
            elif quantifier_token == QUANTIFIER_NONE:
                resource_level_conditions.append(Q(~Exists(matching_rows_resource)))
            else:
                if not is_template_negated:
                    tiles_missing_match = tiles_for_anchor_resource.filter(
                        ~Exists(matches_in_this_tile)
                    ).values("tileid")
                    requires_all_tiles_match = Q(
                        ~Exists(
                            tiles_for_anchor_resource.filter(
                                tileid__in=Subquery(tiles_missing_match)
                            ).values("tileid")[:1]
                        )
                    )
                    has_at_least_one_tile = Q(
                        Exists(tiles_for_anchor_resource.values("tileid")[:1])
                    )
                    resource_level_conditions.append(
                        requires_all_tiles_match & has_at_least_one_tile
                    )
                else:
                    positive_facet = self.facet_registry.get_positive_facet_for(
                        operator_token, datatype_name
                    )
                    if positive_facet is not None:
                        positive_expression, _ = self.facet_registry.predicate(
                            datatype_name,
                            positive_facet.operator,
                            "value",
                            literal_values,
                        )
                        positive_matches_resource = (
                            rows_correlated_to_resource.filter(positive_expression)
                            if isinstance(positive_expression, Q)
                            else rows_correlated_to_resource.filter(
                                **positive_expression
                            )
                        )
                    elif isinstance(predicate_expression, Q) and getattr(
                        predicate_expression, "negated", False
                    ):
                        positive_matches_resource = rows_correlated_to_resource.filter(
                            ~predicate_expression
                        )
                    else:
                        positive_matches_resource = rows_correlated_to_resource.exclude(
                            pk__in=matching_rows_resource.values("pk")
                        )
                    has_no_positive_matches = Q(~Exists(positive_matches_resource)) & Q(
                        Exists(tiles_for_anchor_resource.values("tileid")[:1])
                    )
                    resource_level_conditions.append(has_no_positive_matches)

        if not tileid_subqueries_for_any:
            any_expression = Q()
        else:
            if (logic or "").upper() == LOGIC_AND:
                tiles_requiring_all = tiles_for_anchor_resource
                for tileid_subquery in tileid_subqueries_for_any:
                    tiles_requiring_all = tiles_requiring_all.filter(
                        tileid__in=tileid_subquery
                    )
                any_expression = Q(Exists(tiles_requiring_all.values("tileid")[:1]))
            else:
                or_condition = Q(pk__in=[])
                for tileid_subquery in tileid_subqueries_for_any:
                    or_condition = or_condition | Q(tileid__in=tileid_subquery)
                any_expression = Q(
                    Exists(
                        tiles_for_anchor_resource.filter(or_condition).values("tileid")[
                            :1
                        ]
                    )
                )

        if not resource_level_conditions:
            return any_expression

        if (logic or "").upper() == LOGIC_AND:
            combined = Q()
            for condition in resource_level_conditions:
                combined &= condition
            return any_expression & combined

        combined = Q()
        for condition in resource_level_conditions:
            combined |= condition
        return any_expression | combined

    def filter_pairs_by_clause(
        self,
        pairs_queryset: QuerySet,
        clause_payload: Dict[str, Any],
        correlate_field: str,
    ) -> Tuple[QuerySet, bool]:
        subject_path = clause_payload.get("subject") or []
        if not subject_path:
            return pairs_queryset, False

        subject_graph_slug, subject_node_alias = subject_path[0]
        subject_rows = self.fetch_subject_rows(subject_graph_slug, subject_node_alias)
        if subject_rows is None:
            return pairs_queryset, False

        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef(correlate_field)
        ).order_by()

        operand_items = clause_payload.get("operands") or []
        operator_token = (clause_payload.get("operator") or "").upper()

        if not operand_items:
            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
            )
            if operator_token == OPERATOR_HAS_ANY_VALUE:
                presence_means_match = True
            elif operator_token == OPERATOR_HAS_NO_VALUE:
                presence_means_match = False
            else:
                facet = self.facet_registry.get_facet(datatype_name, operator_token)
                presence_means_match = not bool(
                    getattr(facet, "is_orm_template_negated", False)
                )
            return (
                pairs_queryset.filter(Exists(correlated_rows))
                if presence_means_match
                else pairs_queryset.filter(~Exists(correlated_rows))
            ), True

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        literal_values = [
            (item["value"] if isinstance(item, dict) and "value" in item else item)
            for item in operand_items
        ]
        predicate_expression, is_template_negated = self.facet_registry.predicate(
            datatype_name, operator_token, "value", literal_values
        )
        filtered_rows = (
            correlated_rows.filter(predicate_expression)
            if isinstance(predicate_expression, Q)
            else correlated_rows.filter(**predicate_expression)
        )

        if not is_template_negated:
            return pairs_queryset.filter(Exists(filtered_rows)), True

        positive_facet = self.facet_registry.get_positive_facet_for(
            operator_token, datatype_name
        )
        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name, positive_facet.operator, "value", literal_values
            )
            positive_rows = (
                correlated_rows.filter(positive_expression)
                if isinstance(positive_expression, Q)
                else correlated_rows.filter(**positive_expression)
            )
            return pairs_queryset.filter(~Exists(positive_rows)), True

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            return (
                pairs_queryset.filter(
                    ~Exists(correlated_rows.filter(~predicate_expression))
                ),
                True,
            )

        return pairs_queryset.filter(~Exists(filtered_rows)), True

    def related_child_exists_qs(
        self, clause_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ) -> Optional[QuerySet]:
        subject_path = clause_payload.get("subject") or []
        if not subject_path:
            return None

        subject_graph_slug, subject_node_alias = subject_path[0]
        if subject_graph_slug != compiled_pair_info["terminal_graph_slug"]:
            return None

        subject_rows = self.fetch_subject_rows(subject_graph_slug, subject_node_alias)
        if subject_rows is None:
            return None

        correlated_subject_rows = (
            subject_rows.filter(
                resourceinstanceid=OuterRef(compiled_pair_info["child_id_field"])
            )
            .annotate(
                _anchor_resource_id=OuterRef(compiled_pair_info["anchor_id_field"])
            )
            .order_by()
        )

        operand_items = clause_payload.get("operands") or []
        if not operand_items:
            return correlated_subject_rows

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )

        rhs_path_operand = next(
            (
                item
                for item in operand_items
                if isinstance(item, dict)
                and (item.get("type") or "").upper() == "PATH"
                and "value" in item
            ),
            None,
        )

        if rhs_path_operand:
            rhs_path_sequence = rhs_path_operand["value"]
            _, _, rhs_rows = self.path_navigator.build_path_queryset(rhs_path_sequence)
            rhs_scalar_value = Subquery(
                rhs_rows.filter(
                    resourceinstanceid=OuterRef("_anchor_resource_id")
                ).values("value")[:1]
            )
            predicate_parameters = [rhs_scalar_value]
        else:
            predicate_parameters = [
                (item["value"] if isinstance(item, dict) and "value" in item else item)
                for item in operand_items
            ]

        predicate_expression, _ = self.facet_registry.predicate(
            datatype_name, clause_payload["operator"], "value", predicate_parameters
        )
        return (
            correlated_subject_rows.filter(predicate_expression)
            if isinstance(predicate_expression, Q)
            else correlated_subject_rows.filter(**predicate_expression)
        )

    def child_ok_rows_from_literals(
        self, group_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ) -> Optional[QuerySet]:
        terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]
        child_id_field = compiled_pair_info["child_id_field"]

        literal_clauses: List[Dict[str, Any]] = []

        for child_group_payload in group_payload.get("groups") or []:
            relationship_block = child_group_payload.get("relationship") or {}
            if relationship_block.get("path"):
                continue
            if (child_group_payload.get("logic") or LOGIC_AND).upper() != LOGIC_AND:
                return None

            pending_nodes: List[Dict[str, Any]] = [child_group_payload]
            while pending_nodes:
                node_payload = pending_nodes.pop()
                relationship_block = node_payload.get("relationship") or {}
                if relationship_block.get("path"):
                    continue

                for clause_payload in node_payload.get("clauses") or []:
                    if (
                        clause_payload.get("type") or ""
                    ).upper() != CLAUSE_TYPE_LITERAL:
                        continue
                    subject_path = clause_payload.get("subject") or []
                    if not subject_path:
                        continue
                    subject_graph_slug, _ = subject_path[0]
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
            subject_rows = self.fetch_subject_rows(
                subject_graph_slug, subject_node_alias
            )
            if subject_rows is None:
                continue

            correlated_rows = subject_rows.filter(
                resourceinstanceid=OuterRef(child_id_field)
            ).order_by()

            operator_token = (clause_payload.get("operator") or "").upper()
            operands = clause_payload.get("operands") or []

            if not operands:
                datatype_name = self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
                if operator_token == OPERATOR_HAS_NO_VALUE:
                    predicate_rows = correlated_rows.none()
                elif operator_token == OPERATOR_HAS_ANY_VALUE:
                    predicate_rows = correlated_rows
                else:
                    facet = self.facet_registry.get_facet(datatype_name, operator_token)
                    is_template_negated = bool(
                        getattr(facet, "is_orm_template_negated", False)
                    )
                    predicate_rows = (
                        correlated_rows.none()
                        if is_template_negated
                        else correlated_rows
                    )
            else:
                datatype_name = self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
                literal_values = [
                    (
                        item["value"]
                        if isinstance(item, dict) and "value" in item
                        else item
                    )
                    for item in operands
                ]
                predicate_expression, is_template_negated = (
                    self.facet_registry.predicate(
                        datatype_name, operator_token, "value", literal_values
                    )
                )
                filtered = (
                    correlated_rows.filter(predicate_expression)
                    if isinstance(predicate_expression, Q)
                    else correlated_rows.filter(**predicate_expression)
                )

                if not is_template_negated:
                    predicate_rows = filtered
                else:
                    positive_facet = self.facet_registry.get_positive_facet_for(
                        operator_token, datatype_name
                    )
                    if positive_facet is not None:
                        positive_expression, _ = self.facet_registry.predicate(
                            datatype_name,
                            positive_facet.operator,
                            "value",
                            literal_values,
                        )
                        positive_filtered = (
                            correlated_rows.filter(positive_expression)
                            if isinstance(positive_expression, Q)
                            else correlated_rows.filter(**positive_expression)
                        )
                        predicate_rows = correlated_rows.exclude(
                            pk__in=positive_filtered.values("pk")
                        )
                    elif isinstance(predicate_expression, Q) and getattr(
                        predicate_expression, "negated", False
                    ):
                        predicate_rows = correlated_rows.exclude(
                            pk__in=correlated_rows.filter(~predicate_expression).values(
                                "pk"
                            )
                        )
                    else:
                        predicate_rows = correlated_rows.exclude(
                            pk__in=filtered.values("pk")
                        )

            accumulated_rows = (
                predicate_rows
                if accumulated_rows is None
                else accumulated_rows.filter(pk__in=predicate_rows.values("pk"))
            )

        return accumulated_rows

    def fetch_subject_rows(
        self, graph_slug: str, node_alias: str
    ) -> Optional[QuerySet]:
        datatype = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                graph_slug, node_alias
            )
        )

        model_class = self.search_model_registry.get_model_for_datatype(datatype)
        return model_class.objects.filter(
            graph_slug=graph_slug, node_alias=node_alias
        ).order_by()
