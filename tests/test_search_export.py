from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from openpyxl import load_workbook

from arches_search.utils.search_export import SearchExcelExporter

# python manage.py test tests.test_search_export --settings="tests.test_settings"


class SearchExcelExporterTest(SimpleTestCase):
    def _make_resource(self, resourceinstanceid, graph_slug, name, descriptors=None):
        resource = MagicMock()
        resource.resourceinstanceid = resourceinstanceid
        resource.graph.slug = graph_slug
        resource.name = name
        resource.descriptors = descriptors
        return resource

    def _export_with_resources(self, resources, languages):
        queryset = MagicMock()
        queryset.select_related.return_value.iterator.return_value = resources
        exporter = SearchExcelExporter()
        with patch.object(
            SearchExcelExporter, "_collect_languages", return_value=languages
        ):
            return exporter.export(queryset)

    def _get_row(self, output, row_index):
        ws = load_workbook(filename=output).active
        return [ws.cell(row_index, col).value for col in range(1, ws.max_column + 1)]

    def test_undefined_description_is_blank(self):
        resource = self._make_resource(
            "abc-123",
            "heritage_site",
            "Parthenon",
            descriptors={"en": {"description": "Undefined"}},
        )
        output = self._export_with_resources([resource], ["en"])
        row = self._get_row(output, row_index=2)
        self.assertFalse(row[3])  # en-description column should be blank

    def test_language_columns_and_missing_descriptors(self):
        # Resource has "en" but not "fr"; another has None descriptors entirely
        resource_with_en = self._make_resource(
            "abc-123",
            "heritage_site",
            "Parthenon",
            descriptors={"en": {"description": "A temple"}},
        )
        resource_no_descriptors = self._make_resource(
            "def-456",
            "heritage_site",
            "Colosseum",
            descriptors={"fr": {"description": "Un amphithéâtre"}},
        )
        output = self._export_with_resources(
            [resource_with_en, resource_no_descriptors], ["en", "fr"]
        )
        headers = self._get_row(output, row_index=1)
        row1 = self._get_row(output, row_index=2)
        row2 = self._get_row(output, row_index=3)

        self.assertEqual(headers[3], "en-description")
        self.assertEqual(headers[4], "fr-description")
        self.assertEqual(row1[3], "A temple")  # en present
        self.assertFalse(row1[4])  # fr missing -> blank
        self.assertFalse(row2[3])  # en missing -> blank
        self.assertEqual(row2[4], "Un amphithéâtre")  # fr present
