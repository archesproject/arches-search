"""
Compiles a SearchPayload into the resources it matches.

One graph at a time: each is narrowed by the term search, then by the advanced
search payload addressing it, and the results are unioned. A graph no payload
addresses is returned whole.
"""

from django.core.exceptions import ValidationError
from django.db.models import Count
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
from arches_search.utils.search.payload import SearchPayload, SearchResult
from arches_search.utils.term_search.matching import get_related_resources_by_text


def _resolve_graph_metadata(**filter_kwargs):
    """
    (graph_id, slug, name, iconclass) for the matching graphs, in a stable order.

    Ordered by slug so anything built from this -- the resource type facet, most
    visibly -- does not reshuffle between requests.
    """
    return [
        (str(graph["graphid"]), graph["slug"], graph["name"], graph["iconclass"])
        for graph in GraphModel.objects.filter(**filter_kwargs)
        .exclude(slug="arches_system_settings")
        .order_by("slug")
        .values("graphid", "slug", "name", "iconclass")
    ]


def active_resource_graph_ids():
    return _resolve_graph_metadata(isresource=True, is_active=True)


def resolve_graph_metadata_by_slug(graph_slugs):
    # isresource=True because a branch graph holds no resources: searching one
    # costs a query and can only ever return nothing.
    return _resolve_graph_metadata(slug__in=graph_slugs, isresource=True)


def union_all(querysets):
    querysets = list(querysets)
    if not querysets:
        return ResourceInstance.objects.none().values_list(
            "resourceinstanceid", flat=True
        )
    if len(querysets) == 1:
        return querysets[0]
    # resourceinstanceid is a globally-unique UUID PK, disjoint across graphs.
    return querysets[0].union(*querysets[1:], all=True)


def build_graph_payload(graph_slug, advanced_search_queries):
    """
    The advanced search payload addressing this graph, or None when none does.

    Returning None is what lets a requested graph come back unfiltered: the
    caller asked for it, and no payload had anything to say about it.
    """
    for graph_payload in advanced_search_queries or []:
        if graph_payload.get("graph_slug") == graph_slug:
            return graph_payload
    return None


class SearchCompiler:
    def __init__(self, search_payload: SearchPayload, user) -> None:
        self.search_payload = search_payload
        self.user = user
        self.facet_registry = FacetRegistry()
        self.search_model_registry = SearchModelRegistry()

    def compile(self) -> SearchResult:
        active_graphs = active_resource_graph_ids()
        active_graph_slugs = {slug for _gid, slug, _name, _icon in active_graphs}

        # graph_slugs, and each advanced search payload's own graph_slug, can
        # name a graph outside the "active" universe (e.g. is_active=False) and
        # must still be searchable -- only resource_type_counts is restricted to
        # active graphs.
        requested_slugs = list(self.search_payload.graph_slugs or [])
        queried_slugs = [
            graph_payload.get("graph_slug")
            for graph_payload in self.search_payload.advanced_search_queries or []
        ]
        missing_slugs = sorted(
            {
                graph_slug
                for graph_slug in requested_slugs + queried_slugs
                if graph_slug and graph_slug not in active_graph_slugs
            }
        )
        extra_requested_graphs = (
            resolve_graph_metadata_by_slug(missing_slugs) if missing_slugs else []
        )

        graphs_to_search = active_graphs + extra_requested_graphs

        # A payload whose graph_slug matches nothing in scope would otherwise be
        # dropped without a word -- and the graph it was meant to filter would
        # come back whole, which reads as a working search returning too much.
        searchable_slugs = {slug for _gid, slug, _name, _icon in graphs_to_search}
        unmatched_slugs = sorted(
            {
                graph_slug
                for graph_slug in queried_slugs
                if graph_slug not in searchable_slugs
            }
        )
        if unmatched_slugs:
            raise ValidationError(
                _(
                    "advanced_search_queries names %(slugs)s, which is not a "
                    "resource model being searched."
                ),
                params={"slugs": ", ".join(unmatched_slugs)},
            )

        per_graph_id_querysets = [
            self._compile_graph(graph_id, graph_slug).values_list(
                "resourceinstanceid", flat=True
            )
            for graph_id, graph_slug, _name, _icon in graphs_to_search
        ]
        all_matching_resources = ResourceInstance.objects.filter(
            resourceinstanceid__in=union_all(per_graph_id_querysets)
        )

        permission_filtered_resources = permission_backend.filter_resource_queryset(
            self.user, all_matching_resources
        )

        graph_metadata_by_id = {
            graph_id: (graph_slug, name, icon)
            for graph_id, graph_slug, name, icon in graphs_to_search
        }
        counts_by_graph_id = {
            str(row["graph_id"]): row["count"]
            for row in permission_filtered_resources.values("graph_id").annotate(
                count=Count("resourceinstanceid")
            )
        }
        # Built from the ordered list rather than the id set: a facet panel
        # rendered from this must not reshuffle between requests.
        resource_type_counts = [
            {
                "graph_id": graph_id,
                "name": name,
                "icon": icon,
                "count": counts_by_graph_id.get(graph_id, 0),
            }
            for graph_id, _slug, name, icon in active_graphs
        ]
        all_resource_count = sum(counts_by_graph_id.values())

        if self.search_payload.graph_slugs:
            requested_slug_set = set(self.search_payload.graph_slugs)
            scoped_results = permission_filtered_resources.filter(
                graph__slug__in=self.search_payload.graph_slugs
            )
            scoped_count = sum(
                count
                for graph_id, count in counts_by_graph_id.items()
                if graph_metadata_by_id.get(graph_id, (None,))[0] in requested_slug_set
            )
        else:
            # graph_slugs is the selector, so naming nothing selects nothing. The
            # counts above still cover every active graph, which is what lets a
            # caller see what naming one would get them.
            scoped_results = permission_filtered_resources.none()
            scoped_count = 0

        return SearchResult(
            results=scoped_results,
            resource_type_counts=resource_type_counts,
            all_resource_count=all_resource_count,
            scoped_count=scoped_count,
        )

    def _compile_graph(self, graph_id, graph_slug):
        """
        One graph's contribution to the result set.

        A graph addressed by an advanced search payload is filtered by it; a
        graph nothing addresses is returned whole, narrowed only by the term
        search.
        """
        term_search_pre_filter = self._resolve_term_search_pre_filter(graph_id)

        advanced_search_payload = build_graph_payload(
            graph_slug=graph_slug,
            advanced_search_queries=self.search_payload.advanced_search_queries,
        )

        if advanced_search_payload is None:
            return (
                term_search_pre_filter
                if term_search_pre_filter is not None
                else ResourceInstance.objects.filter(graph_id=graph_id)
            )

        return AdvancedSearchQueryCompiler(
            advanced_search_payload,
            facet_registry=self.facet_registry,
            search_model_registry=self.search_model_registry,
            user=self.user,
        ).compile(pre_filter=term_search_pre_filter)

    def _resolve_term_search_pre_filter(self, graph_id):
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
