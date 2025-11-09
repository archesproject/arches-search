from typing import Any, Dict, List
from django.db.models import Exists, OuterRef, Q, QuerySet

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"


class TileScopeEvaluator:
    def __init__(self, *, literal_evaluator, facet_registry, path_navigator) -> None:
        self.literal_evaluator = literal_evaluator
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator

    def compose_group_predicate(
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

        if any(
            ((child.get("relationship") or {}).get("path"))
            for child in (group_payload.get("groups") or [])
        ):
            return Q(pk__in=[])

        use_and_logic = (group_payload.get("logic") or "AND").upper() == "AND"

        per_tile_exists_conditions: List[Q] = []
        resource_level_conditions: List[Q] = []

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
            model_class = (
                self.path_navigator.search_model_registry.get_model_for_datatype(
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
                self.literal_evaluator.operand_compiler.build_predicate(
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
                    self.literal_evaluator.operand_compiler.literal_values_only(
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
