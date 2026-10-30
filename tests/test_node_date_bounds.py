import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import ResourceInstance, TileModel
from arches_search.models.models import DateRangeSearch, DateSearch
from tests.integration.utils.advanced_search.test_advanced_search import (
    AdvancedSearchSetupMixin,
)

# python manage.py test tests.test_node_date_bounds --settings="tests.test_settings"

UNKNOWN_YEAR_EARLIEST = 112
UNKNOWN_YEAR_LATEST = 99991212


class NodeDateBoundsTest(AdvancedSearchSetupMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = User.objects.create_superuser(
            username="date_bounds_admin",
            password="password123",
            email="date_bounds_admin@example.com",
        )

        person_with_unknown_year = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.person_graph
        )
        unknown_year_birth_date_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.birth_date,
            resourceinstance=person_with_unknown_year,
            data={},
            provisionaledits=None,
        )
        unknown_year_birth_date_tile.save()
        for sortable_date in (UNKNOWN_YEAR_EARLIEST, UNKNOWN_YEAR_LATEST):
            DateSearch.objects.create(
                tileid=unknown_year_birth_date_tile,
                resourceinstanceid=person_with_unknown_year,
                graph_slug="person",
                node_alias="birth_date",
                datatype="date",
                value=sortable_date,
            )
        DateRangeSearch.objects.create(
            tileid=cls.person_b_availability_window_tile,
            resourceinstanceid=cls.person_b,
            graph_slug="person",
            node_alias="availability_window",
            datatype="edtf",
            start_value=UNKNOWN_YEAR_EARLIEST,
            end_value=UNKNOWN_YEAR_LATEST,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def _bounds(self, node_alias):
        response = self.client.get(
            reverse("node_date_bounds_for_graph", args=[self.person_graph.graphid]),
            {"node_alias": node_alias},
        )
        return response.json()

    def test_an_unknown_year_leaves_a_date_field_on_its_real_dates(self):
        self.assertEqual(
            self._bounds("birth_date"), {"min_value": 1000, "max_value": 2000}
        )

    def test_an_unknown_year_leaves_a_date_range_field_on_its_real_dates(self):
        self.assertEqual(
            self._bounds("availability_window"),
            {"min_value": 500, "max_value": 2200},
        )
