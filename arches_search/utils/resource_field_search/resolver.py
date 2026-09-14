"""
Compiles one resource field clause into a Django Q object.

Fields and operators are resolved against ResourceInstanceFieldRegistry, so a
client-supplied string is never used to build an ORM lookup path directly, and
the lookup itself comes from the facet row's orm_template -- an operator is
added by seeding a row rather than by adding a branch here.
"""

from typing import Any, List, Optional

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import get_language, gettext as _

from arches_search.utils.resource_field_search.field_registry import (
    CURRENT_USER_FORMAT,
    ResourceInstanceField,
)

# An empty Q() cannot stand in for MATCH_EVERYTHING: Django absorbs it when
# combining, so inside an OR it would mean the opposite.
MATCH_NOTHING = Q(pk__in=[])
MATCH_EVERYTHING = ~Q(pk__in=[])

# The param_formats vocabulary a facet row uses to describe its operands.
LIST_FORMAT = "{values}"


def current_user_id(user) -> Optional[int]:
    """
    The requesting user's id, or None when there isn't one.

    AnonymousUser.id is None, and Q(principaluser_id=None) compiles to
    "principaluser_id IS NULL" -- which would match every resource that has no
    recorded creator. Callers must treat None as "no identity", never as a value
    to filter on.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    return user.id


def _expected_operand_count(facet) -> int:
    """
    How many operands a facet's template consumes.

    param_formats names the template's parameters, so its length is the count --
    except for "current_user", which is filled from the request, and arity 0
    operators, which compare against presence rather than a value.
    """
    param_formats = list(facet.param_formats or [])
    if CURRENT_USER_FORMAT in param_formats or facet.arity == 0:
        return 0
    return max(len(param_formats), 1)


def _operand_shape_error(param_format: str, value: Any) -> Optional[str]:
    """
    Why `value` cannot fill `param_format`, or None when it can.

    The vocabulary is the facet row's own, so a newly seeded operator is
    validated by the row that defines it rather than by a branch added here:
    "{values}" takes a list, a format carrying "%" is a substring match and so
    needs text, any other "{...}" placeholder takes one scalar, and a bare name
    is a key of a composite value (a range's "from"/"to") that must be present.
    """
    if param_format == LIST_FORMAT:
        if not isinstance(value, list) or not value:
            return _("takes a non-empty list")
        return None

    if "%" in param_format:
        if not isinstance(value, str) or not value:
            return _("takes a non-empty string")
        return None

    if "{" in param_format:
        if isinstance(value, (list, dict)):
            return _("takes a single value")
        return None

    if value is None:
        return _("requires a %(param)s value") % {"param": param_format}
    return None


def validate_operands(
    facet, operand_values: List[Any], field_name: str, operator_token: str
) -> None:
    """
    Raise unless the operands match what the facet's param_formats describe.
    """
    required_count = _expected_operand_count(facet)
    if len(operand_values) != required_count:
        raise ValidationError(
            _(
                "Operator %(operator)s on resource field %(field)s takes "
                "%(expected)s operand(s), got %(actual)s."
            ),
            params={
                "operator": operator_token,
                "field": field_name,
                "expected": required_count,
                "actual": len(operand_values),
            },
        )

    param_formats = list(facet.param_formats or [])
    for param_format, value in zip(param_formats, operand_values):
        shape_error = _operand_shape_error(param_format, value)
        if shape_error is not None:
            raise ValidationError(
                _("Operator %(operator)s on resource field %(field)s %(reason)s."),
                params={
                    "operator": operator_token,
                    "field": field_name,
                    "reason": shape_error,
                },
            )


def _operands_for(facet, operand_values: List[Any], user_id) -> Optional[List[Any]]:
    if "current_user" in list(facet.param_formats or []):
        return None if user_id is None else [user_id]
    if facet.arity == 0:
        return []
    return list(operand_values)


def build_resource_field_predicate(
    descriptor: ResourceInstanceField,
    facet,
    operand_values: List[Any],
    user_id: Optional[int],
) -> Optional[Q]:
    """
    The Q for one clause, or None when the clause constrains nothing.
    """
    operands = _operands_for(facet, operand_values, user_id)

    if operands is None:
        # No identity to compare against: "is me" must match nothing rather
        # than every creator-less resource.
        return None if facet.is_orm_template_negated else MATCH_NOTHING

    lookup = facet.orm_template.format(
        col=descriptor.orm_path, language=get_language() or "en"
    )

    if facet.arity == 0:
        value_for_lookup = True
    elif facet.arity == 1:
        value_for_lookup = operands[0]
    else:
        value_for_lookup = tuple(operands)

    predicate = Q(**{lookup: value_for_lookup})

    if not facet.is_orm_template_negated:
        return predicate

    # Django compiles ~Q(col=x) to NOT (col = x AND col IS NOT NULL), so rows
    # with no value are already kept.
    return ~predicate
