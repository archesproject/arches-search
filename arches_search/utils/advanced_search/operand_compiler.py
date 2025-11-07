from __future__ import annotations
from typing import Any, List, Optional, Tuple

from django.db.models import Q, Subquery, OuterRef


class OperandCompiler:
    def __init__(self, facet_registry, path_navigator) -> None:
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator

    def build_predicate(
        self,
        datatype_name: str,
        operator_token: str,
        operands: List[Any],
        *,
        anchor_resource_id_annotation: Optional[str] = None,
    ) -> Tuple[Any, bool]:
        parameters = self._normalize_operands(
            operands=operands,
            anchor_resource_id_annotation=anchor_resource_id_annotation,
        )
        predicate_expression, is_template_negated = self.facet_registry.predicate(
            datatype_name, operator_token, "value", parameters
        )
        return predicate_expression, is_template_negated

    def literal_values_only(self, operands: List[Any]) -> List[Any]:
        literal_values: List[Any] = []
        for operand_item in operands or []:
            if isinstance(operand_item, dict):
                operand_type = (operand_item.get("type") or "").upper()
                if operand_type == "PATH":
                    continue
                if "value" in operand_item:
                    literal_values.append(operand_item["value"])
            else:
                literal_values.append(operand_item)
        return literal_values

    def _normalize_operands(
        self,
        operands: List[Any],
        *,
        anchor_resource_id_annotation: Optional[str],
    ) -> List[Any]:
        if not operands:
            return []

        normalized: List[Any] = []
        for operand_item in operands:
            if isinstance(operand_item, dict):
                operand_type = (operand_item.get("type") or "").upper()
                if operand_type == "PATH":
                    path_segments = operand_item["value"]
                    _, _, rhs_rows = self.path_navigator.build_path_queryset(
                        path_segments
                    )
                    outer_ref_field = (
                        anchor_resource_id_annotation or "resourceinstanceid"
                    )
                    rhs_scalar_value = rhs_rows.filter(
                        resourceinstanceid=OuterRef(outer_ref_field)
                    ).values("value")[:1]
                    normalized.append(Subquery(rhs_scalar_value))
                    continue
                if "value" in operand_item:
                    normalized.append(operand_item["value"])
                    continue
            normalized.append(operand_item)
        return normalized
