"""
Tests for arches_search.utils.search_sort.SortResolver.

Covers:
  - Validation of sort spec payloads (no DB required).
  - Ordering behavior of SortResolver.apply() against a ResourceInstance
    queryset, including the always-on resourceinstanceid tie-break.
"""

import uuid

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.utils import translation

from arches.app.models.models import GraphModel, ResourceInstance

from arches_search.utils.search_sort import (
    DEFAULT_SORT,
    DIRECTION_ASC,
    DIRECTION_DESC,
    SORT_TYPE_PRIMARY_NAME,
    SortResolver,
)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class SortResolverValidationTests(SimpleTestCase):
    def test_none_uses_default_sort(self):
        resolver = SortResolver(None)
        self.assertEqual(resolver.sort_specs, DEFAULT_SORT)

    def test_omitted_argument_uses_default_sort(self):
        resolver = SortResolver()
        self.assertEqual(resolver.sort_specs, DEFAULT_SORT)

    def test_empty_list_is_valid(self):
        resolver = SortResolver([])
        self.assertEqual(resolver.sort_specs, [])

    def test_non_list_raises(self):
        with self.assertRaises(ValidationError):
            SortResolver("primary_name")

    def test_non_dict_spec_raises(self):
        with self.assertRaises(ValidationError):
            SortResolver(["primary_name"])

    def test_missing_type_raises(self):
        with self.assertRaises(ValidationError):
            SortResolver([{"direction": DIRECTION_ASC}])

    def test_unknown_type_raises(self):
        with self.assertRaises(ValidationError):
            SortResolver([{"type": "not_a_real_sort", "direction": DIRECTION_ASC}])

    def test_invalid_direction_raises(self):
        with self.assertRaises(ValidationError):
            SortResolver([{"type": SORT_TYPE_PRIMARY_NAME, "direction": "sideways"}])

    def test_omitted_direction_defaults_to_asc(self):
        resolver = SortResolver([{"type": SORT_TYPE_PRIMARY_NAME}])
        self.assertEqual(resolver.sort_specs, [{"type": SORT_TYPE_PRIMARY_NAME}])


# ---------------------------------------------------------------------------
# Apply (integration with a real queryset)
# ---------------------------------------------------------------------------


class SortResolverApplyTests(TestCase):
    """
    Builds a small set of ResourceInstance rows whose `descriptors` JSON field
    holds {language: {"name": ...}} entries and asserts the ordering produced
    by SortResolver.apply().
    """

    @classmethod
    def setUpTestData(cls):
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="test-search-sort",
            isresource=True,
        )

        # Pre-chosen UUIDs let us assert the id tie-break deterministically.
        cls.id_apple = uuid.UUID("00000000-0000-0000-0000-000000000001")
        cls.id_banana = uuid.UUID("00000000-0000-0000-0000-000000000002")
        cls.id_cherry = uuid.UUID("00000000-0000-0000-0000-000000000003")
        cls.id_no_descriptor = uuid.UUID("00000000-0000-0000-0000-000000000004")

        cls.apple = ResourceInstance.objects.create(
            resourceinstanceid=cls.id_apple,
            graph=cls.graph,
            descriptors={
                "en": {"name": "apple"},
                "fr": {"name": "zeste"},
            },
        )
        # Mixed-case to verify case-insensitive ordering.
        cls.banana = ResourceInstance.objects.create(
            resourceinstanceid=cls.id_banana,
            graph=cls.graph,
            descriptors={
                "en": {"name": "Banana"},
                "fr": {"name": "abricot"},
            },
        )
        cls.cherry = ResourceInstance.objects.create(
            resourceinstanceid=cls.id_cherry,
            graph=cls.graph,
            descriptors={
                "en": {"name": "cherry"},
                "fr": {"name": "myrtille"},
            },
        )
        # Missing descriptors entry exercises the null-name path.
        cls.no_descriptor = ResourceInstance.objects.create(
            resourceinstanceid=cls.id_no_descriptor,
            graph=cls.graph,
            descriptors=None,
        )

    def _ordered_ids(self, sort_specs):
        queryset = ResourceInstance.objects.filter(graph=self.graph)
        ordered = SortResolver(sort_specs).apply(queryset)
        return [row.resourceinstanceid for row in ordered]

    def test_empty_sort_specs_orders_by_resourceinstanceid(self):
        ordered_ids = self._ordered_ids([])
        self.assertEqual(
            ordered_ids,
            [
                self.id_apple,
                self.id_banana,
                self.id_cherry,
                self.id_no_descriptor,
            ],
        )

    def test_primary_name_asc_is_case_insensitive(self):
        with translation.override("en"):
            ordered_ids = self._ordered_ids(
                [{"type": SORT_TYPE_PRIMARY_NAME, "direction": DIRECTION_ASC}]
            )

        # Postgres orders nulls last in asc; "Banana" sorts after "apple"
        # because Lower() folds case.
        named_ids = [i for i in ordered_ids if i != self.id_no_descriptor]
        self.assertEqual(
            named_ids,
            [self.id_apple, self.id_banana, self.id_cherry],
        )
        self.assertIn(self.id_no_descriptor, ordered_ids)

    def test_primary_name_desc_reverses_named_rows(self):
        with translation.override("en"):
            ordered_ids = self._ordered_ids(
                [{"type": SORT_TYPE_PRIMARY_NAME, "direction": DIRECTION_DESC}]
            )

        named_ids = [i for i in ordered_ids if i != self.id_no_descriptor]
        self.assertEqual(
            named_ids,
            [self.id_cherry, self.id_banana, self.id_apple],
        )

    def test_primary_name_respects_active_language(self):
        with translation.override("fr"):
            ordered_ids = self._ordered_ids(
                [{"type": SORT_TYPE_PRIMARY_NAME, "direction": DIRECTION_ASC}]
            )

        # French names: abricot, myrtille, zeste → banana, cherry, apple.
        named_ids = [i for i in ordered_ids if i != self.id_no_descriptor]
        self.assertEqual(
            named_ids,
            [self.id_banana, self.id_cherry, self.id_apple],
        )

    def test_id_tiebreak_when_primary_names_match(self):
        # Two extra rows that share a primary name; the id tie-break must
        # order them deterministically by resourceinstanceid asc.
        id_dup_a = uuid.UUID("00000000-0000-0000-0000-0000000000aa")
        id_dup_b = uuid.UUID("00000000-0000-0000-0000-0000000000bb")
        ResourceInstance.objects.create(
            resourceinstanceid=id_dup_a,
            graph=self.graph,
            descriptors={"en": {"name": "duplicate"}},
        )
        ResourceInstance.objects.create(
            resourceinstanceid=id_dup_b,
            graph=self.graph,
            descriptors={"en": {"name": "duplicate"}},
        )

        with translation.override("en"):
            ordered_ids = self._ordered_ids(
                [{"type": SORT_TYPE_PRIMARY_NAME, "direction": DIRECTION_ASC}]
            )

        dup_positions = [i for i in ordered_ids if i in (id_dup_a, id_dup_b)]
        self.assertEqual(dup_positions, [id_dup_a, id_dup_b])
