from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.search_aggregation import build_aggregations


class AdvancedSearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        raw_aggregations = body.get("aggregations")

        results = AdvancedSearchQueryCompiler(body).compile()

        if raw_aggregations:
            # dynamically join the necessary arches_search_* tables
            aggregations = build_aggregations(results, raw_aggregations)

        return JSONResponse(
            {
                "resources": list(results),
                "aggregations": aggregations,
            }
        )
