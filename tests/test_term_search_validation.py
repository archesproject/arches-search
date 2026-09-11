from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from arches_search.utils.search import validate_term_search

# python manage.py test tests.test_term_search_validation --settings="tests.test_settings"


class TermSearchTermValidationTests(SimpleTestCase):
    def _term_search(self, *terms):
        return {"terms": list(terms), "max_hops": 0}

    def test_accepts_plain_string_terms(self):
        validate_term_search(self._term_search("amber"))

    def test_accepts_a_term_restricted_to_a_datatype(self):
        validate_term_search(
            self._term_search("amber", {"text": "adobe", "datatype": "reference"})
        )

    def test_rejects_a_term_object_without_a_datatype(self):
        with self.assertRaises(ValidationError):
            validate_term_search(self._term_search({"text": "adobe"}))

    def test_rejects_an_empty_datatype(self):
        with self.assertRaises(ValidationError):
            validate_term_search(self._term_search({"text": "adobe", "datatype": ""}))

    def test_rejects_a_non_string_datatype(self):
        with self.assertRaises(ValidationError):
            validate_term_search(
                self._term_search({"text": "adobe", "datatype": ["reference"]})
            )
