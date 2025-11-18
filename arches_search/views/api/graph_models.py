from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches.app.models import models as arches_models


class GraphModelsAPI(APIBase):
    def get(self, request):
        graphs = arches_models.GraphModel.objects.filter(isresource=True).order_by(
            "name"
        )
        return JSONResponse(list(graphs))
