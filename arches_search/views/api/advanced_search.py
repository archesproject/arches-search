from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.search_aggregation import apply_json_aggregations


class AdvancedSearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        aggregations = {}

        results = AdvancedSearchQueryCompiler(body).compile()
        raw_aggregations = body.get("aggregations")

        if raw_aggregations:
            aggregations = apply_json_aggregations(raw_aggregations, results)

        return JSONResponse(
            {
                "resources": list(results),
                "aggregations": aggregations,
            }
        )
