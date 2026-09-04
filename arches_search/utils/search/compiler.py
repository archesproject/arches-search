"""
Compiles a SearchPayload into the resources it matches.

One graph at a time: each is narrowed by the term search, then by the advanced
search payload addressing it, and the results are unioned. A graph no payload
addresses is returned whole.
"""

from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db.models import Count, QuerySet
from django.utils.translation import gettext as _

from arches.app.models.models import GraphModel, ResourceInstance
from arches.app.utils import permission_backend

from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.advanced_search.registries.facet_registry import FacetRegistry
from arches_search.utils.advanced_search.registries.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.search.types import SearchPayload, SearchResult
from arches_search.utils.term_search.matching import get_related_resources_by_text


class SearchableGraph(NamedTuple):
    id: str
    slug: str
    name: str
    icon: str


def _resolve_graphs(**filter_kwargs) -> List[SearchableGraph]:
    """
    The matching resource graphs, in a stable order.

    Ordered by slug so anything built from this -- the resource type facet, most
    visibly -- does not reshuffle between requests.
    """
    return [
        SearchableGraph(
            id=str(graph["graphid"]),
            slug=graph["slug"],
            name=graph["name"],
            icon=graph["iconclass"],
        )
        for graph in GraphModel.objects.filter(**filter_kwargs)
        .exclude(slug="arches_system_settings")
        .order_by("slug")
        .values("graphid", "slug", "name", "iconclass")
    ]


def _union_all(querysets: Iterable[QuerySet]) -> QuerySet:
    querysets = list(querysets)
    if not querysets:
        return ResourceInstance.objects.none().values_list(
            "resourceinstanceid", flat=True
        )
    if len(querysets) == 1:
        return querysets[0]
    # resourceinstanceid is a globally-unique UUID PK, disjoint across graphs.
    return querysets[0].union(*querysets[1:], all=True)


def _counts_by_graph_id(matches: QuerySet) -> Dict[str, int]:
    return {
        str(row["graph_id"]): row["count"]
        for row in matches.values("graph_id").annotate(
            count=Count("resourceinstanceid")
        )
    }


def _resource_type_counts(
    active_graphs: List[SearchableGraph], counts_by_graph_id: Dict[str, int]
) -> List[Dict[str, Any]]:
    # Ordered, so a facet panel built from this does not reshuffle.
    return [
        {
            "graph_id": graph.id,
            "name": graph.name,
            "icon": graph.icon,
            "count": counts_by_graph_id.get(graph.id, 0),
        }
        for graph in active_graphs
    ]


