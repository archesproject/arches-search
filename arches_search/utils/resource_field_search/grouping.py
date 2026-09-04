"""
Resolution of resource-field group-by specs for search.aggregation.

Grouping is restricted to fields whose cardinality is naturally bounded
(foreign keys and booleans). Grouping by a timestamp or a primary key would
produce roughly one bucket per row, which is never a useful aggregation and is
an easy way to make the database do a lot of pointless work.
"""

from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches_search.utils.advanced_search.constants import (
    SUBJECT_TYPE_RESOURCE_FIELD,
)
from arches_search.utils.resource_field_search.field_registry import (
    ResourceInstanceFieldRegistry,
    get_resource_instance_fields,
)

# The same token a clause subject and an additional_data entry use.
GROUP_BY_TYPE_RESOURCE_FIELD = SUBJECT_TYPE_RESOURCE_FIELD

# TileModel's forward relation to the row a resource-field lives on, used when
# aggregating at tile granularity.
TILE_TO_RESOURCE_PREFIX = "resourceinstance__"


def is_resource_field_spec(spec: Dict[str, Any]) -> bool:
    """True for a group_by or metric spec that targets a resource field."""
    return spec.get("type") == GROUP_BY_TYPE_RESOURCE_FIELD


def _resolve_descriptor(spec: Dict[str, Any], registry) -> Optional[Any]:
    field_name = spec.get("field")
    descriptor = registry.get(field_name) if isinstance(field_name, str) else None
    if descriptor is None:
        raise ValidationError(
            _("Unsupported resource field: %(field)s.") % {"field": field_name}
        )
    return descriptor


def resolve_group_by_path(
    group_spec: Dict[str, Any],
    aggregate_by_tile: bool = False,
    registry: Optional[ResourceInstanceFieldRegistry] = None,
) -> str:
    """
    The ORM path to group by, resolved through the registry so a group-by can
    only name a field the registry actually exposes.

    Pass `registry` when resolving several specs: building it costs a query and
    an import per facet row, and the whole point of one registry is that the
    consumers cannot disagree about what exists.
    """
    registry = registry or get_resource_instance_fields()
    descriptor = _resolve_descriptor(group_spec, registry)

    if not descriptor.is_groupable:
        raise ValidationError(
            _(
                "Resource field %(field)s cannot be grouped by; only bounded-"
                "cardinality fields are groupable."
            )
            % {"field": descriptor.name}
        )

    if aggregate_by_tile:
        return f"{TILE_TO_RESOURCE_PREFIX}{descriptor.orm_path}"
    return descriptor.orm_path


def resolve_metric_path(
    metric_spec: Dict[str, Any],
    aggregate_by_tile: bool = False,
    registry: Optional[ResourceInstanceFieldRegistry] = None,
) -> str:
    """
    The ORM path for a metric over a resource field (e.g. counting rows per
    group). Unlike group-by, cardinality is irrelevant here -- the field is
    being aggregated, not bucketed -- so only registry membership is required.
    """
    registry = registry or get_resource_instance_fields()
    descriptor = _resolve_descriptor(metric_spec, registry)

    if aggregate_by_tile:
        return f"{TILE_TO_RESOURCE_PREFIX}{descriptor.orm_path}"
    return descriptor.orm_path
