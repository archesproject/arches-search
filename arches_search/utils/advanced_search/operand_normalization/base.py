from typing import Any, Optional

from arches.app.datatypes.datatypes import BaseDataType


class BaseOperandNormalizer:
    def __init__(self):
        self.datatype: Optional[BaseDataType] = None

    def normalize_value(self, operand_item: dict) -> Any:
        """Value to substitute into operand_item["value"] before comparison."""
        return operand_item.get("value")

    def resolve_filter_value(self, operand_item: dict) -> Any:
        """Value to compare against the facet's filter_field column, if any."""
        return None
