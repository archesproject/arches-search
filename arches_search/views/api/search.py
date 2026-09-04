from django.core.exceptions import ValidationError

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.search import SearchRequest, execute_search


class SearchAPI(APIBase):
    """
    HTTP in front of arches_search.utils.search.

    The search itself is callable in-process, so this reads the body, hands it
    over, and serializes what comes back -- nothing about how a search runs
    lives here.
    """

    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        try:
            search_response = execute_search(
                SearchRequest.from_body(body), request.user
            )
        except ValidationError as error:
            return JSONResponse({"error": str(error)}, status=400)

        return JSONResponse(search_response.serialize())
