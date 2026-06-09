from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.query_narrator import narrate_query


class NarrateQueryAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        narration = narrate_query(body)
        return JSONResponse({"narration": narration})
