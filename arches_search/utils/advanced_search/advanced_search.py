from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db.models import Count, QuerySet
from django.utils.translation import gettext as _

from arches.app.models.models import GraphModel, ResourceInstance
from arches.app.utils import permission_backend

from arches_search.utils.advanced_search.graph_query_compiler import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.advanced_search.registries.facet_registry import FacetRegistry
from arches_search.utils.advanced_search.registries.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.node_agnostic_search.date_matching import (
    get_related_resources_by_date_range,
)
from arches_search.utils.node_agnostic_search.geometry_matching import (
    get_related_resources_by_geometry,
)
from arches_search.utils.node_agnostic_search.relationship_traversal import (
    MAX_ALLOWED_HOPS,
)
from arches_search.utils.node_agnostic_search.term_matching import (
    get_related_resources_by_text,
)

NODE_AGNOSTIC_FILTER_TYPES = {"TEXT_MATCH", "GEO_INTERSECTS", "DATE_RANGE"}


@dataclass(frozen=True)
class SearchPayload:
    graph_ids: Optional[List[str]]
    node_agnostic_filters: Optional[List[Dict[str, Any]]]
    advanced_search_query: Optional[Dict[str, Any]]


@dataclass(frozen=True)
class SearchResult:
    results: QuerySet
    resource_type_counts: List[Dict[str, Any]]
    all_resource_count: int
    scoped_count: int


def active_resource_graph_ids():
    return [
        (str(graph["graphid"]), graph["slug"], graph["name"], graph["iconclass"])
        for graph in GraphModel.objects.filter(isresource=True, is_active=True)
        .exclude(slug="arches_system_settings")
        .values("graphid", "slug", "name", "iconclass")
    ]


def _resolve_graph_metadata(**filter_kwargs):
    return [
        (str(graph["graphid"]), graph["slug"], graph["name"], graph["iconclass"])
        for graph in GraphModel.objects.filter(**filter_kwargs)
        .exclude(slug="arches_system_settings")
        .values("graphid", "slug", "name", "iconclass")
    ]


def resolve_graph_metadata_by_id(graph_ids):
    return _resolve_graph_metadata(graphid__in=graph_ids)


def resolve_graph_metadata_by_slug(graph_slugs):
    return _resolve_graph_metadata(slug__in=graph_slugs)


def union_all(querysets):
    querysets = list(querysets)
    if not querysets:
        return ResourceInstance.objects.none().values_list("resourceinstanceid", flat=True)
    if len(querysets) == 1:
        return querysets[0]
    # resourceinstanceid is a globally-unique UUID PK, disjoint across graphs.
    return querysets[0].union(*querysets[1:], all=True)


def validate_node_agnostic_filters(node_agnostic_filters):
    if node_agnostic_filters is None:
        return
    if not isinstance(node_agnostic_filters, list):
        raise ValidationError(_("node_agnostic_filters must be a list."))

    for filter_entry in node_agnostic_filters:
        if not isinstance(filter_entry, dict):
            raise ValidationError(_("Each node_agnostic_filters entry must be an object."))

        filter_type = filter_entry.get("type")
        if filter_type not in NODE_AGNOSTIC_FILTER_TYPES:
            raise ValidationError(
                _("node_agnostic_filters type must be one of %(types)s.")
                % {"types": ", ".join(sorted(NODE_AGNOSTIC_FILTER_TYPES))}
            )

        max_hops = filter_entry.get("max_hops", 0)
        if not isinstance(max_hops, int) or isinstance(max_hops, bool) or not (
            0 <= max_hops <= MAX_ALLOWED_HOPS
        ):
            raise ValidationError(
                _("max_hops must be an integer between 0 and %(max)s.")
                % {"max": MAX_ALLOWED_HOPS}
            )

        value = filter_entry.get("value")
        if filter_type == "TEXT_MATCH":
            if not isinstance(value, list) or not all(
                isinstance(term, str) and term for term in value
            ):
                raise ValidationError(
                    _("TEXT_MATCH value must be a list of non-empty strings.")
                )
        elif filter_type == "GEO_INTERSECTS":
            if not isinstance(value, dict) or value.get("type") != "FeatureCollection":
                raise ValidationError(
                    _("GEO_INTERSECTS value must be a GeoJSON FeatureCollection.")
                )
        elif filter_type == "DATE_RANGE":
            if (
                not isinstance(value, dict)
                or not isinstance(value.get("from"), str)
                or not isinstance(value.get("to"), str)
            ):
                raise ValidationError(
                    _('DATE_RANGE value must be an object with "from" and "to" strings.')
                )


def build_graph_payload(graph_slug, advanced_search_query):
    if advanced_search_query and advanced_search_query.get("graph_slug") == graph_slug:
        return advanced_search_query
    return None


