from arches.app.datatypes.datatypes import DataTypeFactory

from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)


class ResourceInstanceOperandNormalizer(BaseOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("resource-instance")

    def normalize_value(self, operand_item):
        raw_value = operand_item.get("value")
        if isinstance(raw_value, list):
            return [self._extract_resource_id(item) for item in raw_value]
        if isinstance(raw_value, dict):
            return self._extract_resource_id(raw_value)
        return raw_value

    @staticmethod
    def _extract_resource_id(resource_reference):
        if isinstance(resource_reference, dict):
            return resource_reference.get("resourceId")
        return resource_reference
