from arches.app.models.models import ResourceInstance
from arches.app.utils.permission_backend import user_can_read_resource
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase


class ResourceDescriptorsAPI(APIBase):
    """Return descriptor and graph_id data for a batch of resource instance IDs.

    GET /arches_search/api/resource-descriptors/?ids=uuid1&ids=uuid2&...

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
            "graph_id": "<uuid>"
        },
        ...
    }
    """

    def get(self, request):
        ids = request.GET.getlist("ids")
        instances = ResourceInstance.objects.filter(resourceinstanceid__in=ids).only(
            "resourceinstanceid", "descriptors", "graph_id", "principaluser_id"
        )
        response = {}
        for r in instances:
            if not user_can_read_resource(user=request.user, resource=r):
                continue
            response[str(r.resourceinstanceid)] = {
                "descriptors": r.descriptors or {},
                "graph_id": str(r.graph_id),
            }
        return JSONResponse(response)
