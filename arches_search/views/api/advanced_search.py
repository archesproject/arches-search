from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search import search_resource_ids_from_payload


class AdvancedSearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        resource_ids = search_resource_ids_from_payload(body)

        return JSONResponse({"resource_ids": list(resource_ids)})
