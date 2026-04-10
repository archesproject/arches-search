from typing import Any, Dict, List

from django.db.models import Exists, OuterRef, Q, QuerySet

from arches_search.utils.advanced_search.aggregate_predicate_runtime import (
    build_grouped_rows_matching_aggregate_predicate,
)
from arches_search.utils.advanced_search.constants import (
    CLAUSE_TYPE_LITERAL,
    LOGIC_AND,
    LOGIC_OR,
    QUANTIFIER_ALL,
    QUANTIFIER_ANY,
    QUANTIFIER_NONE,
)
from arches_search.utils.advanced_search.specs import (
    AggregatePredicateSpec,
    TileScopePredicateSet,
)
from arches_search.utils.advanced_search.constants import SUBJECT_TYPE_SEARCH_MODELS


class TileScopeEvaluator:
    def __init__(self, literal_clause_evaluator) -> None:
        self.literal_clause_evaluator = literal_clause_evaluator

    def build_tile_scope_predicates(
        self,
        clause_payload: Dict[str, Any],
        tiles_for_anchor_resource: QuerySet,
        tile_id_outer_ref: Any,
    ) -> TileScopePredicateSet:
        subject = clause_payload["subject"]
        if subject.get("type") == SUBJECT_TYPE_SEARCH_MODELS:
            raise NotImplementedError(
                "search_models subject is not supported with TILE scope."
            )
        subject_graph_slug = subject["graph_slug"]
        subject_node_alias = subject["node_alias"]
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        operand_items = clause_payload["operands"]

        datatype_name, facet, model_class = (
            self.literal_clause_evaluator.resolve_facet_and_model(
                subject_graph_slug=subject_graph_slug,
                subject_node_alias=subject_node_alias,
                operator_token=operator_token,
            )
        )

        any_tile_for_resource_q = Q(Exists(tiles_for_anchor_resource))

        if not operand_items:
            presence_subject_row_sets = (
                self.literal_clause_evaluator.build_presence_subject_row_sets(
                    datatype_name=datatype_name,
                    subject_graph_slug=subject_graph_slug,
                    subject_node_alias=subject_node_alias,
                )
            )
            resource_row_sets = [
                subject_rows.filter(resourceinstanceid=OuterRef("resourceinstanceid"))
                for subject_rows in presence_subject_row_sets
            ]
            tile_row_sets = [
                subject_rows.filter(resourceinstanceid=OuterRef("resourceinstance_id"))
                for subject_rows in presence_subject_row_sets
            ]
            any_resource_row_exists = Exists(resource_row_sets[0])
            for current_row_set in resource_row_sets[1:]:
                any_resource_row_exists = any_resource_row_exists | Exists(
                    current_row_set
                )

            per_tile_row_sets = [
                tile_rows.filter(tileid=tile_id_outer_ref)
                for tile_rows in tile_row_sets
            ]
            per_tile_presence = Exists(per_tile_row_sets[0])
            for current_row_set in per_tile_row_sets[1:]:
                per_tile_presence = per_tile_presence | Exists(current_row_set)
            presence_implies_match = (
                self.literal_clause_evaluator.facet_registry.presence_implies_match(
                    datatype_name,
                    operator_token,
                )
            )

            if quantifier_token == QUANTIFIER_ANY:
                return TileScopePredicateSet(
                    per_tile=(
                        Q(per_tile_presence)
                        if presence_implies_match
                        else ~Q(per_tile_presence)
                    ),
                    resource_level=None,
                )

            if quantifier_token == QUANTIFIER_NONE:
                return TileScopePredicateSet(
                    per_tile=None,
                    resource_level=(
                        Q(~any_resource_row_exists)
                        if presence_implies_match
                        else Q(any_resource_row_exists)
                    ),
                )

            tiles_missing_presence = tiles_for_anchor_resource.filter(
                ~per_tile_presence
            )
            resource_level_q = (
                Q(~Exists(tiles_missing_presence)) & any_tile_for_resource_q
                if presence_implies_match
                else Q(~Exists(tiles_for_anchor_resource))
            )
            return TileScopePredicateSet(
                per_tile=None,
                resource_level=resource_level_q,
            )

        subject_rows = self.literal_clause_evaluator.build_subject_rows(
            model_class=model_class,
            subject_graph_slug=subject_graph_slug,
            subject_node_alias=subject_node_alias,
        )

        normalized_operand_items, filter_value = (
            model_class.normalize_operands(operand_items)
            if hasattr(model_class, "normalize_operands")
            else (list(operand_items), None)
        )
        resource_rows = facet.filter_rows(
            subject_rows.filter(resourceinstanceid=OuterRef("resourceinstanceid")),
            filter_value,
        )
        tile_rows = facet.filter_rows(
            subject_rows.filter(resourceinstanceid=OuterRef("resourceinstance_id")),
            filter_value,
        )

        predicate_expression, is_template_negated = (
            self.literal_clause_evaluator.predicate_builder.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=normalized_operand_items,
                anchor_resource_id_annotation=None,
                facet=facet,
            )
        )
        if isinstance(predicate_expression, AggregatePredicateSpec):
            resource_level_matches = build_grouped_rows_matching_aggregate_predicate(
                correlated_rows=resource_rows,
                aggregate_predicate_spec=predicate_expression,
                grouping_field_name="resourceinstanceid",
            )
            per_tile_matches = build_grouped_rows_matching_aggregate_predicate(
                correlated_rows=tile_rows.filter(tileid=tile_id_outer_ref),
                aggregate_predicate_spec=predicate_expression,
                grouping_field_name="tileid",
            )

            if quantifier_token == QUANTIFIER_ANY:
                per_tile_q = Q(Exists(per_tile_matches))
                return TileScopePredicateSet(
                    per_tile=(~per_tile_q if is_template_negated else per_tile_q),
                    resource_level=None,
                )

            if quantifier_token == QUANTIFIER_NONE:
                resource_level_q = Q(Exists(resource_level_matches))
                return TileScopePredicateSet(
                    per_tile=None,
                    resource_level=(
                        resource_level_q if is_template_negated else ~resource_level_q
                    ),
                )

            if quantifier_token == QUANTIFIER_ALL:
                if not is_template_negated:
                    tiles_missing_match = tiles_for_anchor_resource.filter(
                        ~Exists(per_tile_matches)
                    )
                    return TileScopePredicateSet(
                        per_tile=None,
                        resource_level=(
                            Q(~Exists(tiles_missing_match)) & any_tile_for_resource_q
                        ),
                    )

                tiles_with_positive_match = tiles_for_anchor_resource.filter(
                    Exists(per_tile_matches)
                )
                return TileScopePredicateSet(
                    per_tile=None,
                    resource_level=(
                        Q(~Exists(tiles_with_positive_match)) & any_tile_for_resource_q
                    ),
                )

            raise ValueError(f"Unsupported quantifier: {quantifier_token}")

        if quantifier_token == QUANTIFIER_ANY:
            per_tile_matches = tile_rows.filter(predicate_expression).filter(
                tileid=tile_id_outer_ref
            )
            return TileScopePredicateSet(
                per_tile=Q(Exists(per_tile_matches)),
                resource_level=None,
            )

        if quantifier_token == QUANTIFIER_NONE:
            resource_level_matches = resource_rows.filter(predicate_expression)
            return TileScopePredicateSet(
                per_tile=None,
                resource_level=Q(~Exists(resource_level_matches)),
            )

        if quantifier_token == QUANTIFIER_ALL:
            if not is_template_negated:
                per_tile_matches = tile_rows.filter(predicate_expression).filter(
                    tileid=tile_id_outer_ref
                )
                tiles_missing_match = tiles_for_anchor_resource.filter(
                    ~Exists(per_tile_matches)
                )
                return TileScopePredicateSet(
                    per_tile=None,
                    resource_level=(
                        Q(~Exists(tiles_missing_match)) & any_tile_for_resource_q
                    ),
                )

            positive_per_tile_rows = (
                self.literal_clause_evaluator.positive_rows_for_negated_template(
                    operator_token=operator_token,
                    datatype_name=datatype_name,
                    operand_items=normalized_operand_items,
                    correlated_rows=tile_rows.filter(tileid=tile_id_outer_ref),
                    predicate_expression=predicate_expression,
                )
            )
            tiles_with_violations = tiles_for_anchor_resource.filter(
                Exists(positive_per_tile_rows)
            )
            return TileScopePredicateSet(
                per_tile=None,
                resource_level=(
                    Q(~Exists(tiles_with_violations)) & any_tile_for_resource_q
                ),
            )

        raise ValueError(f"Unsupported quantifier: {quantifier_token}")

    def compose_group_predicate(
        self,
        group_payload: Dict[str, Any],
        tiles_for_anchor_resource: QuerySet,
    ) -> Q:
        logic_connector_token = group_payload["logic"].upper()

        tile_identifier_outer_ref = OuterRef("tileid")

        tile_scoped_predicates: List[Q] = []
        resource_scoped_predicates: List[Q] = []

        for clause_payload in group_payload["clauses"]:
            if clause_payload["type"] != CLAUSE_TYPE_LITERAL:
                continue

            tile_scope_predicates = self.build_tile_scope_predicates(
                clause_payload=clause_payload,
                tiles_for_anchor_resource=tiles_for_anchor_resource,
                tile_id_outer_ref=tile_identifier_outer_ref,
            )

            if tile_scope_predicates.per_tile is not None:
                tile_scoped_predicates.append(tile_scope_predicates.per_tile)

            if tile_scope_predicates.resource_level is not None:
                resource_scoped_predicates.append(tile_scope_predicates.resource_level)

        combined_per_tile_predicate = self._combine_tile_scoped_predicates(
            logic_connector_token,
            tiles_for_anchor_resource,
            tile_scoped_predicates,
        )

        if not resource_scoped_predicates:
            return combined_per_tile_predicate

        if logic_connector_token == LOGIC_AND:
            combined_resource_scoped_predicate = Q()
            for predicate in resource_scoped_predicates:
                combined_resource_scoped_predicate &= predicate
            return combined_per_tile_predicate & combined_resource_scoped_predicate

        combined_resource_scoped_predicate = Q(pk__in=[])
        for predicate in resource_scoped_predicates:
            combined_resource_scoped_predicate |= predicate
        return combined_per_tile_predicate | combined_resource_scoped_predicate

    def _combine_tile_scoped_predicates(
        self,
        logic_connector_token: str,
        tiles_for_anchor_resource: QuerySet,
        tile_scoped_predicates: List[Q],
    ) -> Q:
        if not tile_scoped_predicates:
            return Q()

        if logic_connector_token == LOGIC_AND:
            tiles_satisfying_all_predicates = tiles_for_anchor_resource

            for per_tile_predicate in tile_scoped_predicates:
                tiles_satisfying_all_predicates = (
                    tiles_satisfying_all_predicates.filter(per_tile_predicate)
                )

            return Q(Exists(tiles_satisfying_all_predicates))

        if logic_connector_token == LOGIC_OR:
            union_predicate_across_tiles = Q(pk__in=[])

            for per_tile_predicate in tile_scoped_predicates:
                union_predicate_across_tiles |= per_tile_predicate

            return Q(
                Exists(tiles_for_anchor_resource.filter(union_predicate_across_tiles))
            )

        return Q()
