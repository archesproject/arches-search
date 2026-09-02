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
from arches_search.utils.extra_columns import (
    annotate_node_columns,
    column_keys,
    format_node_columns,
    resolve_node_columns,
    validate_extra_columns,
)
from arches_search.utils.resource_field_search.validators import (
    validate_resource_field_filters,
)
from arches_search.utils.search_aggregation import build_aggregations
from arches_search.utils.search_sort import SORT_TYPE_EXTRA_COLUMN, SortResolver


def build_search_payload(body):
    return SearchPayload(
        graph_ids=body.get("graph_ids") or None,
        node_agnostic_filters=body.get("node_agnostic_filters"),
        advanced_search_query=body.get("advanced_search_query"),
        resource_field_filters=body.get("resource_field_filters"),
    )


class SearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        try:
            validate_node_agnostic_filters(body.get("node_agnostic_filters"))
            validate_resource_field_filters(body.get("resource_field_filters"))
            validate_extra_columns(body.get("extra_columns"))
        except ValidationError as error:
            return JSONResponse({"error": str(error)}, status=400)

        search_payload = build_search_payload(body)
        search_result = SearchCompiler(search_payload, request.user).compile()

        sort_specs = body.get("sort")
        # Sorting by a node value needs that value annotated onto the queryset,
        # so collect the columns the sort needs alongside the ones requested for
        # display and resolve both in one pass -- a column used for both then
        # costs a single annotation.
        requested_column_keys = column_keys(body.get("extra_columns"))
        # Guarded rather than trusting the shape: SortResolver validates the
        # sort payload, but it does not run until further down.
        for sort_spec in sort_specs if isinstance(sort_specs, list) else []:
            if (
                isinstance(sort_spec, dict)
                and sort_spec.get("type") == SORT_TYPE_EXTRA_COLUMN
                and isinstance(sort_spec.get("graph_slug"), str)
                and isinstance(sort_spec.get("node_alias"), str)
            ):
                sort_key = (sort_spec["graph_slug"], sort_spec["node_alias"])
                if sort_key not in requested_column_keys:
                    requested_column_keys.append(sort_key)

        nodes_by_key = resolve_node_columns(requested_column_keys, request.user)
        annotated_queryset, annotation_names = annotate_node_columns(
            search_result.results, nodes_by_key
        )

        results_queryset = SortResolver(sort_specs).apply(
            annotated_queryset, node_column_annotations=annotation_names
        )
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

        page_resources = list(results_page.object_list)
        extra_columns_by_resource = format_node_columns(
            page_resources, nodes_by_key, annotation_names
        )
        serialized_resources = []
        for resource in page_resources:
            serialized = JSONSerializer().serializeToPython(resource)
            serialized["extra_columns"] = extra_columns_by_resource.get(
                str(resource.pk), {}
            )
            serialized_resources.append(serialized)

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
