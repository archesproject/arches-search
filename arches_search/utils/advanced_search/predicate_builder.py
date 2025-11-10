from typing import Any, List, Optional, Tuple
from django.db.models import Subquery, OuterRef
from django.utils.translation import gettext as _

TYPE_LITERAL = "LITERAL"
TYPE_PATH = "PATH"


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
    ) -> Tuple[Any, bool]:
        normalized_operands = self._normalize_operands(
            operands=operands,
            anchor_resource_id_annotation=anchor_resource_id_annotation,
        )
        predicate_expression, is_template_negated = self.facet_registry.predicate(
            datatype_name, operator_token, "value", normalized_operands
        )

        return predicate_expression, is_template_negated

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
                _("Unsupported operand type: %(type)s") % {"type": operand_type}
            )

        return normalized_values
