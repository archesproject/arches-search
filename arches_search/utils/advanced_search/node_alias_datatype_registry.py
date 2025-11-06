from typing import Any, Dict, Optional, Set

from arches.app.models import models as arches_models


class NodeAliasDatatypeRegistry:
    def __init__(self, payload_query: Optional[Dict[str, Any]] = None) -> None:
        self._graph_slug_and_node_alias_to_datatype: Dict[str, Dict[str, str]] = {}
        if payload_query:
            needed = self._collect_required_nodes_from_payload(payload_query)
            print(f"[ADV][ALIAS] preload needed graphs={list(needed.keys())}")
            self._preload_nodes(needed)

    # ---------- public API ----------------------------------------------------

    def get_datatype_for_alias(self, graph_slug: str, node_alias: str) -> str:
        cached = self._graph_slug_and_node_alias_to_datatype.get(graph_slug, {}).get(
            node_alias
        )
        if cached:
            return cached

        print(
            f"[ADV][ALIAS] MISS graph={graph_slug} alias={node_alias} -> values() lookup"
        )
        row = (
            arches_models.Node.objects.filter(graph__slug=graph_slug, alias=node_alias)
            .values("datatype")
            .first()
        )
        if not row:
            raise ValueError(
                f"Datatype for node alias '{node_alias}' in graph '{graph_slug}' not found."
            )

        datatype_name = row.get("datatype")
        if not datatype_name:
            raise ValueError(
                f"Datatype missing for alias '{node_alias}' in graph '{graph_slug}'."
            )

        self._graph_slug_and_node_alias_to_datatype.setdefault(graph_slug, {})[
            node_alias
        ] = datatype_name
        print(
            f"[ADV][ALIAS] CACHED graph={graph_slug} alias={node_alias} -> {datatype_name}"
        )
        return datatype_name

    # ---------- preload + collectors -----------------------------------------

    def _preload_nodes(self, needed: Dict[str, Set[str]]) -> None:
        if not needed:
            print("[ADV][ALIAS] nothing to preload")
            return

        slugs = sorted(needed.keys())
        print(f"[ADV][ALIAS] preloading node aliases for graphs={slugs}")

        queryset = arches_models.Node.objects.filter(graph__slug__in=slugs).values(
            "graph__slug", "alias", "datatype"
        )

        loaded_count = 0
        for row in queryset.iterator():
            graph_slug = row.get("graph__slug")
            node_alias = row.get("alias")
            datatype_name = row.get("datatype")
            if not graph_slug or not node_alias:
                continue
            if (
                graph_slug in needed
                and node_alias in needed[graph_slug]
                and datatype_name
            ):
                self._graph_slug_and_node_alias_to_datatype.setdefault(graph_slug, {})[
                    node_alias
                ] = datatype_name
                loaded_count += 1

        print(f"[ADV][ALIAS] preloaded={loaded_count}")

    def _collect_required_nodes_from_payload(
        self, group: Dict[str, Any]
    ) -> Dict[str, Set[str]]:
        accumulated: Dict[str, Set[str]] = {}

        def add_segment_if_valid(segment: Any) -> None:
            if isinstance(segment, (list, tuple)) and len(segment) == 2:
                graph_slug, node_alias = segment
                if graph_slug and node_alias:
                    accumulated.setdefault(graph_slug, set()).add(node_alias)

        def add_path_if_valid(path_value: Any) -> None:
            if isinstance(path_value, list):
                for segment in path_value:
                    add_segment_if_valid(segment)

        # relationship.path
        relationship_payload = group.get("relationship") or {}
        if isinstance(relationship_payload, dict) and relationship_payload.get("path"):
            print(
                f"[ADV][ALIAS] collect relationship path={relationship_payload.get('path')}"
            )
            add_path_if_valid(relationship_payload.get("path"))

        # clauses: subjects + operand paths
        for clause_payload in group.get("clauses") or []:
            subject_path = clause_payload.get("subject")
            if subject_path:
                print(f"[ADV][ALIAS] collect clause subject={subject_path}")
                add_path_if_valid(subject_path)
            for operand in clause_payload.get("operands") or []:
                operand_path = operand.get("path")
                if operand_path:
                    print(f"[ADV][ALIAS] collect operand path={operand_path}")
                    add_path_if_valid(operand_path)

        # recurse
        for child_group in group.get("groups") or []:
            child_needed = self._collect_required_nodes_from_payload(child_group)
            for child_graph_slug, alias_set in child_needed.items():
                accumulated.setdefault(child_graph_slug, set()).update(alias_set)

        return accumulated
