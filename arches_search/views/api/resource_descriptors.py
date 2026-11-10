from arches.app.models.models import GeoJSONGeometry, Node, ResourceInstance
from arches.app.utils.permission_backend import user_can_read_resource
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.readable_nodes import ReadableNodes


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
            "graph_id": "<uuid>",
            "has_geometry": true,
            "lifecycle_state_id": "<uuid>" | null
        },
        ...
    }
    """

    def get(self, request):
        ids = request.GET.getlist("ids")
        instances = ResourceInstance.objects.filter(resourceinstanceid__in=ids).only(
            "resourceinstanceid",
            "descriptors",
            "graph_id",
            "principaluser_id",
            "resource_instance_lifecycle_state_id",
        )
        readable_geometry_nodes = ReadableNodes(request.user).filter_nodes(
            Node.objects.filter(datatype="geojson-feature-collection")
        )
        ids_with_readable_geometry = {
            str(resource_id)
            for resource_id in GeoJSONGeometry.objects.filter(
                resourceinstance_id__in=ids,
                node_id__in=readable_geometry_nodes.values("nodeid"),
            )
            .values_list("resourceinstance_id", flat=True)
            .distinct()
        }
        response = {}
        for r in instances:
            if not user_can_read_resource(user=request.user, resource=r):
                continue
            lifecycle_state_id = None
            if r.resource_instance_lifecycle_state_id:
                lifecycle_state_id = str(r.resource_instance_lifecycle_state_id)
            response[str(r.resourceinstanceid)] = {
                "descriptors": r.descriptors or {},
                "graph_id": str(r.graph_id),
                "has_geometry": str(r.resourceinstanceid) in ids_with_readable_geometry,
                "lifecycle_state_id": lifecycle_state_id,
            }
        return JSONResponse(response)
