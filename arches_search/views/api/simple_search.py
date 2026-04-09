from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchQuery

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.models.models import TermSearch
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.search_aggregation import build_aggregations
from arches_search.utils.through_resource_search import get_related_resources_by_text


from arches.app.models.models import (
    ResourceInstance,
)


class SimpleSearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        terms = body.get("terms")
        query = body.get("query")
        graph_id = body.get("graphId")

        results_queryset = None
        if terms:
            if graph_id:
                results_queryset = get_related_resources_by_text(terms, graph_id)
            else:
                initial_match_ids = None
                for term in terms:
                    sq = SearchQuery(term, search_type="plain")
                    if initial_match_ids is None:
                        initial_match_ids = TermSearch.objects.filter(
                            search_vector=sq
                        ).values_list("resourceinstanceid", flat=True)
                    else:
                        initial_match_ids = initial_match_ids.intersection(
                            TermSearch.objects.filter(search_vector=sq).values_list(
                                "resourceinstanceid", flat=True
                            )
                        )
                results_queryset = ResourceInstance.objects.filter(
                    resourceinstanceid__in=initial_match_ids
                )

        if query:
            if results_queryset is None:
                base = ResourceInstance.objects.all()
                if graph_id:
                    base = base.filter(graph_id=graph_id)
                results_queryset = base
            results_queryset = AdvancedSearchQueryCompiler(query).compile(
                results_queryset.values_list("resourceinstanceid")
            )

        if not terms and not query:
            results_queryset = ResourceInstance.objects.all()
            if graph_id:
                results_queryset = results_queryset.filter(graph_id=graph_id)

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
