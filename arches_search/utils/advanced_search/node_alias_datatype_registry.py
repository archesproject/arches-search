from typing import Any, Dict, Optional, Set
from collections import defaultdict

from django.utils.translation import gettext as _
from arches.app.models import models as arches_models


class NodeAliasDatatypeRegistry:
    def __init__(self, payload_query: Optional[Dict[str, Any]] = None) -> None:
        self._datatype_cache: Dict[str, Dict[str, str]] = {}
        if payload_query is not None:
            self._preload_datatypes(
                self._collect_required_aliases_from_group(payload_query)
            )

    def get_datatype_for_alias(self, graph_slug: str, node_alias: str) -> str:
        datatypes_by_alias = self._datatype_cache.setdefault(graph_slug, {})
        cached = datatypes_by_alias.get(node_alias)
        if cached:
            return cached

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

        datatypes_by_alias[node_alias] = datatype_name
        return datatype_name

    def _preload_datatypes(
        self, required_aliases_by_graph: Dict[str, Set[str]]
    ) -> None:
        if not required_aliases_by_graph:
            return

        graph_slugs = sorted(required_aliases_by_graph)
        all_required_aliases = set().union(*required_aliases_by_graph.values())
        if not all_required_aliases:
            return

        node_rows = (
            arches_models.Node.objects.filter(
                graph__slug__in=graph_slugs, alias__in=all_required_aliases
            )
            .exclude(datatype__isnull=True)
            .exclude(datatype="")
            .values("graph__slug", "alias", "datatype")
        )

        for row in node_rows.iterator():
            graph_slug = row["graph__slug"]
            node_alias = row["alias"]
            if node_alias in required_aliases_by_graph[graph_slug]:
                self._datatype_cache.setdefault(graph_slug, {})[node_alias] = row[
                    "datatype"
                ]

    def _collect_required_aliases_from_group(
        self, group_payload: Dict[str, Any]
    ) -> Dict[str, Set[str]]:
        required_aliases_by_graph = defaultdict(set)

        relationship_payload = group_payload.get("relationship")
        if relationship_payload is not None:
            for graph_slug, node_alias in relationship_payload.get("path", []):
                required_aliases_by_graph[graph_slug].add(node_alias)

        for clause_payload in group_payload.get("clauses", []):
            for graph_slug, node_alias in clause_payload.get("subject", []):
                required_aliases_by_graph[graph_slug].add(node_alias)
            for operand_payload in clause_payload.get("operands", []):
                for graph_slug, node_alias in operand_payload.get("path", []):
                    required_aliases_by_graph[graph_slug].add(node_alias)

        for child_group_payload in group_payload.get("groups", []):
            child_required = self._collect_required_aliases_from_group(
                child_group_payload
            )
            for graph_slug, alias_set in child_required.items():
                required_aliases_by_graph[graph_slug].update(alias_set)

        return {
            graph_slug: set(alias_set)
            for graph_slug, alias_set in required_aliases_by_graph.items()
        }
