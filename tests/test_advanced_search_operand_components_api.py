from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

# python manage.py test tests.test_advanced_search_operand_components_api --settings="tests.test_settings"


class AdvancedSearchOperandComponentsAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="operand_components_user", password="password123"
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_lists_the_seeded_panel_components_by_datatype(self):
        response = self.client.get(reverse("advanced_search_operand_components"))

        self.assertEqual(response.status_code, 200)
        components_by_datatype = {
            entry["datatype_id"]: entry for entry in response.json()
        }
        self.assertEqual(
            set(components_by_datatype),
            {"date", "edtf", "geojson-feature-collection"},
        )
        self.assertEqual(
            components_by_datatype["date"],
            {
                "datatype_id": "date",
                "slug": "time",
                "label": "Time filter",
                "icon": "pi pi-calendar",
                "component": "arches_search/AdvancedSearch/components/OperandPanel/components/TimeOperandEditor.vue",
                "opens_in_panel": True,
                "sets_operator": True,
            },
        )
        self.assertEqual(components_by_datatype["edtf"]["slug"], "time")
        self.assertEqual(
            components_by_datatype["geojson-feature-collection"],
            {
                "datatype_id": "geojson-feature-collection",
                "slug": "map",
                "label": "Map filter",
                "icon": "pi pi-map-marker",
                "component": "arches_search/AdvancedSearch/components/OperandPanel/components/MapOperandEditor.vue",
                "opens_in_panel": True,
                "sets_operator": False,
            },
        )
