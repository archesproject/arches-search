from typing import Any, Dict, Optional, Set

from django.utils.translation import gettext as _
from arches.app.models import models as arches_models

TYPE_PATH = "PATH"


class NodeAliasDatatypeRegistry:
    def __init__(self, payload_query: Optional[Dict[str, Any]] = None) -> None:
        self._datatype_cache_by_graph: Dict[str, Dict[str, str]] = {}
        if payload_query is not None:
            required_aliases_by_graph = self._collect_required_aliases(payload_query)
            self._preload_required_datatypes(required_aliases_by_graph)

    def get_datatype_for_alias(self, graph_slug: str, node_alias: str) -> str:
        cache_for_graph = self._datatype_cache_by_graph.setdefault(graph_slug, {})
        cached_datatype = cache_for_graph.get(node_alias)
        if cached_datatype:
            return cached_datatype

        datatype_name = (
            arches_models.Node.objects.filter(graph__slug=graph_slug, alias=node_alias)
            .values_list("datatype", flat=True)
            .first()
        )
        if not datatype_name:
            raise ValueError(
                _("Datatype for node alias '%(alias)s' in graph '%(graph)s' not found.")
                % {"alias": node_alias, "graph": graph_slug}
            )

        cache_for_graph[node_alias] = datatype_name
        return datatype_name

    def _preload_required_datatypes(
        self, required_aliases_by_graph: Dict[str, Set[str]]
    ) -> None:
        if not required_aliases_by_graph:
            return

        graph_slugs = sorted(required_aliases_by_graph.keys())
        all_required_aliases: Set[str] = set().union(
            *required_aliases_by_graph.values()
        )
        if not all_required_aliases:
            return

        node_rows = (
            arches_models.Node.objects.filter(
                graph__slug__in=graph_slugs,
                alias__in=all_required_aliases,
            )
            .exclude(datatype__isnull=True)
            .exclude(datatype="")
            .values("graph__slug", "alias", "datatype")
        )

        for row in node_rows.iterator():
            graph_slug = row["graph__slug"]
            node_alias = row["alias"]
            if node_alias in required_aliases_by_graph[graph_slug]:
                cache_for_graph = self._datatype_cache_by_graph.setdefault(
                    graph_slug, {}
                )
                cache_for_graph[node_alias] = row["datatype"]

    def _collect_required_aliases(
        self, group_payload: Dict[str, Any]
    ) -> Dict[str, Set[str]]:
        required_aliases_by_graph: Dict[str, Set[str]] = {}

        relationship_payload = group_payload["relationship"]
        if relationship_payload is not None:
            for graph_slug, node_alias in relationship_payload["path"]:
                required_aliases_by_graph.setdefault(graph_slug, set()).add(node_alias)

        for clause_payload in group_payload["clauses"]:
            for graph_slug, node_alias in clause_payload["subject"]:
                required_aliases_by_graph.setdefault(graph_slug, set()).add(node_alias)

            for operand_payload in clause_payload["operands"]:
                if operand_payload["type"].upper() == TYPE_PATH:
                    for graph_slug, node_alias in operand_payload["value"]:
                        required_aliases_by_graph.setdefault(graph_slug, set()).add(
                            node_alias
                        )

        for child_group_payload in group_payload["groups"]:
            child_required_aliases_by_graph = self._collect_required_aliases(
                child_group_payload
            )
            for graph_slug, alias_set in child_required_aliases_by_graph.items():
                required_aliases_by_graph.setdefault(graph_slug, set()).update(
                    alias_set
                )

        return required_aliases_by_graph
