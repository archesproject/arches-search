from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.utils.date_utils import ExtendedDateFormat

from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)


class DateOperandNormalizer(BaseOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("date")

    def normalize_value(self, operand_item):
        raw_value = operand_item.get("value")
        if not isinstance(raw_value, str) or not raw_value:
            return raw_value

        # Mirrors DateIndexing.index()'s own short-circuit: a plain
        # "YYYY-MM-DD" (optionally with a time component) is common enough,
        # and slow enough to parse with the edtf library, to fast-path here.
        date_components = raw_value.split(" ")[0].split("-")
        if len(date_components[0]) == 4 and len(date_components) == 3:
            year_str, month_str, day_str = date_components
            return ExtendedDateFormat().to_sortable_date(
                int(year_str), int(month_str), int(day_str)
            )
        return ExtendedDateFormat(raw_value).lower
