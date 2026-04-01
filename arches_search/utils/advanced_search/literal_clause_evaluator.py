from __future__ import annotations

from typing import Any, Dict, List, NamedTuple, Optional

from django.db.models import Count, Exists, OuterRef, Q, QuerySet
from django.utils.translation import get_language

from arches_search.utils.advanced_search.predicate_builder import (
    AGGREGATE_KIND_COUNT,
    AGGREGATE_KIND_SET_EQUAL,
    AGGREGATE_KIND_SET_SUPERSET,
    AggregatePredicateSpec,
)


from arches_search.utils.advanced_search.constants import (
    CLAUSE_TYPE_LITERAL,
    CLAUSE_TYPE_RELATED,
    QUANTIFIER_ALL,
    QUANTIFIER_ANY,
    QUANTIFIER_NONE,
)


def _combine_exists(row_sets: List[QuerySet]):
    if not row_sets:
        raise ValueError("At least one row set is required.")
    combined = Exists(row_sets[0])
    for rows in row_sets[1:]:
        combined = combined | Exists(rows)
    return combined


class TileScopePredicates(NamedTuple):
    per_tile: Optional[Q]
    resource_level: Optional[Q]


def _dedupe_values(values: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(dict.fromkeys(values))


def _build_aggregate_match_rows(
    correlated_rows: QuerySet,
    aggregate_spec: AggregatePredicateSpec,
    group_field_name: str,
) -> QuerySet:
    grouped_rows = correlated_rows.values(group_field_name)

    if aggregate_spec.kind == AGGREGATE_KIND_SET_SUPERSET:
        requested_values = _dedupe_values(aggregate_spec.values)
        field_name = aggregate_spec.field_name or "value"
        return grouped_rows.annotate(
            _matched_distinct_count=Count(
                field_name,
                filter=Q(**{f"{field_name}__in": list(requested_values)}),
                distinct=True,
            )
        ).filter(_matched_distinct_count=len(requested_values))

    if aggregate_spec.kind == AGGREGATE_KIND_SET_EQUAL:
        requested_values = _dedupe_values(aggregate_spec.values)
        field_name = aggregate_spec.field_name or "value"
        return grouped_rows.annotate(
            _matched_distinct_count=Count(
                field_name,
                filter=Q(**{f"{field_name}__in": list(requested_values)}),
                distinct=True,
            ),
            _total_distinct_count=Count(field_name, distinct=True),
        ).filter(
            _matched_distinct_count=len(requested_values),
            _total_distinct_count=len(requested_values),
        )

    if aggregate_spec.kind == AGGREGATE_KIND_COUNT:
        lookup_token = aggregate_spec.lookup or "exact"
        threshold = aggregate_spec.values[0]
        return grouped_rows.annotate(_row_count=Count("pk")).filter(
            **{f"_row_count__{lookup_token}": threshold}
        )

    raise ValueError(f"Unsupported aggregate predicate kind: {aggregate_spec.kind}")


class LiteralClauseEvaluator:
    def __init__(
        self,
        search_model_registry,
        facet_registry,
        path_navigator,
        predicate_builder,
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.predicate_builder = predicate_builder

    def _build_subject_rows(
        self,
        model_class,
        subject_graph_slug: str,
        subject_node_alias: str,
    ) -> QuerySet:
        return model_class.objects.filter(
            graph_slug=subject_graph_slug,
            node_alias=subject_node_alias,
        )

    def _build_presence_subject_row_sets(
        self,
        datatype_name: str,
        subject_graph_slug: str,
        subject_node_alias: str,
    ) -> List[QuerySet]:
        return [
            self._build_subject_rows(
                model_class=model_class,
                subject_graph_slug=subject_graph_slug,
                subject_node_alias=subject_node_alias,
            )
            for model_class in self.search_model_registry.get_all_models_for_datatype(
                datatype_name
            )
        ]

    def _resolve_facet_and_model(
        self,
        subject_graph_slug: str,
        subject_node_alias: str,
        operator_token: str,
    ):
        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug,
                subject_node_alias,
            )
        )
        facet = self.facet_registry.get_facet(datatype_name, operator_token)
        model_class = facet.target_model_class
        return datatype_name, facet, model_class

    def build_anchor_exists(self, clause_payload: Dict[str, Any]) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        operand_items = clause_payload["operands"]

        datatype_name, facet, model_class = self._resolve_facet_and_model(
            subject_graph_slug=subject_graph_slug,
            subject_node_alias=subject_node_alias,
            operator_token=operator_token,
        )

        if not operand_items:
            correlated_row_sets = [
                subject_rows.filter(resourceinstanceid=OuterRef("resourceinstanceid"))
                for subject_rows in self._build_presence_subject_row_sets(
                    datatype_name=datatype_name,
                    subject_graph_slug=subject_graph_slug,
                    subject_node_alias=subject_node_alias,
                )
            ]
            any_value_exists = _combine_exists(correlated_row_sets)
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name,
                operator_token,
            )
            if quantifier_token == QUANTIFIER_NONE:
                return ~any_value_exists if presence_implies_match else any_value_exists
            return any_value_exists if presence_implies_match else ~any_value_exists

        subject_rows = self._build_subject_rows(
            model_class=model_class,
            subject_graph_slug=subject_graph_slug,
            subject_node_alias=subject_node_alias,
        )
        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstanceid")
        )

        normalized_operand_items = self._localize_string_operands(
            datatype_name=datatype_name,
            operand_items=operand_items,
        )

        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=normalized_operand_items,
                anchor_resource_id_annotation=None,
                facet=facet,
            )
        )
        if isinstance(predicate_expression, AggregatePredicateSpec):
            aggregate_matches = _build_aggregate_match_rows(
                correlated_rows=correlated_rows,
                aggregate_spec=predicate_expression,
                group_field_name="resourceinstanceid",
            )

            if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
                return (
                    ~Exists(aggregate_matches)
                    if is_template_negated
                    else Exists(aggregate_matches)
                )

            if quantifier_token == QUANTIFIER_NONE:
                return (
                    Exists(aggregate_matches)
                    if is_template_negated
                    else ~Exists(aggregate_matches)
                )

            raise ValueError(f"Unsupported quantifier: {quantifier_token}")

        if quantifier_token == QUANTIFIER_ANY:
            return Exists(correlated_rows.filter(predicate_expression))

        if quantifier_token == QUANTIFIER_NONE:
            return ~Exists(correlated_rows.filter(predicate_expression))

        if quantifier_token == QUANTIFIER_ALL:
            if not is_template_negated:
                violating_rows = correlated_rows.exclude(predicate_expression)
                return Exists(correlated_rows) & ~Exists(violating_rows)

            positive_per_row = self._positive_rows_for_negated_template(
                operator_token=operator_token,
                datatype_name=datatype_name,
                operand_items=normalized_operand_items,
                correlated_rows=correlated_rows,
                predicate_expression=predicate_expression,
            )
            return Exists(correlated_rows) & ~Exists(positive_per_row)

        raise ValueError(f"Unsupported quantifier: {quantifier_token}")

    def build_child_exists(
        self,
        clause_payload: Dict[str, Any],
        correlate_field: str,
    ) -> Exists:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"]
        operand_items = clause_payload["operands"]

        datatype_name, facet, model_class = self._resolve_facet_and_model(
            subject_graph_slug=subject_graph_slug,
            subject_node_alias=subject_node_alias,
            operator_token=operator_token,
        )

        if not operand_items:
            correlated_row_sets = [
                subject_rows.filter(resourceinstanceid=OuterRef(correlate_field))
                for subject_rows in self._build_presence_subject_row_sets(
                    datatype_name=datatype_name,
                    subject_graph_slug=subject_graph_slug,
                    subject_node_alias=subject_node_alias,
                )
            ]
            any_value_exists = _combine_exists(correlated_row_sets)
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name,
                operator_token,
            )
            return any_value_exists if presence_implies_match else ~any_value_exists

        subject_rows = self._build_subject_rows(
            model_class=model_class,
            subject_graph_slug=subject_graph_slug,
            subject_node_alias=subject_node_alias,
        )
        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef(correlate_field)
        )

        normalized_operand_items = self._localize_string_operands(
            datatype_name=datatype_name,
            operand_items=operand_items,
        )

        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=normalized_operand_items,
                anchor_resource_id_annotation=None,
                facet=facet,
            )
        )
        if isinstance(predicate_expression, AggregatePredicateSpec):
            aggregate_matches = _build_aggregate_match_rows(
                correlated_rows=correlated_rows,
                aggregate_spec=predicate_expression,
                group_field_name="resourceinstanceid",
            )
            return (
                ~Exists(aggregate_matches)
                if is_template_negated
                else Exists(aggregate_matches)
            )

        if not is_template_negated:
            return Exists(correlated_rows.filter(predicate_expression))

        positive_rows = self._positive_rows_for_negated_template(
            operator_token=operator_token,
            datatype_name=datatype_name,
            operand_items=normalized_operand_items,
            correlated_rows=correlated_rows,
            predicate_expression=predicate_expression,
        )
        return ~Exists(positive_rows)

    def compute_child_rows(
        self,
        group_payload: Dict[str, Any],
        correlate_field: str,
        terminal_graph_slug: str,
    ) -> Optional[QuerySet]:
        literal_clauses: List[Dict[str, Any]] = []

        for direct_child_group in group_payload["groups"]:
            if direct_child_group["relationship"]["path"]:
                continue

            pending_groups: List[Dict[str, Any]] = [direct_child_group]
            while pending_groups:
                current_group = pending_groups.pop()
                if current_group["relationship"]["path"]:
                    continue

                for clause_payload in current_group["clauses"]:
                    clause_type_token = clause_payload["type"]
                    if clause_type_token == CLAUSE_TYPE_LITERAL:
                        clause_graph_slug, _ = clause_payload["subject"][0]
                        if clause_graph_slug != terminal_graph_slug:
                            return None
                        literal_clauses.append(clause_payload)
                    elif clause_type_token == CLAUSE_TYPE_RELATED:
                        continue
                    else:
                        continue

                pending_groups.extend(current_group["groups"])

        if not literal_clauses:
            return None

        intersected_rows: Optional[QuerySet] = None

        for clause_payload in literal_clauses:
            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = clause_payload["operator"]
            operand_items = clause_payload["operands"]

            datatype_name, facet, model_class = self._resolve_facet_and_model(
                subject_graph_slug=subject_graph_slug,
                subject_node_alias=subject_node_alias,
                operator_token=operator_token,
            )

            if not operand_items:
                presence_implies_match = self.facet_registry.presence_implies_match(
                    datatype_name,
                    operator_token,
                )
                base_row_sets = self._build_presence_subject_row_sets(
                    datatype_name=datatype_name,
                    subject_graph_slug=subject_graph_slug,
                    subject_node_alias=subject_node_alias,
                )
                if presence_implies_match:
                    predicate_rows = None
                    for base_rows in base_row_sets:
                        correlated_rows = base_rows.filter(
                            resourceinstanceid=OuterRef(correlate_field)
                        ).values("resourceinstanceid")
                        predicate_rows = (
                            correlated_rows
                            if predicate_rows is None
                            else predicate_rows.union(correlated_rows)
                        )
                else:
                    first_model_class = base_row_sets[0].model
                    predicate_rows = first_model_class.objects.none().values(
                        "resourceinstanceid"
                    )
            else:
                base_rows = self._build_subject_rows(
                    model_class=model_class,
                    subject_graph_slug=subject_graph_slug,
                    subject_node_alias=subject_node_alias,
                )
                correlated_rows = base_rows.filter(
                    resourceinstanceid=OuterRef(correlate_field)
                )
                normalized_operand_items = self._localize_string_operands(
                    datatype_name=datatype_name,
                    operand_items=operand_items,
                )

                predicate_expression, is_template_negated = (
                    self.predicate_builder.build_predicate(
                        datatype_name=datatype_name,
                        operator_token=operator_token,
                        operands=normalized_operand_items,
                        anchor_resource_id_annotation=None,
                        facet=facet,
                    )
                )
                if isinstance(predicate_expression, AggregatePredicateSpec):
                    positive_rows = _build_aggregate_match_rows(
                        correlated_rows=correlated_rows,
                        aggregate_spec=predicate_expression,
                        group_field_name="resourceinstanceid",
                    )
                    if not is_template_negated:
                        predicate_rows = positive_rows
                    else:
                        predicate_rows = (
                            correlated_rows.values("resourceinstanceid")
                            .exclude(
                                resourceinstanceid__in=positive_rows.values(
                                    "resourceinstanceid"
                                )
                            )
                            .distinct()
                        )
                else:
                    if not is_template_negated:
                        predicate_rows = correlated_rows.filter(predicate_expression)
                    else:
                        positive_rows = self._positive_rows_for_negated_template(
                            operator_token=operator_token,
                            datatype_name=datatype_name,
                            operand_items=normalized_operand_items,
                            correlated_rows=correlated_rows,
                            predicate_expression=predicate_expression,
                        )
                        predicate_rows = correlated_rows.exclude(
                            pk__in=positive_rows.values("pk")
                        )

            intersected_rows = (
                predicate_rows
                if intersected_rows is None
                else intersected_rows.filter(
                    resourceinstanceid__in=predicate_rows.values("resourceinstanceid")
                )
            )

        return intersected_rows

    def build_tile_scope_predicates(
        self,
        clause_payload: Dict[str, Any],
        tiles_for_anchor_resource: QuerySet,
        tile_id_outer_ref: Any,
    ) -> TileScopePredicates:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        operand_items = clause_payload["operands"]

        datatype_name, facet, model_class = self._resolve_facet_and_model(
            subject_graph_slug=subject_graph_slug,
            subject_node_alias=subject_node_alias,
            operator_token=operator_token,
        )

        any_tile_for_resource_q = Q(Exists(tiles_for_anchor_resource))

        if not operand_items:
            presence_subject_row_sets = self._build_presence_subject_row_sets(
                datatype_name=datatype_name,
                subject_graph_slug=subject_graph_slug,
                subject_node_alias=subject_node_alias,
            )
            resource_row_sets = [
                subject_rows.filter(resourceinstanceid=OuterRef("resourceinstanceid"))
                for subject_rows in presence_subject_row_sets
            ]
            tile_row_sets = [
                subject_rows.filter(resourceinstanceid=OuterRef("resourceinstance_id"))
                for subject_rows in presence_subject_row_sets
            ]
            any_resource_row_exists = _combine_exists(resource_row_sets)
            per_tile_presence = _combine_exists(
                [
                    tile_rows.filter(tileid=tile_id_outer_ref)
                    for tile_rows in tile_row_sets
                ]
            )
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name,
                operator_token,
            )

            if quantifier_token == QUANTIFIER_ANY:
                return TileScopePredicates(
                    per_tile=(
                        Q(per_tile_presence)
                        if presence_implies_match
                        else ~Q(per_tile_presence)
                    ),
                    resource_level=None,
                )

            if quantifier_token == QUANTIFIER_NONE:
                return TileScopePredicates(
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
            return TileScopePredicates(per_tile=None, resource_level=resource_level_q)

        subject_rows = self._build_subject_rows(
            model_class=model_class,
            subject_graph_slug=subject_graph_slug,
            subject_node_alias=subject_node_alias,
        )

        resource_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstanceid")
        )
        tile_rows = subject_rows.filter(
            resourceinstanceid=OuterRef("resourceinstance_id")
        )

        normalized_operand_items = self._localize_string_operands(
            datatype_name=datatype_name,
            operand_items=operand_items,
        )

        predicate_expression, is_template_negated = (
            self.predicate_builder.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=normalized_operand_items,
                anchor_resource_id_annotation=None,
                facet=facet,
            )
        )
        if isinstance(predicate_expression, AggregatePredicateSpec):
            resource_level_matches = _build_aggregate_match_rows(
                correlated_rows=resource_rows,
                aggregate_spec=predicate_expression,
                group_field_name="resourceinstanceid",
            )
            per_tile_matches = _build_aggregate_match_rows(
                correlated_rows=tile_rows.filter(tileid=tile_id_outer_ref),
                aggregate_spec=predicate_expression,
                group_field_name="tileid",
            )

            if quantifier_token == QUANTIFIER_ANY:
                per_tile_q = Q(Exists(per_tile_matches))
                return TileScopePredicates(
                    per_tile=(~per_tile_q if is_template_negated else per_tile_q),
                    resource_level=None,
                )

            if quantifier_token == QUANTIFIER_NONE:
                resource_level_q = Q(Exists(resource_level_matches))
                return TileScopePredicates(
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
                    return TileScopePredicates(
                        per_tile=None,
                        resource_level=(
                            Q(~Exists(tiles_missing_match)) & any_tile_for_resource_q
                        ),
                    )

                tiles_with_positive_match = tiles_for_anchor_resource.filter(
                    Exists(per_tile_matches)
                )
                return TileScopePredicates(
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
            return TileScopePredicates(
                per_tile=Q(Exists(per_tile_matches)),
                resource_level=None,
            )

        if quantifier_token == QUANTIFIER_NONE:
            resource_level_matches = resource_rows.filter(predicate_expression)
            return TileScopePredicates(
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
                return TileScopePredicates(
                    per_tile=None,
                    resource_level=(
                        Q(~Exists(tiles_missing_match)) & any_tile_for_resource_q
                    ),
                )

            positive_per_tile_rows = self._positive_rows_for_negated_template(
                operator_token=operator_token,
                datatype_name=datatype_name,
                operand_items=normalized_operand_items,
                correlated_rows=tile_rows.filter(tileid=tile_id_outer_ref),
                predicate_expression=predicate_expression,
            )
            tiles_with_violations = tiles_for_anchor_resource.filter(
                Exists(positive_per_tile_rows)
            )
            return TileScopePredicates(
                per_tile=None,
                resource_level=(
                    Q(~Exists(tiles_with_violations)) & any_tile_for_resource_q
                ),
            )

        raise ValueError(f"Unsupported quantifier: {quantifier_token}")

    def _positive_rows_for_negated_template(
        self,
        operator_token: str,
        datatype_name: str,
        operand_items: List[Dict[str, Any]],
        correlated_rows: QuerySet,
        predicate_expression: Q,
    ) -> QuerySet:
        positive_facet = self.facet_registry.resolve_positive_facet(
            operator_token,
            datatype_name,
        )

        if positive_facet is not None:
            positive_expression, _ = self.predicate_builder.build_predicate(
                datatype_name,
                positive_facet.operator,
                operand_items,
                facet=positive_facet,
            )
            return correlated_rows.filter(positive_expression)

        if predicate_expression.negated:
            return correlated_rows.filter(~predicate_expression)

        return correlated_rows.exclude(predicate_expression)

    def _localize_string_operands(
        self,
        datatype_name: str,
        operand_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if datatype_name.lower() != "string":
            return operand_items

        language_code = get_language()
        short_language_code = None

        if language_code:
            short_language_code = language_code.split("-")[0]

        normalized_items: List[Dict[str, Any]] = []

        for operand_item in operand_items:
            raw_value = operand_item.get("value")

            if isinstance(raw_value, dict) and raw_value:
                chosen_value = None

                if language_code and language_code in raw_value:
                    chosen_value = raw_value[language_code]
                elif short_language_code and short_language_code in raw_value:
                    chosen_value = raw_value[short_language_code]
                else:
                    chosen_value = next(iter(raw_value.values()))

                normalized_items.append({**operand_item, "value": chosen_value})
            else:
                normalized_items.append(operand_item)

        return normalized_items
