from collections import Counter
from functools import cached_property

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
from arches_search.utils.term_matching import build_term_match_filter
from arches_search.utils.through_resource_search import get_related_resources_by_text


class SimpleSearchQuerysetBuilder:
    """
    Lazily builds the querysets a simple-search request needs, each at most
    once. graphId makes scoped_queryset and type_agnostic_queryset genuinely
    different searches when a resource type is selected; when it isn't,
    they're the same search, so type_agnostic_queryset reuses scoped_queryset
    instead of paying to rebuild it — which relies on nothing downstream
    (sorting, pagination, aggregation) ever mutating a queryset in place
    instead of chaining a new one, per normal Django QuerySet convention.

    Copies body so a caller mutating its own dict after construction can't
    invalidate an already-cached property below.
    """

    def __init__(self, body):
        self.body = dict(body)

    @cached_property
    def scoped_queryset(self):
        return build_search_queryset(self.body)

    @cached_property
    def type_agnostic_queryset(self):
        if not self.body.get("graphId"):
            return self.scoped_queryset

        return build_search_queryset({**self.body, "graphId": None})


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
                term_match_filter = build_term_match_filter(term["text"])
                if initial_match_ids is None:
                    initial_match_ids = TermSearch.objects.filter(
                        term_match_filter
                    ).values_list("resourceinstanceid", flat=True)
                else:
                    initial_match_ids = initial_match_ids.intersection(
                        TermSearch.objects.filter(term_match_filter).values_list(
                            "resourceinstanceid", flat=True
                        )
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


def build_resource_type_counts(terms, type_agnostic_queryset):
    """
    Compute per-graph and all-types resource counts.

    type_agnostic_queryset should be a
    SimpleSearchQuerysetBuilder.type_agnostic_queryset (or an equivalent
    build_search_queryset(body) result with graphId cleared) — this function
    only consumes it, it never decides how to build one.
    """
    graphs = list(
        GraphModel.objects.filter(isresource=True, is_active=True)
        .exclude(slug="arches_system_settings")
        .values("graphid", "name", "iconclass")
    )

    if terms:
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
        all_resource_count = type_agnostic_queryset.count()
    else:
        counts_by_graph_id = dict(
            type_agnostic_queryset.values_list("graph_id").annotate(
                count=Count("resourceinstanceid")
            )
        )

        all_resource_count = sum(counts_by_graph_id.values())

    return [
        {
            "graph_id": str(graph["graphid"]),
            "name": graph["name"],
            "icon": graph["iconclass"],
            "count": counts_by_graph_id.get(graph["graphid"], 0),
        }
        for graph in graphs
    ], all_resource_count
