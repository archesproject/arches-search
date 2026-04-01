from typing import Any, Dict, List
from django.db.models import Exists, Q, QuerySet, OuterRef

from arches_search.utils.advanced_search.constants import (
    CLAUSE_TYPE_LITERAL,
    LOGIC_AND,
    LOGIC_OR,
)


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
        logic_connector_token = group_payload["logic"].upper()

        tile_identifier_outer_ref = OuterRef("tileid")

        tile_scoped_predicates: List[Q] = []
        resource_scoped_predicates: List[Q] = []

        for clause_payload in group_payload["clauses"]:
            if clause_payload["type"] != CLAUSE_TYPE_LITERAL:
                continue

            tile_scope_predicates = (
                self.literal_clause_evaluator.build_tile_scope_predicates(
                    clause_payload=clause_payload,
                    tiles_for_anchor_resource=tiles_for_anchor_resource,
                    tile_id_outer_ref=tile_identifier_outer_ref,
                )
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

        combined_resource_scoped_predicate = self._combine_resource_scoped_predicates(
            logic_connector_token,
            resource_scoped_predicates,
        )

        if logic_connector_token == LOGIC_AND:
            return combined_per_tile_predicate & combined_resource_scoped_predicate

        if logic_connector_token == LOGIC_OR:
            return combined_per_tile_predicate | combined_resource_scoped_predicate

        return combined_per_tile_predicate

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

    def _combine_resource_scoped_predicates(
        self,
        logic_connector_token: str,
        resource_scoped_predicates: List[Q],
    ) -> Q:
        combined_predicate = Q()

        if logic_connector_token == LOGIC_AND:
            for predicate in resource_scoped_predicates:
                combined_predicate &= predicate

        elif logic_connector_token == LOGIC_OR:
            for predicate in resource_scoped_predicates:
                combined_predicate |= predicate

        return combined_predicate
