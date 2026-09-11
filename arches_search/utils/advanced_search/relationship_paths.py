from typing import Any, Dict, Tuple

from arches_search.utils.advanced_search.constants import SUBJECT_TYPE_NODE


def is_node_relationship_path(path: Any) -> bool:
    """Used by PayloadValidator to check that a path dict is a NODE subject."""
    return isinstance(path, dict) and path.get("type") == SUBJECT_TYPE_NODE


def has_relationship_path(relationship_payload: Any) -> bool:
    """True when a group's relationship block is present (i.e. not null)."""
    return relationship_payload is not None


def relationship_path_to_pair(path: Dict[str, Any]) -> Tuple[str, str]:
    """Extract (graph_slug, node_alias) from a validated relationship path dict."""
    return path["graph_slug"], path["node_alias"]
