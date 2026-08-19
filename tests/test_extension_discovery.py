from django.apps import apps
from django.test import TestCase

from arches_search.indexing.base import BaseIndexing
from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)
from arches_search.utils.extension_discovery import discover_extension_instances

# python manage.py test tests.test_extension_discovery --settings="tests.test_settings"


class _ThrowawayDatatype:
    datatype_name = "throwaway-cross-app-discovery-test-datatype"


class ThrowawayCrossAppNormalizer(BaseOperandNormalizer):
    """Stands in for a class living in a third-party app's own codebase."""

    def __init__(self):
        super().__init__()
        self.datatype = _ThrowawayDatatype()

    def normalize_value(self, operand_item):
        return "normalized-by-throwaway-cross-app-normalizer"


class ExtensionDiscoverySelfScanTests(TestCase):
    def test_finds_arches_search_own_indexers(self):
        registry = discover_extension_instances(
            "search_indexers",
            BaseIndexing,
            lambda indexer: indexer.datatype.datatype_name,
        )

        self.assertIn("url", registry)
        self.assertIn("reference", registry)
        self.assertIn("resource-instance-list", registry)

    def test_finds_arches_search_own_operand_normalizers(self):
        registry = discover_extension_instances(
            "advanced_search_operand_normalizers",
            BaseOperandNormalizer,
            lambda normalizer: normalizer.datatype.datatype_name,
        )

        self.assertEqual(len(registry), 8)
        self.assertIn("reference", registry)
        self.assertIn("url", registry)

    def test_apps_with_no_attribute_are_skipped_without_error(self):
        # arches_vue_components, arches_controlled_lists, arches_modular_reports,
        # arches_querysets don't declare advanced_search_operand_normalizers -
        # this must be skipped silently, not raise.
        registry = discover_extension_instances(
            "advanced_search_operand_normalizers",
            BaseOperandNormalizer,
            lambda normalizer: normalizer.datatype.datatype_name,
        )

        self.assertEqual(len(registry), 8)


class ExtensionDiscoveryCrossAppTests(TestCase):
    """Proves discovery works for a class declared on a genuinely different
    installed app's AppConfig, not just arches_search's own."""

    def setUp(self):
        self.modular_reports_config = apps.get_app_config("arches_modular_reports")
        self.addCleanup(
            delattr, self.modular_reports_config, "advanced_search_operand_normalizers"
        )
        self.modular_reports_config.advanced_search_operand_normalizers = [
            "tests.test_extension_discovery.ThrowawayCrossAppNormalizer",
        ]

    def test_discovers_normalizer_declared_by_a_separate_installed_app(self):
        registry = discover_extension_instances(
            "advanced_search_operand_normalizers",
            BaseOperandNormalizer,
            lambda normalizer: normalizer.datatype.datatype_name,
        )

        self.assertIn(_ThrowawayDatatype.datatype_name, registry)
        normalizer = registry[_ThrowawayDatatype.datatype_name]
        self.assertIsInstance(normalizer, ThrowawayCrossAppNormalizer)
        self.assertEqual(
            normalizer.normalize_value({"value": "irrelevant"}),
            "normalized-by-throwaway-cross-app-normalizer",
        )

    def test_raises_when_a_declared_class_is_not_the_right_base_type(self):
        self.modular_reports_config.advanced_search_operand_normalizers = [
            "tests.test_extension_discovery._ThrowawayDatatype",
        ]

        with self.assertRaises(TypeError):
            discover_extension_instances(
                "advanced_search_operand_normalizers",
                BaseOperandNormalizer,
                lambda normalizer: normalizer.datatype.datatype_name,
            )
