from typing import Any, Dict, List, Optional, Set

from arches.app.models import models as arches_models

from django.utils.translation import gettext as _


class NodeAliasDatatypeRegistry:
    def __init__(self, payload_query: Optional[Dict[str, Any]] = None) -> None:
        self._graph_slug_and_node_alias_to_datatype: Dict[str, Dict[str, str]] = {}

        if payload_query:
            required_nodes = self._collect_required_nodes_from_payload(payload_query)
            self._preload_nodes(required_nodes)

    def _add_segment_if_valid(
        self, path_segment: Any, graph_slug_to_node_aliases: Dict[str, Set[str]]
    ) -> None:
        graph_slug, node_alias = path_segment
        alias_set = graph_slug_to_node_aliases.get(graph_slug)

        if alias_set is None:
            alias_set = set()
            graph_slug_to_node_aliases[graph_slug] = alias_set

        alias_set.add(node_alias)

    def _collect_required_nodes_from_payload(
        self, query_group: Dict[str, Any]
    ) -> Dict[str, Set[str]]:
        graph_slug_to_node_aliases: Dict[str, Set[str]] = {}

        pending_groups: List[Dict[str, Any]] = [query_group]
        while pending_groups:
            current_group = pending_groups.pop()

            for clause_payload in current_group.get("clauses", []):
                for subject_segment in clause_payload.get("subject", []):
                    self._add_segment_if_valid(
                        subject_segment, graph_slug_to_node_aliases
                    )

                for operand_payload in clause_payload.get("operands", []):
                    if not isinstance(operand_payload, dict):
                        continue

                    value_segments = operand_payload.get("value")
                    if isinstance(value_segments, list):
                        for value_segment in value_segments:
                            self._add_segment_if_valid(
                                value_segment, graph_slug_to_node_aliases
                            )

            nested_groups = current_group.get("groups", [])
            if nested_groups:
                pending_groups.extend(nested_groups)

        return graph_slug_to_node_aliases

    def _preload_nodes(self, graph_slug_to_node_aliases: Dict[str, Set[str]]) -> None:
        for graph_slug, required_aliases in graph_slug_to_node_aliases.items():
            existing_graph_slug_node_aliases = (
                self._graph_slug_and_node_alias_to_datatype.get(graph_slug, {})
            )

            if not required_aliases:
                if graph_slug not in self._graph_slug_and_node_alias_to_datatype:
                    self._graph_slug_and_node_alias_to_datatype[graph_slug] = {}
                continue

            missing_aliases = set(required_aliases) - set(
                existing_graph_slug_node_aliases.keys()
            )
            if not missing_aliases:
                continue

            nodes = arches_models.Node.objects.filter(
                graph__slug=graph_slug, alias__in=missing_aliases
            ).values_list("alias", "datatype")

            updated_alias_map: Dict[str, str] = dict(existing_graph_slug_node_aliases)
            for node_alias, datatype_name in nodes:
                updated_alias_map[str(node_alias)] = datatype_name

            self._graph_slug_and_node_alias_to_datatype[graph_slug] = updated_alias_map

    def lookup_node_datatype(self, graph_slug: str, node_alias: str) -> str:
        alias_map = self._graph_slug_and_node_alias_to_datatype.get(graph_slug, {})
        datatype_name = alias_map.get(node_alias)

        if not datatype_name:
            raise ValueError(
                _(
                    "Datatype for node alias '%(node_alias)s' in graph '%(graph_slug)s' not found."
                )
                % {"node_alias": node_alias, "graph_slug": graph_slug}
            )

        return datatype_name
