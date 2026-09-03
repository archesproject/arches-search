"""
Turns validated resource_field_filters entries into a Django Q object.

Every entry is resolved against ResourceInstanceFieldRegistry, so only fields the
registry discovered are reachable; a client-supplied string is never used to
build an ORM lookup path directly.
"""

from typing import Any, Dict, List, Optional

from django.db.models import Q
from django.utils.translation import get_language

from arches_search.utils.resource_field_search.field_registry import (
    ResourceInstanceField,
    get_resource_instance_fields,
)

# A predicate that is always false, without hitting the database.
MATCH_NOTHING = Q(pk__in=[])


def _current_user_id(user) -> Optional[int]:
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


def _operands_for(facet, value, current_user_id) -> Optional[List[Any]]:
    """
    The operand list a facet's template expects, or None to skip the entry.

    param_formats names how the payload value maps onto the template: "from"/"to"
    unpacks a range object, and "current_user" means the value comes from the
    request rather than the client.
    """
    param_formats = list(facet.param_formats or [])

    if "current_user" in param_formats:
        return None if current_user_id is None else [current_user_id]

    if facet.arity == 0:
        return []

    if param_formats and isinstance(value, dict):
        return [value[key] for key in param_formats]

    return [value]


def _build_entry_predicate(
    descriptor: ResourceInstanceField,
    facet,
    value: Any,
    current_user_id: Optional[int],
) -> Optional[Q]:
    """
    Compile one entry the same way PredicateBuilder compiles a tile facet.

    The lookup comes from the facet row's orm_template, so an operator is added
    by seeding a row rather than by adding a branch here.
    """
    operands = _operands_for(facet, value, current_user_id)

    if operands is None:
        # A current-user operator with no identity to compare against. An
        # affirmative one matches nothing rather than matching every
        # creator-less resource; a negative one constrains nothing.
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

    if "current_user" in (facet.param_formats or []) and descriptor.is_nullable:
        # Under SQL's three-valued logic a bare negation drops NULL rows, which
        # would hide creator-less resources from "is not me".
        return ~predicate | Q(**{f"{descriptor.orm_path}__isnull": True})
    return ~predicate


def build_resource_field_filter(
    user,
    filter_entries: Optional[List[Dict[str, Any]]],
    registry=None,
) -> Optional[Q]:
    """
    Combine resource_field_filters entries into a single AND-ed Q, or None when
    there is nothing to apply.

    Entries are assumed to have passed validate_resource_field_filters().
    """
    if not filter_entries:
        return None

    registry = registry or get_resource_instance_fields()
    current_user_id = _current_user_id(user)

    combined: Optional[Q] = None
    for filter_entry in filter_entries:
        descriptor = registry.get(filter_entry["field"])
        if descriptor is None:
            # Validation rejects unknown fields; treat any that reach here as
            # matching nothing rather than silently widening the result set.
            return MATCH_NOTHING

        facet = descriptor.facet_for(filter_entry["operator"])
        if facet is None:
            raise ValueError(
                f"Unsupported resource field operator: {filter_entry['operator']}"
            )

        predicate = _build_entry_predicate(
            descriptor=descriptor,
            facet=facet,
            value=filter_entry.get("value"),
            current_user_id=current_user_id,
        )
        if predicate is None:
            continue
        combined = predicate if combined is None else (combined & predicate)

    return combined
