from arches.app.datatypes.datatypes import DataTypeFactory

from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)


class URLOperandNormalizer(BaseOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("url")

    def normalize_value(self, operand_item):
        raw_value = operand_item.get("value")
        if not isinstance(raw_value, dict):
            return raw_value
        return raw_value.get("url_label") or raw_value.get("url")
