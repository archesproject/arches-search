from arches.app.datatypes.datatypes import DataTypeFactory
from arches.extensions.controlled_lists.models import ListItemValue

from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)


class ReferenceOperandNormalizer(BaseOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("reference")

    def normalize_value(self, operand_item):
        raw_value = operand_item.get("value")
        if self._is_reference_value(raw_value):
            return list(
                dict.fromkeys(
                    label["list_item_id"]
                    for reference_item in raw_value
                    for label in reference_item["labels"]
                    if label.get("list_item_id") is not None
                )
            )
        if isinstance(raw_value, str):
            raw_value = [raw_value]
        if self._is_label_list(raw_value):
            return self._list_item_ids_for_each_label(raw_value)
        return raw_value

    @staticmethod
    def _list_item_ids_for_each_label(labels):
        list_item_ids_by_label = {label: set() for label in labels}
        for label in ListItemValue.objects.labels().filter(value__in=labels):
            list_item_ids_by_label[label.value].add(str(label.list_item_id))
        return [
            tuple(sorted(list_item_ids))
            for list_item_ids in list_item_ids_by_label.values()
        ]

    @staticmethod
    def _is_label_list(raw_value):
        return isinstance(raw_value, list) and all(
            isinstance(label, str) for label in raw_value
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
