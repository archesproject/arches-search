"""
Describes which ResourceInstance system fields a client may filter, sort, and
group by, so the UI can render inputs from the registry rather than hardcoding
a field list that would drift from the backend.
"""

from typing import Any, Dict, Iterable, List

from arches.app.models.models import GraphModel, ResourceInstanceLifecycleState

from arches_search.utils.resource_field_search.field_registry import (
    get_resource_instance_fields,
)


def _serialize_descriptor(descriptor) -> Dict[str, Any]:
    return {
        "field": descriptor.name,
        "label": descriptor.label,
        "kind": descriptor.kind,
        "operators": list(descriptor.operators),
        "is_groupable": descriptor.is_groupable,
        "is_user_relation": descriptor.is_user_relation,
    }


def _lifecycle_state_choices(graph_ids: Iterable[str]) -> List[Dict[str, str]]:
    """
    Lifecycle states, narrowed to the graphs in play when the caller names them.

    Each graph carries its own lifecycle, so an unscoped list would blend the
    vocabularies of unrelated resource models into one dropdown.
    """
    states = ResourceInstanceLifecycleState.objects.all()

    if graph_ids:
        lifecycle_ids = (
            GraphModel.objects.filter(graphid__in=graph_ids)
            .exclude(resource_instance_lifecycle__isnull=True)
            .values_list("resource_instance_lifecycle_id", flat=True)
        )
        states = states.filter(resource_instance_lifecycle_id__in=lifecycle_ids)

    return [
        {"value": str(state.pk), "label": str(state.name)}
        for state in states.order_by("name")
    ]


def resource_field_metadata(graph_ids: Iterable[str]) -> List[Dict[str, Any]]:
    """Every filterable field, with pick-list choices where they are bounded."""
    fields = []

    for descriptor in get_resource_instance_fields().all():
        serialized = _serialize_descriptor(descriptor)
        if descriptor.name == "resource_instance_lifecycle_state":
            serialized["choices"] = _lifecycle_state_choices(graph_ids)
        fields.append(serialized)

    return fields
