from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.query_narrator import QueryNarrator


class NarrateQueryAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        narration = QueryNarrator(body).narrate()
        return JSONResponse({"narration": narration})
