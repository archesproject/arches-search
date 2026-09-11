from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search.advanced_search import (
    SearchCompiler,
    SearchPayload,
)


class ResourceTypeCountsAPI(APIBase):
    def get(self, request):
        search_payload = SearchPayload(
            graph_ids=None, node_agnostic_filters=None, advanced_search_query=None
        )
        search_result = SearchCompiler(search_payload, request.user).compile()

        return JSONResponse(
            {
                "resourceTypes": [
                    {
                        "graphId": entry["graph_id"],
                        "count": entry["count"],
                    }
                    for entry in search_result.resource_type_counts
                ],
            }
        )
