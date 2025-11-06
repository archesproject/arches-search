from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional, Sequence

from django.db.models import Exists, OuterRef, Q, QuerySet, Subquery
from arches.app.models import models as arches_models


class ClauseCompiler:
    def __init__(self, search_model_registry, facet_registry, path_navigator) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator

    def compile(
        self,
        clause_payload: Dict[str, Any],
        anchor_graph_slug: str,
        *,
        correlate_to_tile: bool = False,
    ) -> Exists:
        if not clause_payload or not clause_payload.get("subject"):
            return Exists(arches_models.ResourceInstance.objects.none())
        if (clause_payload.get("type") or "").upper() == "RELATED":
            return Exists(arches_models.ResourceInstance.objects.none())

        quantifier = (clause_payload.get("quantifier") or "ANY").upper()
        subject_path = clause_payload.get("subject") or []
        subject_graph_slug, subject_node_alias = (
            subject_path[0] if subject_path else ("", "")
        )
        if subject_graph_slug != anchor_graph_slug:
            return Exists(arches_models.ResourceInstance.objects.none())

        subject_search_rows = self.rows_for(subject_graph_slug, subject_node_alias)
        if subject_search_rows is None:
            return Exists(arches_models.ResourceInstance.objects.none())

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        facet = self.facet_registry.get_facet(
            datatype_name, clause_payload.get("operator")
        )
        operand_items = clause_payload.get("operands") or []

        correlation_filters = (
            {
                "resourceinstanceid": OuterRef("resourceinstance_id"),
                "tileid": OuterRef("tileid"),
            }
            if correlate_to_tile
            else {"resourceinstanceid": OuterRef("resourceinstanceid")}
        )
        correlated_rows = subject_search_rows.filter(**correlation_filters).order_by()

        operator_upper = (clause_payload.get("operator") or "").upper()
        predicate_result = None
        if operand_items:
            literal_values = self._literal_params(operand_items)
            predicate_result = self.facet_registry.predicate(
                datatype_name, clause_payload.get("operator"), "value", literal_values
            )

        if not operand_items:
            is_template_negated = bool(getattr(facet, "is_orm_template_negated", False))
            if operator_upper == "HAS_ANY_VALUE":
                return (
                    Exists(correlated_rows)
                    if quantifier in ("ANY", "ALL")
                    else ~Exists(correlated_rows)
                )
            if operator_upper == "HAS_NO_VALUE":
                return (
                    ~Exists(correlated_rows)
                    if quantifier in ("ANY", "ALL")
                    else Exists(correlated_rows)
                )
            if is_template_negated:
                return (
                    ~Exists(correlated_rows)
                    if quantifier in ("ANY", "ALL")
                    else Exists(correlated_rows)
                )
            return (
                Exists(correlated_rows)
                if quantifier in ("ANY", "ALL")
                else ~Exists(correlated_rows)
            )

        predicate_expr, is_template_negated = predicate_result
        matching_rows = (
            correlated_rows.filter(predicate_expr)
            if isinstance(predicate_expr, Q)
            else correlated_rows.filter(**predicate_expr)
        )

        if not is_template_negated:
            violating_rows = correlated_rows.exclude(pk__in=matching_rows.values("pk"))
        else:
            positive_facet = self.facet_registry.get_positive_facet_for(
                clause_payload.get("operator"), datatype_name
            )
            if positive_facet is not None:
                positive_predicate_expr, _ = self.facet_registry.predicate(
                    datatype_name,
                    positive_facet.operator,
                    "value",
                    self._literal_params(operand_items),
                )
                violating_rows = (
                    correlated_rows.filter(positive_predicate_expr)
                    if isinstance(positive_predicate_expr, Q)
                    else correlated_rows.filter(**positive_predicate_expr)
                )
            elif isinstance(predicate_expr, Q) and getattr(
                predicate_expr, "negated", False
            ):
                violating_rows = correlated_rows.filter(~predicate_expr)
            else:
                violating_rows = correlated_rows.exclude(
                    pk__in=matching_rows.values("pk")
                )

        if quantifier == "ANY":
            return Exists(matching_rows)
        if quantifier == "NONE":
            return ~Exists(matching_rows)
        return Exists(correlated_rows) & ~Exists(violating_rows)

    def compile_literal_to_q(
        self, clause_payload: Dict[str, Any], anchor_graph_slug: str, *, scope: str
    ) -> Optional[Q]:
        if (clause_payload.get("type") or "").upper() != "LITERAL":
            return None

        quantifier = (clause_payload.get("quantifier") or "ANY").upper()
        subject_path = clause_payload.get("subject") or []
        subject_graph_slug, subject_node_alias = (
            subject_path[0] if subject_path else ("", "")
        )
        if subject_graph_slug != anchor_graph_slug:
            return Q(pk__in=[])

        subject_search_rows = self.rows_for(subject_graph_slug, subject_node_alias)
        if subject_search_rows is None:
            return Q(pk__in=[])

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        operator_upper = (clause_payload.get("operator") or "").upper()
        operand_items = clause_payload.get("operands") or []

        if scope == "TILE":
            return self.compile_relationshipless_tile_group_to_q(
                group_payload={"clauses": [clause_payload], "logic": "AND"},
                anchor_graph_slug=anchor_graph_slug,
                logic="AND",
            )

        correlated_rows = subject_search_rows.filter(
            resourceinstanceid=OuterRef("resourceinstanceid")
        ).order_by()

        if not operand_items:
            facet = self.facet_registry.get_facet(
                datatype_name, clause_payload.get("operator")
            )
            is_template_negated = bool(getattr(facet, "is_orm_template_negated", False))
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
            if not is_template_negated:
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

        predicate_expr, is_template_negated = self.facet_registry.predicate(
            datatype_name,
            clause_payload.get("operator"),
            "value",
            self._literal_params(operand_items),
        )
        matching_rows = (
            correlated_rows.filter(predicate_expr)
            if isinstance(predicate_expr, Q)
            else correlated_rows.filter(**predicate_expr)
        )

        if not is_template_negated:
            violating_rows = correlated_rows.exclude(pk__in=matching_rows.values("pk"))
        else:
            positive_facet = self.facet_registry.get_positive_facet_for(
                clause_payload.get("operator"), datatype_name
            )
            if positive_facet is not None:
                positive_expr, _ = self.facet_registry.predicate(
                    datatype_name,
                    positive_facet.operator,
                    "value",
                    self._literal_params(operand_items),
                )
                violating_rows = (
                    correlated_rows.filter(positive_expr)
                    if isinstance(positive_expr, Q)
                    else correlated_rows.filter(**positive_expr)
                )
            elif isinstance(predicate_expr, Q) and getattr(
                predicate_expr, "negated", False
            ):
                violating_rows = correlated_rows.filter(~predicate_expr)
            else:
                violating_rows = correlated_rows.exclude(
                    pk__in=matching_rows.values("pk")
                )

        if quantifier == "ANY":
            return Q(Exists(matching_rows))
        if quantifier == "NONE":
            return Q(~Exists(matching_rows))
        return Q(Exists(correlated_rows) & ~Exists(violating_rows))

    def compile_relationshipless_tile_group_to_q(
        self, *, group_payload: Dict[str, Any], anchor_graph_slug: str, logic: str
    ) -> Q:
        clauses = group_payload.get("clauses") or []
        if not clauses:
            return Q()

        tileid_subqueries_for_any: List[Subquery] = []
        resource_level_conditions: List[Q] = []

        tiles_base = arches_models.Tile.objects.filter(
            resourceinstance_id=OuterRef("resourceinstanceid")
        ).order_by()

        for clause_payload in clauses:
            subject_path = clause_payload.get("subject") or []
            subject_graph_slug, subject_alias = (
                subject_path[0] if subject_path else ("", "")
            )
            if subject_graph_slug != anchor_graph_slug:
                empty_tile_subquery = arches_models.Tile.objects.none().values(
                    "tileid"
                )[:1]
                tileid_subqueries_for_any.append(Subquery(empty_tile_subquery))
                continue

            subject_rows = self.rows_for(subject_graph_slug, subject_alias)
            if subject_rows is None:
                empty_tile_subquery = arches_models.Tile.objects.none().values(
                    "tileid"
                )[:1]
                tileid_subqueries_for_any.append(Subquery(empty_tile_subquery))
                continue

            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_alias
                )
            )
            facet = self.facet_registry.get_facet(
                datatype_name, clause_payload.get("operator")
            )
            operator_upper = (clause_payload.get("operator") or "").upper()
            operand_items = clause_payload.get("operands") or []
            quantifier = (clause_payload.get("quantifier") or "ANY").upper()
            is_negated_template = bool(getattr(facet, "is_orm_template_negated", False))

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
                params = self._literal_params(operand_items)
                predicate_expr, _ = self.facet_registry.predicate(
                    datatype_name, clause_payload.get("operator"), "value", params
                )
                matches_rows_tile = (
                    subject_rows_correlated_to_tile.filter(predicate_expr)
                    if isinstance(predicate_expr, Q)
                    else subject_rows_correlated_to_tile.filter(**predicate_expr)
                )
                matches_rows_resource = (
                    subject_rows_correlated_to_resource.filter(predicate_expr)
                    if isinstance(predicate_expr, Q)
                    else subject_rows_correlated_to_resource.filter(**predicate_expr)
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
                    params = self._literal_params(operand_items)
                    positive_facet = self.facet_registry.get_positive_facet_for(
                        clause_payload.get("operator"), datatype_name
                    )
                    if positive_facet is not None:
                        positive_expr, _ = self.facet_registry.predicate(
                            datatype_name, positive_facet.operator, "value", params
                        )
                        positive_matches_resource = (
                            subject_rows_correlated_to_resource.filter(positive_expr)
                            if isinstance(positive_expr, Q)
                            else subject_rows_correlated_to_resource.filter(
                                **positive_expr
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

    def filter_pairs_by_clause(
        self,
        pairs_queryset: QuerySet,
        clause_payload: Dict[str, Any],
        correlate_field: str,
    ) -> tuple[QuerySet, bool]:
        subject_path = clause_payload.get("subject") or []
        subject_graph_slug, subject_alias = (
            subject_path[0] if subject_path else ("", "")
        )
        subject_rows = self.rows_for(subject_graph_slug, subject_alias)
        if subject_rows is None:
            return pairs_queryset, False

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_alias
            )
        )
        operand_items = clause_payload.get("operands") or []
        correlated = subject_rows.filter(
            resourceinstanceid=OuterRef(correlate_field)
        ).order_by()

        if not operand_items:
            facet = self.facet_registry.get_facet(
                datatype_name, clause_payload.get("operator")
            )
            operator_upper = (clause_payload.get("operator") or "").upper()
            if operator_upper == "HAS_NO_VALUE":
                return pairs_queryset.filter(~Exists(correlated)), True
            if operator_upper == "HAS_ANY_VALUE":
                return pairs_queryset.filter(Exists(correlated)), True
            is_negated_template = bool(getattr(facet, "is_orm_template_negated", False))
            return (
                pairs_queryset.filter(~Exists(correlated))
                if is_negated_template
                else pairs_queryset.filter(Exists(correlated))
            ), True

        predicate_expr, is_template_negated = self.facet_registry.predicate(
            datatype_name,
            clause_payload.get("operator"),
            "value",
            self._literal_params(operand_items),
        )
        filtered = (
            correlated.filter(predicate_expr)
            if isinstance(predicate_expr, Q)
            else correlated.filter(**predicate_expr)
        )

        if not is_template_negated:
            return pairs_queryset.filter(Exists(filtered)), True

        positive_facet = self.facet_registry.get_positive_facet_for(
            clause_payload.get("operator"), datatype_name
        )
        if positive_facet is not None:
            positive_expr, _ = self.facet_registry.predicate(
                datatype_name,
                positive_facet.operator,
                "value",
                self._literal_params(operand_items),
            )
            positive_filtered = (
                correlated.filter(positive_expr)
                if isinstance(positive_expr, Q)
                else correlated.filter(**positive_expr)
            )
            return pairs_queryset.filter(~Exists(positive_filtered)), True

        if isinstance(predicate_expr, Q) and getattr(predicate_expr, "negated", False):
            return (
                pairs_queryset.filter(~Exists(correlated.filter(~predicate_expr))),
                True,
            )

        return pairs_queryset.filter(~Exists(filtered)), True

    def related_child_exists_qs(
        self, clause_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ) -> Optional[QuerySet]:
        subject_path = clause_payload.get("subject") or []
        subject_graph_slug, subject_node_alias = (
            subject_path[0] if subject_path else ("", "")
        )
        if subject_graph_slug != compiled_pair_info["terminal_graph_slug"]:
            return None

        subject_search_rows = self.rows_for(subject_graph_slug, subject_node_alias)
        if subject_search_rows is None:
            return None

        correlated_subject_rows = (
            subject_search_rows.filter(
                resourceinstanceid=OuterRef(compiled_pair_info["child_id_field"])
            )
            .annotate(
                _anchor_resource_id=OuterRef(compiled_pair_info["anchor_id_field"])
            )
            .order_by()
        )

        operator_token = clause_payload.get("operator")
        operand_items = clause_payload.get("operands") or []
        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )

        if not operand_items:
            return correlated_subject_rows

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
            rhs_path = rhs_path_operand["value"]
            _rhs_datatype_name, _rhs_graph_slug, rhs_rows = (
                self.path_navigator.build_path_queryset(rhs_path)
            )
            rhs_scalar = Subquery(
                rhs_rows.filter(
                    resourceinstanceid=OuterRef("_anchor_resource_id")
                ).values("value")[:1]
            )
            params = [rhs_scalar]
        else:
            params = self._literal_params(operand_items)

        predicate_expr, _ = self.facet_registry.predicate(
            datatype_name, operator_token, "value", params
        )
        return (
            correlated_subject_rows.filter(predicate_expr)
            if isinstance(predicate_expr, Q)
            else correlated_subject_rows.filter(**predicate_expr)
        )

    def rows_for(self, graph_slug: str, node_alias: str) -> Optional[QuerySet]:
        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                graph_slug, node_alias
            )
        )
        try:
            model_class = self.search_model_registry.get_model_for_datatype(
                datatype_name
            )
        except Exception:
            return None
        return model_class.objects.filter(
            graph_slug=graph_slug, node_alias=node_alias
        ).order_by()

    def _literal_params(self, operands: List[Any]) -> List[Any]:
        literal_values: List[Any] = []
        for operand_item in operands:
            if operand_item is None:
                continue
            if isinstance(operand_item, dict):
                operand_type = (operand_item.get("type") or "").upper()
                if operand_type == "LITERAL" and "value" in operand_item:
                    literal_values.append(operand_item["value"])
                elif "value" in operand_item and operand_type == "":
                    literal_values.append(operand_item["value"])
            else:
                literal_values.append(operand_item)
        return literal_values
