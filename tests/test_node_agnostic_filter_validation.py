from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from arches_search.utils.advanced_search.advanced_search import (
    validate_node_agnostic_filters,
)

# python manage.py test tests.test_node_agnostic_filter_validation --settings="tests.test_settings"


class TextMatchDatatypeValidationTests(SimpleTestCase):
    def _text_match(self, **extra):
        return [{"type": "TEXT_MATCH", "value": ["amber"], "max_hops": 0, **extra}]

    def test_datatype_is_optional(self):
        validate_node_agnostic_filters(self._text_match())

    def test_accepts_string_datatype(self):
        validate_node_agnostic_filters(self._text_match(datatype="reference"))

    def test_rejects_empty_datatype(self):
        with self.assertRaises(ValidationError):
            validate_node_agnostic_filters(self._text_match(datatype=""))

    def test_rejects_non_string_datatype(self):
        with self.assertRaises(ValidationError):
            validate_node_agnostic_filters(self._text_match(datatype=["reference"]))
