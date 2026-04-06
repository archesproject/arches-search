from typing import Any, Dict

from arches_search.utils.advanced_search.constants import (
    SUBJECT_TYPE_NODE,
    SUBJECT_TYPE_SEARCH_MODELS,
)


def is_node_subject(subject: Dict[str, Any]) -> bool:
    return subject.get("type") == SUBJECT_TYPE_NODE


def is_search_models_subject(subject: Dict[str, Any]) -> bool:
    return subject.get("type") == SUBJECT_TYPE_SEARCH_MODELS
