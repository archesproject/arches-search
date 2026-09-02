"""
Turns validated resource_field_filters entries into a Django Q object.

Every entry is resolved against ResourceFieldRegistry, so only fields the
registry discovered are reachable; a client-supplied string is never used to
build an ORM lookup path directly.
"""

from typing import Any, Dict, List, Optional

from django.db.models import Q

from arches_search.utils.resource_field_search.field_registry import (
    OPERATOR_AFTER,
    OPERATOR_BEFORE,
    OPERATOR_CONTAINS,
    OPERATOR_EQUALS,
    OPERATOR_HAS_ANY_VALUE,
    OPERATOR_HAS_NO_VALUE,
    OPERATOR_IN,
    OPERATOR_IS_CURRENT_USER,
    OPERATOR_IS_FALSE,
    OPERATOR_IS_NOT_CURRENT_USER,
    OPERATOR_IS_TRUE,
    OPERATOR_RANGE,
    OPERATOR_STARTS_WITH,
    ResourceFieldDescriptor,
    get_resource_field_registry,
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


def _build_entry_predicate(
    descriptor: ResourceFieldDescriptor,
    operator: str,
    value: Any,
    current_user_id: Optional[int],
) -> Optional[Q]:
    path = descriptor.orm_path

    if operator == OPERATOR_EQUALS:
        return Q(**{path: value})
    if operator == OPERATOR_IN:
        return Q(**{f"{path}__in": value})
    if operator == OPERATOR_CONTAINS:
        return Q(**{f"{path}__icontains": value})
    if operator == OPERATOR_STARTS_WITH:
        return Q(**{f"{path}__istartswith": value})
    if operator == OPERATOR_RANGE:
        return Q(**{f"{path}__range": (value["from"], value["to"])})
    if operator == OPERATOR_BEFORE:
        return Q(**{f"{path}__lt": value})
    if operator == OPERATOR_AFTER:
        return Q(**{f"{path}__gt": value})
    if operator == OPERATOR_IS_TRUE:
        return Q(**{path: True})
    if operator == OPERATOR_IS_FALSE:
        return Q(**{path: False})
    if operator == OPERATOR_HAS_ANY_VALUE:
        return Q(**{f"{path}__isnull": False})
    if operator == OPERATOR_HAS_NO_VALUE:
        return Q(**{f"{path}__isnull": True})

    if operator == OPERATOR_IS_CURRENT_USER:
        # The compared value comes only from the request's authenticated user.
        # Anonymous requests match nothing rather than matching creator-less
        # resources.
        if current_user_id is None:
            return MATCH_NOTHING
        return Q(**{path: current_user_id})

    if operator == OPERATOR_IS_NOT_CURRENT_USER:
        if current_user_id is None:
            # No identity to exclude, so this constrains nothing.
            return None
        # Spelled out rather than relying on ~Q alone: under SQL's three-valued
        # logic a bare negation drops rows where the column is NULL, which would
        # silently hide creator-less resources from "not mine".
        return ~Q(**{path: current_user_id}) | Q(**{f"{path}__isnull": True})

    raise ValueError(f"Unsupported resource field operator: {operator}")


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

    registry = registry or get_resource_field_registry()
    current_user_id = _current_user_id(user)

    combined: Optional[Q] = None
    for filter_entry in filter_entries:
        descriptor = registry.get(filter_entry["field"])
        if descriptor is None:
            # Validation rejects unknown fields; treat any that reach here as
            # matching nothing rather than silently widening the result set.
            return MATCH_NOTHING

        predicate = _build_entry_predicate(
            descriptor=descriptor,
            operator=filter_entry["operator"],
            value=filter_entry.get("value"),
            current_user_id=current_user_id,
        )
        if predicate is None:
            continue
        combined = predicate if combined is None else (combined & predicate)

    return combined
