"""
Runs a whole search: filter, project, order, paginate, aggregate.

The HTTP API is a thin wrapper over this. Anything in the same process -- another
Arches application, a management command, a report -- calls execute_search
directly rather than posting to the endpoint.
"""

from typing import Any, Dict, List, Tuple

from django.core.paginator import EmptyPage, Paginator

from arches.app.utils.betterJSONSerializer import JSONSerializer

from arches_search.utils.search.additional_data import (
    AdditionalData,
    validate_additional_data,
)
from arches_search.utils.search.compiler import SearchCompiler
from arches_search.utils.search.payload import SearchRequest, SearchResponse
from arches_search.utils.search.validation import (
    validate_paging,
    validate_search_payload,
)
from arches_search.utils.search.aggregation import build_aggregations
from arches_search.utils.search.sorting import SORT_TYPE_NODE, SortResolver


def execute_search(search_request: SearchRequest, user) -> SearchResponse:
    """
    Raises ValidationError for anything the caller got wrong, which the API
    turns into a 400.
    """
    payload = search_request.payload

    validate_search_payload(payload)
    validate_additional_data(search_request.additional_data)
    validate_paging(search_request.page, search_request.page_size)
    sort_resolver = SortResolver(search_request.sort)

    # Each advanced search payload validates itself as it compiles, so compiling
    # belongs in the same guarded stretch as the checks above: an unknown field
    # or operator is a bad request, not a 500.
    search_result = SearchCompiler(payload, user).compile()

    additional_data = AdditionalData(
        search_request.additional_data,
        user,
        # Ordering by a node value needs that value annotated too. A node wanted
        # for both display and ordering still resolves to one annotation,
        # because the name comes from the node rather than its position.
        also_project_nodes=_node_keys_an_ordering_needs(sort_resolver),
    )

    results_queryset = sort_resolver.apply(
        additional_data.annotate(search_result.results),
        node_column_annotations=additional_data.node_annotation_names,
    )

    paginator = Paginator(results_queryset, search_request.page_size)
    # Skips Paginator's own COUNT(*) -- the total is already known.
    paginator.count = search_result.scoped_count

    try:
        results_page = paginator.page(search_request.page)
        page_resources = list(results_page.object_list)
        has_next, has_previous = results_page.has_next(), results_page.has_previous()
    except EmptyPage:
        # Asking for a page past the end is not an error -- num_pages below says
        # where the end is, so an empty page is the honest answer.
        page_resources = []
        has_next, has_previous = False, True

    return SearchResponse(
        resources=_serialize_resources(page_resources, additional_data),
        pagination={
            "page": search_request.page,
            "page_size": search_request.page_size,
            "total_results": paginator.count,
            "num_pages": paginator.num_pages,
            "has_next": has_next,
            "has_previous": has_previous,
        },
        aggregations=(
            build_aggregations(results_queryset, search_request.aggregations)
            if search_request.aggregations
            else {}
        ),
        resource_type_counts=search_result.resource_type_counts,
        all_resource_count=search_result.all_resource_count,
    )


def _node_keys_an_ordering_needs(
    sort_resolver: SortResolver,
) -> List[Tuple[str, str]]:
    """The (graph_slug, node_alias) pairs the sort specs order by."""
    return [
        (sort_spec["graph_slug"], sort_spec["node_alias"])
        for sort_spec in sort_resolver.sort_specs
        if sort_spec["type"] == SORT_TYPE_NODE
    ]


def _serialize_resources(
    page_resources, additional_data: AdditionalData
) -> List[Dict[str, Any]]:
    additional_data_by_resource = additional_data.format(page_resources)

    serialized_resources = []
    for resource in page_resources:
        serialized = JSONSerializer().serializeToPython(resource)
        serialized["additional_data"] = additional_data_by_resource.get(
            str(resource.pk), {}
        )
        serialized_resources.append(serialized)
    return serialized_resources
