from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.search import SearchCompiler, SearchPayload
from arches_search.utils.search.compiler import active_resource_graph_slugs


class ResourceTypeCountsAPI(APIBase):
    def get(self, request):
        search_payload = SearchPayload(
            graph_slugs=active_resource_graph_slugs(),
            term_search=None,
            advanced_search_queries=None,
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
