"""
Metadata describing which ResourceInstance system fields a client may filter,
sort, and group by.

Mirrors AllDatatypeFacetsAPI, which does the same job for node datatypes: the
UI fetches this once and renders inputs from it, rather than hardcoding a list
of fields that would drift from the backend.
"""

from arches.app.models.models import GraphModel, ResourceInstanceLifecycleState
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.resource_field_search.field_registry import (
    get_resource_field_registry,
)

# Related models whose rows are safe and bounded to enumerate as pick-list
# choices. Enumerating an arbitrary related table could be unbounded (and could
# expose rows a caller has no business listing), so this is opt-in rather than
# applied to every foreign key.
CHOICE_ENUMERABLE_MODELS = {ResourceInstanceLifecycleState.__name__}


def _serialize_descriptor(descriptor):
    return {
        "field": descriptor.name,
        "label": descriptor.label,
        "kind": descriptor.kind,
        "operators": list(descriptor.operators),
        "is_groupable": descriptor.is_groupable,
        "is_user_relation": descriptor.is_user_relation,
    }


def _lifecycle_state_choices(graph_ids):
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


class ResourceFieldMetadataAPI(APIBase):
    def get(self, request):
        graph_ids = request.GET.getlist("graph_ids")
        registry = get_resource_field_registry()

        fields = []
        for descriptor in registry.all():
            serialized = _serialize_descriptor(descriptor)
            related_model = descriptor.metadata.get("related_model")
            if related_model in CHOICE_ENUMERABLE_MODELS:
                serialized["choices"] = _lifecycle_state_choices(graph_ids)
            fields.append(serialized)

        return JSONResponse({"fields": fields})
