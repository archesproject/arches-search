from arches.app.models.models import ResourceInstance
from arches.app.utils.permission_backend import (
    user_can_edit_resource,
    user_can_read_resource,
)
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase


class ResourceDescriptorsAPI(APIBase):
    """Return descriptor and graph_id data for a batch of resource instance IDs.

    GET /arches_search/api/resource-descriptors/?ids=uuid1&ids=uuid2&...

    Pass `include_can_edit=true` to add `can_edit`; it costs extra
    permission queries per resource, so batch callers should omit it.

    Response shape:
    {
        "<resourceinstanceid>": {
            "descriptors": {
                "<language_code>": {
                    "name": "...",
                    "description": "...",
                    "map_popup": "..."
                },
                ...
            },
            "graph_id": "<uuid>",
            "can_edit": false  # only with include_can_edit=true
        },
        ...
    }
    """

    def get(self, request):
        ids = request.GET.getlist("ids")
        include_can_edit = request.GET.get("include_can_edit") == "true"
        instances = (
            ResourceInstance.objects.filter(resourceinstanceid__in=ids)
            .select_related("resource_instance_lifecycle_state")
            .only(
                "resourceinstanceid",
                "descriptors",
                "graph_id",
                "principaluser_id",
                "resource_instance_lifecycle_state",
            )
        )
        response = {}
        for r in instances:
            if not user_can_read_resource(user=request.user, resource=r):
                continue
            data = {"descriptors": r.descriptors or {}, "graph_id": str(r.graph_id)}
            if include_can_edit:
                data["can_edit"] = bool(
                    user_can_edit_resource(request.user, resource=r)
                )
            response[str(r.resourceinstanceid)] = data
        return JSONResponse(response)
