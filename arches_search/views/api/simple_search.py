from django.core.paginator import Paginator

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.search_aggregation import build_aggregations
from arches_search.utils.search_queryset import (
    build_resource_type_counts,
    build_search_queryset,
)
from arches_search.utils.search_sort import SortResolver


class SimpleSearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        results_queryset = build_search_queryset(body)

        results_queryset = SortResolver(body.get("sort")).apply(results_queryset)

        page_number = body.get("page", 1)
        page_size = body.get("page_size", 20)

        paginator = Paginator(results_queryset, page_size)
        results_page = paginator.page(page_number)

        raw_aggregations = body.get("aggregations")

        aggregations = {}
        if raw_aggregations:
            aggregations = build_aggregations(results_queryset, raw_aggregations)

        resource_type_counts, all_resource_count = build_resource_type_counts(body)

        return JSONResponse(
            {
                "resources": list(results_page.object_list),
                "pagination": {
                    "page": results_page.number,
                    "page_size": page_size,
                    "total_results": paginator.count,
                    "num_pages": paginator.num_pages,
                    "has_next": results_page.has_next(),
                    "has_previous": results_page.has_previous(),
                },
                "aggregations": aggregations,
                "resource_type_counts": resource_type_counts,
                "all_resource_count": all_resource_count,
            }
        )
