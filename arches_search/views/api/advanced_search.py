from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search import resources_queryset_from_payload
from arches_search.utils.search_aggregation import (
    apply_json_aggregations,
    build_joined_queryset_for_aggregations,
)


class AdvancedSearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        aggregations = {}
        payload_query = body.get("query", body)
        raw_aggregations = payload_query.get("aggregations")

        base_queryset = resources_queryset_from_payload(body)

        if raw_aggregations:
            # dynamically join the necessary arches_search_* tables
            joined_queryset = build_joined_queryset_for_aggregations(
                base_queryset, raw_aggregations
            )

            aggregations = apply_json_aggregations(raw_aggregations, joined_queryset)

        return JSONResponse(
            {
                "resources": list(base_queryset),
                "aggregations": aggregations,
            }
        )
