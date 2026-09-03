"""
Shape validation for the resource_field_filters payload key.

Mirrors validate_node_agnostic_filters: raises django ValidationError, which the
view turns into a 400. Fields and operators are checked against
ResourceInstanceFieldRegistry, so an unknown or unreachable path (principaluser__password,
say) is rejected before any queryset is built.

What value an operator accepts comes from its facet's param_formats, using the
same vocabulary as the datatype facets, so seeding a new operator needs no change
here.
"""

from typing import Any, List

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches_search.utils.resource_field_search.field_registry import (
    get_resource_instance_fields,
)

LIST_FORMAT = "{values}"
SCALAR_FORMAT = "{value}"
CURRENT_USER_FORMAT = "current_user"


def validate_resource_field_filters(resource_field_filters: Any, registry=None) -> None:
    if resource_field_filters is None:
        return
    if not isinstance(resource_field_filters, list):
        raise ValidationError(_("resource_field_filters must be a list."))

    registry = registry or get_resource_instance_fields()

    for index, filter_entry in enumerate(resource_field_filters):
        _validate_entry(filter_entry, index, registry)


def _error(index: int, message: str, **context: Any) -> ValidationError:
    return ValidationError(message % {"i": index, **context})


def _validate_entry(filter_entry: Any, index: int, registry) -> None:
    if not isinstance(filter_entry, dict):
        raise _error(index, _("resource_field_filters[%(i)s] must be an object."))

    field_name = filter_entry.get("field")
    descriptor = registry.get(field_name) if isinstance(field_name, str) else None
    if descriptor is None:
        raise _error(
            index,
            _("resource_field_filters[%(i)s] has unsupported field %(field)s."),
            field=field_name,
        )

    operator = filter_entry.get("operator")
    if not isinstance(operator, str) or not descriptor.supports(operator):
        raise _error(
            index,
            _(
                "resource_field_filters[%(i)s] operator %(operator)s is not "
                "supported for field %(field)s."
            ),
            operator=operator,
            field=field_name,
        )

    facet = descriptor.facet_for(operator)
    param_formats = list(facet.param_formats or [])
    has_value = filter_entry.get("value") is not None

    if _takes_no_value(param_formats):
        # Fail loudly rather than ignoring the value: an operator whose operand
        # comes from the request carrying a client-supplied one is an attempt to
        # filter as someone else, and should not look like it succeeded.
        if has_value:
            raise _error(
                index,
                _(
                    "resource_field_filters[%(i)s] operator %(operator)s does not "
                    "accept a value."
                ),
                operator=operator,
            )
        return

    if not has_value:
        raise _error(
            index,
            _(
                "resource_field_filters[%(i)s] operator %(operator)s requires a "
                "value."
            ),
            operator=operator,
        )

    _validate_value(filter_entry["value"], param_formats, index, operator)


def _takes_no_value(param_formats: List[str]) -> bool:
    """A facet whose operand is implied, or supplied by the request."""
    return not param_formats or param_formats == [CURRENT_USER_FORMAT]


def _named_keys(param_formats: List[str]) -> List[str]:
    """Formats that name a key of an object rather than a placeholder."""
    return [
        param_format
        for param_format in param_formats
        if "{" not in param_format and param_format != CURRENT_USER_FORMAT
    ]


def _validate_value(
    value: Any, param_formats: List[str], index: int, operator: str
) -> None:
    if LIST_FORMAT in param_formats:
        if not isinstance(value, list) or not value:
            raise _error(
                index,
                _(
                    "resource_field_filters[%(i)s] %(operator)s value must be a "
                    "non-empty list."
                ),
                operator=operator,
            )
        return

    named_keys = _named_keys(param_formats)
    if named_keys:
        if not isinstance(value, dict) or any(
            value.get(key) is None for key in named_keys
        ):
            raise _error(
                index,
                _(
                    "resource_field_filters[%(i)s] %(operator)s value must be an "
                    "object with %(keys)s."
                ),
                operator=operator,
                keys=", ".join(named_keys),
            )
        return

    if any("%" in param_format for param_format in param_formats):
        if not isinstance(value, str) or not value:
            raise _error(
                index,
                _(
                    "resource_field_filters[%(i)s] %(operator)s value must be a "
                    "non-empty string."
                ),
                operator=operator,
            )
        return

    if SCALAR_FORMAT in param_formats and isinstance(value, (list, dict)):
        raise _error(
            index,
            _(
                "resource_field_filters[%(i)s] %(operator)s value must be a single "
                "value."
            ),
            operator=operator,
        )
