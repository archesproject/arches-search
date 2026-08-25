from django.core.exceptions import ValidationError
from django.core.paginator import Paginator

from arches.app.utils.betterJSONSerializer import JSONDeserializer, JSONSerializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.extra_columns import (
    attach_extra_columns,
    validate_extra_columns,
)
from arches_search.utils.search_aggregation import build_aggregations
from arches_search.utils.search_queryset import (
    SimpleSearchQuerysetBuilder,
    build_resource_type_counts,
)
from arches_search.utils.search_sort import SortResolver


class SimpleSearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        extra_columns_spec = body.get("extra_columns")
        try:
            validate_extra_columns(extra_columns_spec)
        except ValidationError as error:
            return JSONResponse({"error": str(error)}, status=400)

        querysets = SimpleSearchQuerysetBuilder(body, request.user)

        results_queryset = SortResolver(body.get("sort")).apply(
            querysets.scoped_queryset
        )

        resource_type_counts, all_resource_count = build_resource_type_counts(
            body.get("terms"), querysets.type_agnostic_queryset
        )

        page_number = body.get("page", 1)
        page_size = body.get("page_size", 20)

        paginator = Paginator(results_queryset, page_size)
        if not body.get("graphIds"):
            paginator.count = all_resource_count

        results_page = paginator.page(page_number)

        raw_aggregations = body.get("aggregations")

        aggregations = {}
        if raw_aggregations:
            aggregations = build_aggregations(results_queryset, raw_aggregations)

        resources = list(results_page.object_list)
        extra_columns_by_resource = attach_extra_columns(
            resources, extra_columns_spec, request.user
        )
        serialized_resources = [
            {
                **JSONSerializer().serializeToPython(resource),
                "extra_columns": extra_columns_by_resource.get(str(resource.pk), {}),
            }
            for resource in resources
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
                "resource_type_counts": resource_type_counts,
                "all_resource_count": all_resource_count,
            }
        )
