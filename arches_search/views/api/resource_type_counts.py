from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.simple_search.search_queryset import (
    SimpleSearchQuerysetBuilder,
    build_resource_type_counts,
)


class ResourceTypeCountsAPI(APIBase):
    def get(self, request):
        queryset = SimpleSearchQuerysetBuilder({}, request.user).type_agnostic_queryset
        resource_type_counts, _ = build_resource_type_counts([], queryset)

        return JSONResponse(
            {
                "resourceTypes": [
                    {
                        "graphId": entry["graph_id"],
                        "count": entry["count"],
                    }
                    for entry in resource_type_counts
                ],
            }
        )
