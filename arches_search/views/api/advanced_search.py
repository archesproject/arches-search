from django.core.paginator import Paginator

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

        results_queryset = AdvancedSearchQueryCompiler(body).compile()

        page_number = body.get("page", 1)
        page_size = body.get("page_size", 20)

        paginator = Paginator(results_queryset, page_size)
        page = paginator.page(page_number)

        raw_aggregations = body.get("aggregations")

        aggregations = {}
        if raw_aggregations:
            aggregations = build_aggregations(results_queryset, raw_aggregations)

        return JSONResponse(
            {
                "resources": list(page.object_list),
                "pagination": {
                    "page": page.number,
                    "page_size": page_size,
                    "total_results": paginator.count,
                    "num_pages": paginator.num_pages,
                    "has_next": page.has_next(),
                    "has_previous": page.has_previous(),
                },
                "aggregations": aggregations,
            }
        )
