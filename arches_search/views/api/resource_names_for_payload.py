from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.resource_names_for_payload import (
    build_resource_names_for_payload,
)


class ResourceNamesForPayloadAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        resource_names = build_resource_names_for_payload(body)

        return JSONResponse(resource_names)