def _resolve_filter_entry(filter_entry, graph_id, max_hops):
    filter_type = filter_entry["type"]
    if filter_type == "TEXT_MATCH":
        return get_related_resources_by_text(filter_entry["value"], graph_id, max_hops=max_hops)
    if filter_type == "GEO_INTERSECTS":
        return get_related_resources_by_geometry(
            filter_entry["value"], graph_id, max_hops=max_hops
        )
    if filter_type == "DATE_RANGE":
        return get_related_resources_by_date_range(
            filter_entry["value"]["from"],
            filter_entry["value"]["to"],
            graph_id,
            max_hops=max_hops,
        )
    raise ValueError(f"Unknown node_agnostic_filters entry type: {filter_type}")


class SearchCompiler:
    def __init__(self, search_payload: SearchPayload, user) -> None:
        self.search_payload = search_payload
        self.user = user
        self.facet_registry = FacetRegistry()
        self.search_model_registry = SearchModelRegistry()

    def compile(self) -> SearchResult:
        active_graphs = active_resource_graph_ids()
        active_graph_ids = {graph_id for graph_id, _slug, _name, _icon in active_graphs}
        active_graph_slugs = {slug for _gid, slug, _name, _icon in active_graphs}

        # graph_ids and advanced_search_query's own graph_slug can name a graph
        # outside the "active" universe (e.g. is_active=False) and must still be
        # searchable — only resource_type_counts is restricted to active graphs.
        extra_requested_graphs = []
        if self.search_payload.graph_ids:
            missing_graph_ids = [
                graph_id
                for graph_id in self.search_payload.graph_ids
                if graph_id not in active_graph_ids
            ]
            if missing_graph_ids:
                extra_requested_graphs += resolve_graph_metadata_by_id(missing_graph_ids)

        if self.search_payload.advanced_search_query:
            query_graph_slug = self.search_payload.advanced_search_query.get("graph_slug")
            already_covered_slugs = active_graph_slugs | {
                slug for _gid, slug, _name, _icon in extra_requested_graphs
            }
            if query_graph_slug and query_graph_slug not in already_covered_slugs:
                extra_requested_graphs += resolve_graph_metadata_by_slug([query_graph_slug])

        graphs_to_search = active_graphs + extra_requested_graphs

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
        resource_type_counts = [
            {
                "graph_id": graph_id,
                "name": graph_metadata_by_id[graph_id][1],
                "icon": graph_metadata_by_id[graph_id][2],
                "count": counts_by_graph_id.get(graph_id, 0),
            }
            for graph_id in active_graph_ids
        ]
        all_resource_count = sum(counts_by_graph_id.values())

        if self.search_payload.graph_ids:
            requested_graph_ids = set(self.search_payload.graph_ids)
            scoped_results = permission_filtered_resources.filter(
                graph_id__in=self.search_payload.graph_ids
            )
            scoped_count = sum(
                count
                for graph_id, count in counts_by_graph_id.items()
                if graph_id in requested_graph_ids
            )
        else:
            scoped_results = permission_filtered_resources
            scoped_count = all_resource_count

        return SearchResult(
            results=scoped_results,
            resource_type_counts=resource_type_counts,
            all_resource_count=all_resource_count,
            scoped_count=scoped_count,
        )

    def _compile_graph(self, graph_id, graph_slug):
        node_agnostic_pre_filter = self._resolve_node_agnostic_pre_filter(graph_id)

        advanced_search_payload = build_graph_payload(
            graph_slug=graph_slug,
            advanced_search_query=self.search_payload.advanced_search_query,
        )

        if advanced_search_payload is None:
            return (
                node_agnostic_pre_filter
                if node_agnostic_pre_filter is not None
                else ResourceInstance.objects.filter(graph_id=graph_id)
            )

        return AdvancedSearchQueryCompiler(
            advanced_search_payload,
            facet_registry=self.facet_registry,
            search_model_registry=self.search_model_registry,
        ).compile(pre_filter=node_agnostic_pre_filter)

    def _resolve_node_agnostic_pre_filter(self, graph_id):
        filter_entries = self.search_payload.node_agnostic_filters
        if not filter_entries:
            return None

        combined_matches = None
        for filter_entry in filter_entries:
            max_hops = filter_entry.get("max_hops") or 0
            entry_matches = _resolve_filter_entry(filter_entry, graph_id, max_hops)
            combined_matches = (
                entry_matches
                if combined_matches is None
                else combined_matches.filter(
                    resourceinstanceid__in=entry_matches.values("resourceinstanceid")
                )
            )
        return ResourceInstance.objects.filter(
            graph_id=graph_id,
            resourceinstanceid__in=combined_matches.values("resourceinstanceid"),
        )
