from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches.app.models import models as arches_models


class GraphNodesAPI(APIBase):
    def get(self, request, graph_id):
        nodes = arches_models.Node.objects.filter(graph_id=graph_id).order_by("name")
        return JSONResponse(list(nodes))