class SearchCompiler:
    def __init__(self, search_payload: SearchPayload, user) -> None:
        self.search_payload = search_payload
        self.user = user
        self.facet_registry = FacetRegistry()
        self.search_model_registry = SearchModelRegistry()
        # One payload per graph at most; two for the same graph is already a
        # validation error, so nothing here has to resolve a conflict.
        self.payloads_by_slug = {
            graph_payload.get("graph_slug"): graph_payload
            for graph_payload in search_payload.advanced_search_queries or []
        }

    def compile(self) -> SearchResult:
        active_graphs = _resolve_graphs(isresource=True, is_active=True)
        graphs_to_search = self._graphs_to_search(active_graphs)

        matches = self._permitted_matches(graphs_to_search)
        counts_by_graph_id = _counts_by_graph_id(matches)
        scoped_results, scoped_count = self._scope_to_requested(
            matches, graphs_to_search, counts_by_graph_id
        )

        return SearchResult(
            results=scoped_results,
            resource_type_counts=_resource_type_counts(
                active_graphs, counts_by_graph_id
            ),
            all_resource_count=sum(counts_by_graph_id.values()),
            scoped_count=scoped_count,
        )

    def _graphs_to_search(
        self, active_graphs: List[SearchableGraph]
    ) -> List[SearchableGraph]:
        """
        Every active resource model, plus any inactive one named explicitly.

        A named graph may be inactive and must still be searchable; only
        resource_type_counts is restricted to active graphs.
        """
        queried_slugs = set(self.payloads_by_slug)
        named_slugs = queried_slugs | set(self.search_payload.graph_slugs or [])

        active_slugs = {graph.slug for graph in active_graphs}
        missing_slugs = sorted(slug for slug in named_slugs if slug not in active_slugs)
        graphs_to_search = active_graphs + (
            # isresource: a branch graph holds no resources, so searching one
            # could only return nothing.
            _resolve_graphs(slug__in=missing_slugs, isresource=True)
            if missing_slugs
            else []
        )

        unmatched_slugs = sorted(
            queried_slugs - {graph.slug for graph in graphs_to_search}
        )
        if unmatched_slugs:
            raise ValidationError(
                _(
                    "advanced_search_queries names %(slugs)s, which is not a "
                    "resource model being searched."
                ),
                params={"slugs": ", ".join(unmatched_slugs)},
            )

        return graphs_to_search

    def _permitted_matches(self, graphs_to_search: List[SearchableGraph]) -> QuerySet:
        """Each graph's matches, unioned, then narrowed to what the user may see."""
        per_graph_ids = [
            self._compile_graph(graph).values_list("resourceinstanceid", flat=True)
            for graph in graphs_to_search
        ]
        return permission_backend.filter_resource_queryset(
            self.user,
            ResourceInstance.objects.filter(
                resourceinstanceid__in=_union_all(per_graph_ids)
            ),
        )

    def _scope_to_requested(
        self,
        matches: QuerySet,
        graphs_to_search: List[SearchableGraph],
        counts_by_graph_id: Dict[str, int],
    ) -> Tuple[QuerySet, int]:
        """
        The requested graphs' resources, and how many there are.

        Summed from counts already gathered rather than counted again, which is
        what lets the paginator skip its own COUNT(*).
        """
        requested_slugs = set(self.search_payload.graph_slugs or [])
        if not requested_slugs:
            # The counts still cover every graph, so a caller can see what
            # selecting one would return.
            return matches.none(), 0

        slug_by_graph_id = {graph.id: graph.slug for graph in graphs_to_search}
        scoped_count = sum(
            count
            for graph_id, count in counts_by_graph_id.items()
            if slug_by_graph_id.get(graph_id) in requested_slugs
        )
        return matches.filter(graph__slug__in=requested_slugs), scoped_count

    def _compile_graph(self, graph: SearchableGraph) -> QuerySet:
        """
        One graph's contribution to the result set.

        A graph addressed by an advanced search payload is filtered by it; a
        graph nothing addresses is returned whole, narrowed only by the term
        search.
        """
        term_search_pre_filter = self._term_search_pre_filter(graph.id)
        advanced_search_payload = self.payloads_by_slug.get(graph.slug)

        if advanced_search_payload is None:
            if term_search_pre_filter is not None:
                return term_search_pre_filter
            return ResourceInstance.objects.filter(graph_id=graph.id)

        return AdvancedSearchQueryCompiler(
            advanced_search_payload,
            facet_registry=self.facet_registry,
            search_model_registry=self.search_model_registry,
            user=self.user,
        ).compile(pre_filter=term_search_pre_filter)

    def _term_search_pre_filter(self, graph_id: str) -> Optional[QuerySet]:
        """
        This graph's resources narrowed by the term search, or None when there
        is not one.

        get_related_resources_by_text expands each term independently and then
        intersects, so every term is handled in a single call.
        """
        term_search = self.search_payload.term_search
        if not term_search or not term_search.get("terms"):
            return None

        matches = get_related_resources_by_text(
            term_search["terms"],
            graph_id,
            max_hops=term_search.get("max_hops") or 0,
        )
        return ResourceInstance.objects.filter(
            graph_id=graph_id,
            resourceinstanceid__in=matches.values("resourceinstanceid"),
        )
