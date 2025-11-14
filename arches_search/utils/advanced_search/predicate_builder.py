from typing import Any, List, Optional, Tuple
from django.db.models import Subquery, OuterRef, Q
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
    ) -> Tuple[Q | dict, bool]:
        normalized_operands = self._normalize_operands(
            operands=operands,
            anchor_resource_id_annotation=anchor_resource_id_annotation,
        )

        facet = self.facet_registry.get_facet(datatype_name, operator_token)
        lookup_key = facet.orm_template.replace("{col}", "value")
        is_template_negated = bool(facet.is_orm_template_negated)

        if facet.arity == 0:
            value_for_lookup = True
        elif facet.arity == 1:
            value_for_lookup = normalized_operands[0]
        else:
            value_for_lookup = normalized_operands

        predicate_kwargs = {lookup_key: value_for_lookup}

        if is_template_negated:
            return ~Q(**predicate_kwargs), True

        return predicate_kwargs, False

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
                _("Unsupported operand type: {type}").format(type=operand_type)
            )

        return normalized_values
