from django.core.exceptions import ValidationError
from django.core.paginator import Paginator

from arches.app.utils.betterJSONSerializer import JSONDeserializer, JSONSerializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search.advanced_search import (
    SearchCompiler,
    SearchPayload,
    validate_node_agnostic_filters,
)
from arches_search.utils.search_aggregation import build_aggregations
from arches_search.utils.search_sort import SortResolver


def build_search_payload(body):
    return SearchPayload(
        graph_ids=body.get("graph_ids") or None,
        node_agnostic_filters=body.get("node_agnostic_filters"),
        advanced_search_query=body.get("advanced_search_query"),
    )


class SearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        try:
            validate_node_agnostic_filters(body.get("node_agnostic_filters"))
        except ValidationError as error:
            return JSONResponse({"error": str(error)}, status=400)

        search_payload = build_search_payload(body)
        search_result = SearchCompiler(search_payload, request.user).compile()

        results_queryset = SortResolver(body.get("sort")).apply(search_result.results)
        page_number = body.get("page", 1)
        page_size = body.get("page_size", 20)
        paginator = Paginator(results_queryset, page_size)
        # Skips Paginator's own COUNT(*) query — the total is already known.
        paginator.count = search_result.scoped_count
        results_page = paginator.page(page_number)

        raw_aggregations = body.get("aggregations")
        aggregations = (
            build_aggregations(results_queryset, raw_aggregations)
            if raw_aggregations
            else {}
        )

        serialized_resources = [
            JSONSerializer().serializeToPython(resource)
            for resource in results_page.object_list
        ]

        return JSONResponse(
            {
                "resources": serialized_resources,
                "pagination": {
                    "page": results_page.number,
                    "page_size": page_size,
                    "total_results": paginator.count,
                    "num_pages": paginator.num_pages,
                    "has_next": results_page.has_next(),
                    "has_previous": results_page.has_previous(),
                },
                "aggregations": aggregations,
                "resource_type_counts": search_result.resource_type_counts,
                "all_resource_count": search_result.all_resource_count,
            }
        )
