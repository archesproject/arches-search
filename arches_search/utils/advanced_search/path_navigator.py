from __future__ import annotations
from typing import Tuple, Sequence, Dict, Any

from django.db.models import QuerySet, OuterRef
from arches_search.utils.advanced_search.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.advanced_search.node_alias_datatype_registry import (
    NodeAliasDatatypeRegistry,
)


class PathNavigator:
    def __init__(
        self,
        search_model_registry: SearchModelRegistry,
        node_alias_datatype_registry: NodeAliasDatatypeRegistry,
    ) -> None:
        self.search_model_registry = search_model_registry
        self.node_alias_datatype_registry = node_alias_datatype_registry

    def build_path_queryset(
        self,
        path_segments: Sequence[Tuple[str, str]] | None = None,
    ) -> Tuple[str, str, QuerySet]:
        if not path_segments:
            raise ValueError("path must contain at least one segment")

        terminal_graph_slug, terminal_node_alias = path_segments[-1]
        terminal_datatype_name = (
            self.node_alias_datatype_registry.get_datatype_for_alias(
                terminal_graph_slug, terminal_node_alias
            )
        )
        terminal_search_model = self.search_model_registry.get_model_for_datatype(
            terminal_datatype_name
        )

        terminal_queryset = terminal_search_model.objects.filter(
            graph_slug=terminal_graph_slug,
            node_alias=terminal_node_alias,
        ).order_by()

        return terminal_datatype_name, terminal_graph_slug, terminal_queryset

    def build_relationship_pairs(
        self,
        relationship_context: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], QuerySet]:
        relationship_path = relationship_context["path"]
        is_inverse_relationship = bool(relationship_context.get("is_inverse"))

        terminal_datatype_name, terminal_graph_slug, pair_raw = (
            self.build_path_queryset(relationship_path)
        )
        if (terminal_datatype_name or "").lower() not in [
            "resource-instance",
            "resource-instance-list",
        ]:
            raise ValueError("Relationship must end on a resource-instance node")

        if is_inverse_relationship:
            pairs_scoped_to_anchor = pair_raw.filter(
                value=OuterRef("resourceinstanceid")
            )
            anchor_id_field = "value"
            child_id_field = "resourceinstanceid"
        else:
            pairs_scoped_to_anchor = pair_raw.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            )
            anchor_id_field = "resourceinstanceid"
            child_id_field = "value"

        compiled_pair_info = {
            "pair_queryset": pair_raw,
            "anchor_id_field": anchor_id_field,
            "child_id_field": child_id_field,
            "terminal_graph_slug": terminal_graph_slug,
            "terminal_node_alias": relationship_path[-1][1],
            "is_inverse": is_inverse_relationship,
        }
        return compiled_pair_info, pairs_scoped_to_anchor

    def build_scoped_pairs_for_path(
        self,
        path_segments: Sequence[Tuple[str, str]],
        is_inverse_relationship: bool,
        correlate_on_field: str,
    ) -> Tuple[str, str, QuerySet, str]:
        terminal_datatype_name, terminal_graph_slug, pair_raw = (
            self.build_path_queryset(path_segments)
        )
        if (terminal_datatype_name or "").lower() not in [
            "resource-instance",
            "resource-instance-list",
        ]:
            raise ValueError("Nested relationship must end on a resource-instance node")

        if is_inverse_relationship:
            scoped_pairs = pair_raw.filter(value=OuterRef(correlate_on_field))
            nested_child_id_field = "resourceinstanceid"
        else:
            scoped_pairs = pair_raw.filter(
                resourceinstanceid=OuterRef(correlate_on_field)
            )
            nested_child_id_field = "value"

        return (
            terminal_datatype_name,
            terminal_graph_slug,
            scoped_pairs,
            nested_child_id_field,
        )

    def datatype_for(self, graph_slug: str, node_alias: str) -> str:
        return self.node_alias_datatype_registry.get_datatype_for_alias(
            graph_slug, node_alias
        )

    def terminal_graph_slug(self, path, is_inverse: bool = False) -> str:
        # your paths already specify the terminal segment explicitly
        # inverse doesn’t change which graph the terminal segment names
        if not path:
            raise ValueError("path must contain at least one segment")
        return path[-1][0]
