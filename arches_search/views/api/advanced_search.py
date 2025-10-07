from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search import resources_queryset_from_payload
from arches_search.utils.search_aggregation import apply_json_aggregations


class AdvancedSearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        results = resources_queryset_from_payload(body)

        aggregations = {}
        payload_query = body.get("query", body)
        raw_aggregations = payload_query.get("aggregations")

        if raw_aggregations:
            aggregations = apply_json_aggregations(raw_aggregations, results)

        return JSONResponse(
            {
                "resources": list(results),
                "aggregations": aggregations,
            }
        )
