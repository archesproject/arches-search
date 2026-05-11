from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchQuery


from arches.app.models.models import (
    ResourceInstance,
)
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.models.models import GeometrySearch, TermSearch
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.geo_utils import GeoUtils
from arches_search.utils.search_aggregation import build_aggregations
from arches_search.utils.search_sort import SortResolver
from arches_search.utils.through_resource_search import get_related_resources_by_text


def build_search_queryset(body):
    terms = body.get("terms")
    query = body.get("query")
    graph_id = body.get("graphId")

    results_queryset = None
    if terms:
        if graph_id:
            term_texts = [term["text"] for term in terms]
            results_queryset = get_related_resources_by_text(term_texts, graph_id)
        else:
            initial_match_ids = None
            for term in terms:
                term_search_query = SearchQuery(term["text"], search_type="plain")
                if initial_match_ids is None:
                    initial_match_ids = TermSearch.objects.filter(
                        search_vector=term_search_query
                    ).values_list("resourceinstanceid", flat=True)
                else:
                    initial_match_ids = initial_match_ids.intersection(
                        TermSearch.objects.filter(
                            search_vector=term_search_query
                        ).values_list("resourceinstanceid", flat=True)
                    )
            results_queryset = ResourceInstance.objects.filter(
                resourceinstanceid__in=initial_match_ids
            )

    if query:
        if results_queryset is None:
            base_queryset = ResourceInstance.objects.all()
            if graph_id:
                base_queryset = base_queryset.filter(graph_id=graph_id)
            results_queryset = base_queryset
        results_queryset = AdvancedSearchQueryCompiler(query).compile(results_queryset)

    if not terms and not query:
        results_queryset = ResourceInstance.objects.all()
        if graph_id:
            results_queryset = results_queryset.filter(graph_id=graph_id)

    map_filter = body.get("mapFilter")
    if map_filter and map_filter.get("features"):
        union_geom = GeoUtils().map_filter_to_union(map_filter)
        if union_geom:
            spatial_ids = GeometrySearch.objects.filter(
                geom__intersects=union_geom
            ).values_list("resourceinstanceid", flat=True)
            results_queryset = results_queryset.filter(
                resourceinstanceid__in=spatial_ids
            )

    return results_queryset


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
            }
        )
