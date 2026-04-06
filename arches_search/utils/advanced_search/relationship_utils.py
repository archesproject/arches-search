from typing import Any, Dict, Tuple

from arches_search.utils.advanced_search.constants import SUBJECT_TYPE_NODE


def is_node_relationship_path(path: Any) -> bool:
    return isinstance(path, dict) and path.get("type") == SUBJECT_TYPE_NODE


def has_relationship_path(relationship_payload: Any) -> bool:
    if not isinstance(relationship_payload, dict):
        return False

    path = relationship_payload.get("path")
    return (
        is_node_relationship_path(path)
        and isinstance(path.get("graph_slug"), str)
        and bool(path.get("graph_slug"))
        and isinstance(path.get("node_alias"), str)
        and bool(path.get("node_alias"))
    )


def relationship_path_to_pair(path: Dict[str, Any]) -> Tuple[str, str]:
    if not is_node_relationship_path(path):
        raise ValueError("Relationship path must be a NODE object.")

    graph_slug = path.get("graph_slug")
    node_alias = path.get("node_alias")

    if not isinstance(graph_slug, str) or not graph_slug:
        raise ValueError("Relationship path graph_slug must be a non-empty string.")
    if not isinstance(node_alias, str) or not node_alias:
        raise ValueError("Relationship path node_alias must be a non-empty string.")

    return graph_slug, node_alias
