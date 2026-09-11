from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext as _

from arches_search.utils.resource_field_search.field_registry import (
    get_resource_instance_fields,
)
from arches_search.utils.resource_field_search.resolver import (
    MATCH_EVERYTHING,
    build_resource_field_predicate,
    current_user_id,
    validate_operands,
)


class ResourceFieldClauseEvaluator:
    """
    Evaluates clauses whose subject is a column on the resource row itself.

    A node subject's value lives in a tile and is reached with a correlated
    Exists over the search tables. A resource field is already a column on the
    row being filtered, so it needs none of that machinery and compiles to a
    plain Q that composes with the rest of the group's predicate.
    """

    def __init__(self, user=None, registry=None) -> None:
        self.user = user
        self._registry = registry

    @property
    def registry(self):
        if self._registry is None:
            self._registry = get_resource_instance_fields()
        return self._registry

    def build_predicate(self, clause_payload: Dict[str, Any]) -> Q:
        field_name = clause_payload["subject"]["field"]
        operator_token = clause_payload["operator"]

        descriptor = self.registry.get(field_name)
        if descriptor is None:
            raise ValidationError(
                _("Unknown resource field: %(field)s."),
                params={"field": field_name},
            )

        facet = descriptor.facet_for(operator_token)
        if facet is None:
            raise ValidationError(
                _(
                    "Operator %(operator)s is not available on resource field "
                    "%(field)s. Available: %(available)s."
                ),
                params={
                    "operator": operator_token,
                    "field": field_name,
                    "available": ", ".join(descriptor.operators),
                },
            )

        operand_values = [operand["value"] for operand in clause_payload["operands"]]
        validate_operands(facet, operand_values, field_name, operator_token)

        predicate = build_resource_field_predicate(
            descriptor=descriptor,
            facet=facet,
            operand_values=operand_values,
            user_id=current_user_id(self.user),
        )

        # None means the clause constrains nothing.
        return MATCH_EVERYTHING if predicate is None else predicate
