from collections import Counter

from django.contrib.postgres.search import SearchQuery
from django.db.models import Count

from arches.app.models.models import (
    GraphModel,
    ResourceInstance,
)

from arches_search.models.models import GeometrySearch, TermSearch
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.geo_utils import GeoUtils
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
                term_search_query = SearchQuery(
                    term["text"], search_type="plain", config="english"
                )
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

    return results_queryset.exclude(graph__slug="arches_system_settings")


def build_resource_type_counts(body):
    graphs = list(
        GraphModel.objects.filter(isresource=True, is_active=True)
        .exclude(slug="arches_system_settings")
        .values("graphid", "name", "iconclass")
    )
    terms = body.get("terms")
    all_resource_count = build_search_queryset({**body, "graphId": None}).count()

    if terms:
        # graphId changes the retrieval algorithm itself (2-hop traversal via
        # get_related_resources_by_text) — each type's match set is a
        # genuinely different query, not a filtered view of one shared
        # queryset. Batched as a single UNION ALL so the round-trip count
        # stays O(1) in the number of active resource models, not O(N).
        term_texts = [term["text"] for term in terms]
        per_graph_matches = [
            get_related_resources_by_text(
                term_texts, str(graph["graphid"])
            ).values_list("graph_id", flat=True)
            for graph in graphs
        ]
        if not per_graph_matches:
            combined_matches = []
        elif len(per_graph_matches) == 1:
            combined_matches = per_graph_matches[0]
        else:
            combined_matches = per_graph_matches[0].union(
                *per_graph_matches[1:], all=True
            )
        counts_by_graph_id = Counter(combined_matches)
    else:
        # query/mapFilter-only: graphId is a plain trailing filter here, so
        # one grouped query is correct and cheap — no per-graph fan-out needed.
        type_agnostic_queryset = build_search_queryset({**body, "graphId": None})
        counts_by_graph_id = dict(
            type_agnostic_queryset.values_list("graph_id").annotate(
                count=Count("resourceinstanceid")
            )
        )

    return [
        {
            "graph_id": str(graph["graphid"]),
            "name": graph["name"],
            "icon": graph["iconclass"],
            "count": counts_by_graph_id.get(graph["graphid"], 0),
        }
        for graph in graphs
    ], all_resource_count
