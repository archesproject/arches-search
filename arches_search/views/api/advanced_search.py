from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase


class AdvancedSearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        import pdb

        pdb.set_trace()

        return JSONResponse()
