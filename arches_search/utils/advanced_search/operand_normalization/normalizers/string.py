from django.utils.translation import get_language

from arches.app.datatypes.datatypes import DataTypeFactory

from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)


class StringOperandNormalizer(BaseOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("string")

    def normalize_value(self, operand_item):
        raw_value = operand_item.get("value")
        if not isinstance(raw_value, dict) or not raw_value:
            return raw_value
        chosen_language = self._resolve_language(operand_item, raw_value)
        return self._extract_language_entry_text(raw_value[chosen_language])

    def resolve_filter_value(self, operand_item):
        raw_value = operand_item.get("value")
        if not isinstance(raw_value, dict) or not raw_value:
            return None
        return self._resolve_language(operand_item, raw_value)

    def _resolve_language(self, operand_item, raw_value):
        active_language_code = get_language()
        short_language_code = (
            active_language_code.split("-")[0] if active_language_code else None
        )

        # The widget includes every configured language as a key even when
        # blank, so prefer non-empty entries over a bare key-presence check.
        non_empty_language_codes = [
            language_code
            for language_code, language_entry in raw_value.items()
            if self._extract_language_entry_text(language_entry)
        ]

        display_value = operand_item.get("display_value")
        if display_value:
            displayed_language_codes = [
                language_code
                for language_code in non_empty_language_codes
                if self._extract_language_entry_text(raw_value[language_code])
                == display_value
            ]
            if displayed_language_codes:
                non_empty_language_codes = displayed_language_codes

        candidate_language_codes = non_empty_language_codes or list(raw_value.keys())

        if active_language_code and active_language_code in candidate_language_codes:
            return active_language_code
        if short_language_code and short_language_code in candidate_language_codes:
            return short_language_code
        return candidate_language_codes[0]

    @staticmethod
    def _extract_language_entry_text(language_entry):
        if isinstance(language_entry, dict) and "value" in language_entry:
            return language_entry["value"]
        return language_entry
