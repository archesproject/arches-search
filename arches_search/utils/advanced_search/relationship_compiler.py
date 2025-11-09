from typing import Any, Dict, Tuple
from django.db.models import QuerySet


class RelationshipCompiler:
    def __init__(self, path_navigator) -> None:
        self.path_navigator = path_navigator

    def build_relationship_context(
        self, relationship_block: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], QuerySet]:
        traversal_context, child_row_set = self.path_navigator.build_relationship_pairs(
            relationship_block
        )
        return traversal_context, child_row_set

    def normalize_relationship_context(
        self, relationship_block: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self.path_navigator.normalize_relationship_context(relationship_block)
