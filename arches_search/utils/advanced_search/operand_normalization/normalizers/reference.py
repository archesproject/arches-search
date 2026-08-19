from arches.app.datatypes.datatypes import DataTypeFactory

from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)


class ReferenceOperandNormalizer(BaseOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("reference")

    def normalize_value(self, operand_item):
        raw_value = operand_item.get("value")
        if not self._is_reference_value(raw_value):
            return raw_value
        return list(
            dict.fromkeys(
                label.get("value")
                for reference_item in raw_value
                for label in reference_item.get("labels") or []
                if label.get("value") is not None
            )
        )

    @staticmethod
    def _is_reference_value(raw_value):
        return (
            isinstance(raw_value, list)
            and bool(raw_value)
            and all(
                isinstance(reference_item, dict) and "labels" in reference_item
                for reference_item in raw_value
            )
        )
