"""
Shape validation for the resource_field_filters payload key.

Mirrors validate_node_agnostic_filters: raises django ValidationError, which the
view turns into a 400. Field names and operators are checked against
ResourceFieldRegistry, so an unknown or deliberately-unreachable path (for
example principaluser__password) is rejected before any queryset is built.
"""

from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches_search.utils.resource_field_search.field_registry import (
    OPERATOR_AFTER,
    OPERATOR_BEFORE,
    OPERATOR_CONTAINS,
    OPERATOR_EQUALS,
    OPERATOR_IN,
    OPERATOR_RANGE,
    OPERATOR_STARTS_WITH,
    ZERO_ARITY_OPERATORS,
    get_resource_field_registry,
)


def validate_resource_field_filters(resource_field_filters: Any, registry=None) -> None:
    if resource_field_filters is None:
        return
    if not isinstance(resource_field_filters, list):
        raise ValidationError(_("resource_field_filters must be a list."))

    registry = registry or get_resource_field_registry()

    for index, filter_entry in enumerate(resource_field_filters):
        if not isinstance(filter_entry, dict):
            raise ValidationError(
                _("resource_field_filters[%(i)s] must be an object.") % {"i": index}
            )

        field_name = filter_entry.get("field")
        descriptor = registry.get(field_name) if isinstance(field_name, str) else None
        if descriptor is None:
            raise ValidationError(
                _("resource_field_filters[%(i)s] has unsupported field %(field)s.")
                % {"i": index, "field": field_name}
            )

        operator = filter_entry.get("operator")
        if not isinstance(operator, str) or not descriptor.supports(operator):
            raise ValidationError(
                _(
                    "resource_field_filters[%(i)s] operator %(operator)s is not "
                    "supported for field %(field)s."
                )
                % {"i": index, "operator": operator, "field": field_name}
            )

        has_value = "value" in filter_entry and filter_entry["value"] is not None

        if operator in ZERO_ARITY_OPERATORS:
            # Fail loudly rather than ignoring the value: an IS_CURRENT_USER
            # clause carrying a user id is an attempt to filter as someone else,
            # and should not look like it succeeded.
            if has_value:
                raise ValidationError(
                    _(
                        "resource_field_filters[%(i)s] operator %(operator)s does "
                        "not accept a value."
                    )
                    % {"i": index, "operator": operator}
                )
            continue

        if not has_value:
            raise ValidationError(
                _(
                    "resource_field_filters[%(i)s] operator %(operator)s requires a value."
                )
                % {"i": index, "operator": operator}
            )

        value = filter_entry["value"]

        if operator == OPERATOR_IN:
            if not isinstance(value, list) or not value:
                raise ValidationError(
                    _(
                        "resource_field_filters[%(i)s] IN value must be a non-empty list."
                    )
                    % {"i": index}
                )
        elif operator == OPERATOR_RANGE:
            if (
                not isinstance(value, dict)
                or value.get("from") is None
                or value.get("to") is None
            ):
                raise ValidationError(
                    _(
                        "resource_field_filters[%(i)s] RANGE value must be an object "
                        'with "from" and "to".'
                    )
                    % {"i": index}
                )
        elif operator in (OPERATOR_CONTAINS, OPERATOR_STARTS_WITH):
            if not isinstance(value, str) or not value:
                raise ValidationError(
                    _(
                        "resource_field_filters[%(i)s] %(operator)s value must be a "
                        "non-empty string."
                    )
                    % {"i": index, "operator": operator}
                )
        elif operator in (OPERATOR_EQUALS, OPERATOR_BEFORE, OPERATOR_AFTER):
            if isinstance(value, (list, dict)):
                raise ValidationError(
                    _(
                        "resource_field_filters[%(i)s] %(operator)s value must be a "
                        "single value."
                    )
                    % {"i": index, "operator": operator}
                )
