import json
from typing import Any, List, Optional, Tuple
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Subquery, OuterRef, Q
from django.utils.translation import gettext as _

TYPE_LITERAL = "LITERAL"
TYPE_PATH = "PATH"
TYPE_GEO_LITERAL = "GEO_LITERAL"


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
    ) -> Tuple[Q | dict, bool]:
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
            if isinstance(predicate_expression, Q):
                return ~predicate_expression, True
            return ~Q(**predicate_expression), True

        return predicate_expression, False

    def _build_expression_from_template(self, facet, operands: List[Any]) -> Q | dict:
        orm_template = facet.orm_template
        target_model_class = facet.target_model_class

        if orm_template.startswith("AND:") or orm_template.startswith("OR:"):
            return self._build_compound_q(
                orm_template=orm_template,
                operands=operands,
                target_model_class=target_model_class,
            )

        lookup_key = self._resolve_lookup_key(
            template=orm_template,
            target_model_class=target_model_class,
        )

        if facet.arity == 0:
            value_for_lookup = True
        elif facet.arity == 1:
            value_for_lookup = operands[0]
        else:
            value_for_lookup = operands

        return {lookup_key: value_for_lookup}

    def _build_compound_q(
        self,
        orm_template: str,
        operands: List[Any],
        target_model_class,
    ) -> Q:
        logic_token, raw_conditions = orm_template.split(":", 1)
        condition_expressions = []

        for raw_condition in raw_conditions.split(";"):
            lookup_template, operand_token = raw_condition.rsplit(":", 1)
            lookup_key = self._resolve_lookup_key(
                template=lookup_template,
                target_model_class=target_model_class,
            )
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

    def _resolve_lookup_key(self, template: str, target_model_class) -> str:
        resolved_template = template
        field_aliases = self._get_field_aliases(target_model_class)

        for placeholder, field_name in field_aliases.items():
            resolved_template = resolved_template.replace(placeholder, field_name)

        if "{" in resolved_template or "}" in resolved_template:
            raise ValueError(
                _("Unsupported field placeholder in ORM template: {template}").format(
                    template=template
                )
            )

        return resolved_template

    def _get_field_aliases(self, target_model_class) -> dict[str, str]:
        if target_model_class is None:
            return {"{col}": "value"}

        field_names = {
            field.name
            for field in target_model_class._meta.get_fields()
            if getattr(field, "name", None)
        }

        aliases = {}
        if "value" in field_names:
            aliases["{col}"] = "value"
        if "geom" in field_names:
            aliases["{col}"] = "geom"
        if "start_value" in field_names:
            aliases["{col_start}"] = "start_value"
        if "end_value" in field_names:
            aliases["{col_end}"] = "end_value"
        return aliases

    def _resolve_operand_token(self, operand_token: str, operands: List[Any]) -> Any:
        token = operand_token.strip()

        if token in {"{value}", "{p0}", "{value0}"}:
            return operands[0]
        if token in {"{p1}", "{value1}"}:
            return operands[1]
        if token in {"{p2}", "{value2}"}:
            return operands[2]

        raise ValueError(
            _("Unsupported operand placeholder in ORM template: {token}").format(
                token=token
            )
        )

    def _normalize_operands(
        self,
        operands: List[Any],
        anchor_resource_id_annotation: Optional[str],
    ) -> List[Any]:
        if not operands:
            return []

        has_path_operand = any(
            operand_item["type"].upper() == TYPE_PATH for operand_item in operands
        )
        if has_path_operand and anchor_resource_id_annotation is None:
            raise ValueError(
                _("anchor_resource_id_annotation is required for PATH operands")
            )

        normalized_values: List[Any] = []
        for operand_item in operands:
            operand_type = operand_item["type"].upper()

            if operand_type == TYPE_LITERAL:
                normalized_values.append(operand_item["value"])
                continue

            if operand_type == TYPE_GEO_LITERAL:
                value = operand_item["value"]
                if isinstance(value, dict):
                    value = json.dumps(value)
                normalized_values.append(GEOSGeometry(value, srid=4326))
                continue

            if operand_type == TYPE_PATH:
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
