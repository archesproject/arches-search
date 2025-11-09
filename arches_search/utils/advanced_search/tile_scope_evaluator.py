from typing import Any, Dict, List
from django.db.models import Exists, OuterRef, Q, QuerySet


LOGIC_AND = "AND"
LOGIC_OR = "OR"

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_LITERAL = "LITERAL"


class TileScopeEvaluator:
    def __init__(
        self, literal_clause_evaluator, facet_registry, path_navigator
    ) -> None:
        self.literal_clause_evaluator = literal_clause_evaluator
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator

    def compose_group_predicate(
        self,
        group_payload: Dict[str, Any],
        tiles_for_anchor_resource: QuerySet,
    ) -> Q:
        logic_token = group_payload["logic"].upper()
        tile_id_outer_ref = OuterRef("tileid")
        resource_has_any_tile_q = Q(Exists(tiles_for_anchor_resource))

        per_tile_predicates: List[Q] = []
        resource_level_predicates: List[Q] = []

        for clause_payload in group_payload["clauses"]:
            if clause_payload["type"].upper() != CLAUSE_TYPE_LITERAL:
                continue

            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = clause_payload["operator"].upper()
            quantifier_token = clause_payload["quantifier"].upper()
            operand_items = clause_payload["operands"]

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
                graph_slug=subject_graph_slug,
                node_alias=subject_node_alias,
            )
            resource_rows = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            )
            tile_rows = subject_rows.filter(
                resourceinstanceid=OuterRef("resourceinstance_id")
            )

            if not operand_items:
                self._evaluate_zero_arity_clause(
                    per_tile_predicates,
                    resource_level_predicates,
                    tiles_for_anchor_resource,
                    tile_rows,
                    resource_rows,
                    tile_id_outer_ref,
                    resource_has_any_tile_q,
                    quantifier_token,
                    self.facet_registry.zero_arity_presence_is_match(
                        datatype_name, operator_token
                    ),
                )
                continue

            predicate_expression, is_template_negated = (
                self.literal_clause_evaluator.operand_compiler.build_predicate(
                    datatype_name=datatype_name,
                    operator_token=operator_token,
                    operands=operand_items,
                    anchor_resource_id_annotation=None,
                )
            )

            self._evaluate_operand_clause(
                per_tile_predicates,
                resource_level_predicates,
                tiles_for_anchor_resource,
                resource_has_any_tile_q,
                tile_rows,
                resource_rows,
                tile_id_outer_ref,
                quantifier_token,
                predicate_expression,
                is_template_negated,
                operator_token,
                datatype_name,
                operand_items,
            )

        per_tile_q = self._combine_per_tile_predicates(
            logic_token,
            tiles_for_anchor_resource,
            per_tile_predicates,
        )

        if not resource_level_predicates:
            return per_tile_q

        resource_level_q = self._combine_resource_level_predicates(
            logic_token,
            resource_level_predicates,
        )

        if logic_token == "AND":
            return per_tile_q & resource_level_q
        else:
            return per_tile_q | resource_level_q

    def _evaluate_zero_arity_clause(
        self,
        per_tile_predicates: List[Q],
        resource_level_predicates: List[Q],
        tiles_for_anchor_resource: QuerySet,
        tile_rows: QuerySet,
        resource_rows: QuerySet,
        tile_id_outer_ref,
        resource_has_any_tile_q: Q,
        quantifier_token: str,
        presence_implies_match: bool,
    ) -> None:
        if quantifier_token == QUANTIFIER_ANY:
            present_in_tile = Q(Exists(tile_rows.filter(tileid=tile_id_outer_ref)))
            per_tile_predicates.append(
                present_in_tile if presence_implies_match else ~present_in_tile
            )
            return

        if quantifier_token == QUANTIFIER_NONE:
            resource_level_predicates.append(
                Q(~Exists(resource_rows))
                if presence_implies_match
                else Q(Exists(resource_rows))
            )
            return

        tiles_missing_match = tiles_for_anchor_resource.filter(
            ~Exists(tile_rows.filter(tileid=tile_id_outer_ref))
        )
        resource_level_predicates.append(
            (Q(~Exists(tiles_missing_match)) & resource_has_any_tile_q)
            if presence_implies_match
            else Q(~Exists(tiles_for_anchor_resource))
        )

    def _evaluate_operand_clause(
        self,
        per_tile_predicates: List[Q],
        resource_level_predicates: List[Q],
        tiles_for_anchor_resource: QuerySet,
        resource_has_any_tile_q: Q,
        tile_rows: QuerySet,
        resource_rows: QuerySet,
        tile_id_outer_ref,
        quantifier_token: str,
        predicate_expression: Any,
        is_template_negated: bool,
        operator_token: str,
        datatype_name: str,
        operand_items: List[Dict[str, Any]],
    ) -> None:
        if isinstance(predicate_expression, Q):
            resource_matches = resource_rows.filter(predicate_expression)
            tile_matches = tile_rows.filter(predicate_expression).filter(
                tileid=tile_id_outer_ref
            )
        else:
            resource_matches = resource_rows.filter(**predicate_expression)
            tile_matches = tile_rows.filter(**predicate_expression).filter(
                tileid=tile_id_outer_ref
            )

        if quantifier_token == QUANTIFIER_ANY:
            per_tile_predicates.append(Q(Exists(tile_matches)))
            return

        if quantifier_token == QUANTIFIER_NONE:
            resource_level_predicates.append(Q(~Exists(resource_matches)))
            return

        if not is_template_negated:
            tiles_missing_match = tiles_for_anchor_resource.filter(
                ~Exists(tile_matches)
            )
            resource_level_predicates.append(
                Q(~Exists(tiles_missing_match)) & resource_has_any_tile_q
            )
            return

        positive_tile_matches = self._derive_positive_tile_matches(
            tile_rows,
            tile_id_outer_ref,
            predicate_expression,
            operator_token,
            datatype_name,
            operand_items,
        )
        tiles_with_violations = tiles_for_anchor_resource.filter(
            Exists(positive_tile_matches)
        )
        resource_level_predicates.append(
            Q(~Exists(tiles_with_violations)) & resource_has_any_tile_q
        )

    def _derive_positive_tile_matches(
        self,
        tile_rows: QuerySet,
        tile_id_outer_ref,
        predicate_expression: Any,
        operator_token: str,
        datatype_name: str,
        operand_items: List[Dict[str, Any]],
    ) -> QuerySet:
        positive_facet = self.facet_registry.get_positive_facet_for(
            operator_token, datatype_name
        )

        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name,
                positive_facet.operator,
                "value",
                self.literal_clause_evaluator.operand_compiler.literal_values_only(
                    operand_items
                ),
            )
            if isinstance(positive_expression, Q):
                return tile_rows.filter(positive_expression).filter(
                    tileid=tile_id_outer_ref
                )
            return tile_rows.filter(**positive_expression).filter(
                tileid=tile_id_outer_ref
            )

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            return tile_rows.filter(~predicate_expression).filter(
                tileid=tile_id_outer_ref
            )

        if isinstance(predicate_expression, Q):
            return tile_rows.exclude(predicate_expression).filter(
                tileid=tile_id_outer_ref
            )

        return tile_rows.exclude(**predicate_expression).filter(
            tileid=tile_id_outer_ref
        )

    def _combine_per_tile_predicates(
        self,
        logic_token: str,
        tiles_for_anchor_resource: QuerySet,
        per_tile_predicates: List[Q],
    ) -> Q:
        if not per_tile_predicates:
            return Q()

        if logic_token == LOGIC_AND:
            tiles_satisfying_all = tiles_for_anchor_resource

            for per_tile_q in per_tile_predicates:
                tiles_satisfying_all = tiles_satisfying_all.filter(per_tile_q)

            return Q(Exists(tiles_satisfying_all))

        union_q = Q(pk__in=[])

        for per_tile_q in per_tile_predicates:
            union_q |= per_tile_q

        return Q(Exists(tiles_for_anchor_resource.filter(union_q)))

    def _combine_resource_level_predicates(
        self,
        logic_token: str,
        resource_level_predicates: List[Q],
    ) -> Q:
        if logic_token == LOGIC_AND:
            combined = Q()

            for predicate in resource_level_predicates:
                combined &= predicate

            return combined

        if logic_token == LOGIC_OR:
            combined = Q()

            for predicate in resource_level_predicates:
                combined |= predicate

            return combined
