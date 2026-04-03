import json
from typing import Any, List, Optional, Tuple

from django.contrib.gis.geos import GEOSGeometry
from django.db.models import OuterRef, Q, Subquery
from django.utils.translation import gettext as _

from arches_search.utils.advanced_search.constants import (
    AGGREGATE_KIND_SET_EQUAL,
    AGGREGATE_KIND_SET_SUPERSET,
    OPERAND_TYPE_GEO_LITERAL,
    OPERAND_TYPE_LITERAL,
    OPERAND_TYPE_PATH,
)
from arches_search.utils.advanced_search.specs import (
    AggregatePredicateSpec,
)


class PredicateBuilder:
    def __init__(self, facet_registry, path_navigator) -> None:
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator

    def build_predicate(
        self,
        datatype_name: str,
        operator_token: str,
        operands: List[Any],
        anchor_resource_id_annotation: Optional[str] = None,
        facet=None,
    ) -> Tuple[Q | AggregatePredicateSpec, bool]:
        normalized_operands = self._normalize_operands(
            operands=operands,
            anchor_resource_id_annotation=anchor_resource_id_annotation,
        )

        if facet is None:
            facet = self.facet_registry.get_facet(datatype_name, operator_token)

        is_template_negated = bool(facet.is_orm_template_negated)
        predicate_expression = self._build_expression_from_template(
            facet=facet,
            operands=normalized_operands,
        )

        if is_template_negated:
            if isinstance(predicate_expression, AggregatePredicateSpec):
                return predicate_expression, True
            return ~predicate_expression, True

        return predicate_expression, False

    def _build_expression_from_template(
        self, facet, operands: List[Any]
    ) -> Q | AggregatePredicateSpec:
        orm_template = facet.orm_template

        aggregate_spec = self._build_aggregate_spec(
            orm_template=orm_template,
            operands=operands,
        )
        if aggregate_spec is not None:
            return aggregate_spec

        if orm_template.startswith("AND:") or orm_template.startswith("OR:"):
            return self._build_compound_q(
                orm_template=orm_template,
                operands=operands,
            )

        if facet.arity == 0:
            value_for_lookup = True
        elif facet.arity == 1:
            value_for_lookup = operands[0]
        else:
            value_for_lookup = operands

        return Q(**{orm_template: value_for_lookup})

    def _build_aggregate_spec(
        self,
        orm_template: str,
        operands: List[Any],
    ) -> AggregatePredicateSpec | None:
        if orm_template.startswith("HAVING_ALL:"):
            _, field_name, operand_token = orm_template.split(":", 2)
            return AggregatePredicateSpec(
                kind=AGGREGATE_KIND_SET_SUPERSET,
                field_name=field_name,
                values=self._coerce_aggregate_values(
                    self._resolve_operand_token(operand_token, operands)
                ),
            )

        if orm_template.startswith("HAVING_ONLY:"):
            _, field_name, operand_token = orm_template.split(":", 2)
            return AggregatePredicateSpec(
                kind=AGGREGATE_KIND_SET_EQUAL,
                field_name=field_name,
                values=self._coerce_aggregate_values(
                    self._resolve_operand_token(operand_token, operands)
                ),
            )

        return None

    def _build_compound_q(
        self,
        orm_template: str,
        operands: List[Any],
    ) -> Q:
        logic_token, raw_conditions = orm_template.split(":", 1)
        condition_expressions = []

        for raw_condition in raw_conditions.split(";"):
            lookup_key, operand_token = raw_condition.rsplit(":", 1)
            operand_value = self._resolve_operand_token(operand_token, operands)
            condition_expressions.append(Q(**{lookup_key: operand_value}))

        if logic_token == "AND":
            combined_q = condition_expressions[0]
            for condition_expression in condition_expressions[1:]:
                combined_q &= condition_expression
            return combined_q

        if logic_token == "OR":
            combined_q = condition_expressions[0]
            for condition_expression in condition_expressions[1:]:
                combined_q |= condition_expression
            return combined_q

        raise ValueError(
            _("Unsupported logical template prefix: {prefix}").format(
                prefix=logic_token
            )
        )

    def _resolve_operand_token(self, operand_token: str, operands: List[Any]) -> Any:
        token = operand_token.strip()

        if token in {"{value}", "{value0}"}:
            return operands[0]
        if token == "{value1}":
            return operands[1]

        raise ValueError(
            _("Unsupported operand placeholder in ORM template: {token}").format(
                token=token
            )
        )

    def _coerce_aggregate_values(self, raw_value: Any) -> tuple[Any, ...]:
        match raw_value:
            case None:
                return ()
            case tuple():
                return raw_value
            case list() | set():
                return tuple(raw_value)
            case _:
                return (raw_value,)

    def _normalize_operands(
        self,
        operands: List[Any],
        anchor_resource_id_annotation: Optional[str],
    ) -> List[Any]:
        if not operands:
            return []

        has_path_operand = any(
            operand_item["type"].upper() == OPERAND_TYPE_PATH
            for operand_item in operands
        )
        if has_path_operand and anchor_resource_id_annotation is None:
            raise ValueError(
                _("anchor_resource_id_annotation is required for PATH operands")
            )

        normalized_values: List[Any] = []
        for operand_item in operands:
            operand_type = operand_item["type"].upper()

            if operand_type == OPERAND_TYPE_LITERAL:
                normalized_values.append(operand_item["value"])
                continue

            if operand_type == OPERAND_TYPE_GEO_LITERAL:
                value = operand_item["value"]
                if isinstance(value, dict):
                    value = json.dumps(value)
                normalized_values.append(GEOSGeometry(value, srid=4326))
                continue

            if operand_type == OPERAND_TYPE_PATH:
                _, _, related_rows = self.path_navigator.build_path_queryset(
                    operand_item["value"]
                )
                related_scalar_value = Subquery(
                    related_rows.filter(
                        resourceinstanceid=OuterRef(anchor_resource_id_annotation)
                    ).values("value")[:1]
                )
                normalized_values.append(related_scalar_value)
                continue

            raise ValueError(
                _("Unsupported operand type: {type}").format(type=operand_type)
            )

        return normalized_values
