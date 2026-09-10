import json
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import GraphModel, ResourceInstance
from arches.app.utils.permission_backend import assign_perm

# python manage.py test tests.test_search_definition_counts --settings="tests.test_settings"


class SearchDefinitionCountsAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="search_definition_counts_user", password="password123"
        )

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="search-definition-counts-test-graph",
            isresource=True,
            is_active=True,
        )

        cls.visible_resource_one = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )
        cls.visible_resource_two = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )
        assign_perm("view_resourceinstance", cls.user, cls.visible_resource_one)
        assign_perm("view_resourceinstance", cls.user, cls.visible_resource_two)

    def setUp(self):
        self.client.force_login(self.user)

    def _post_counts(self, items):
        return self.client.post(
            reverse("search_definition_counts"),
            json.dumps({"items": items}),
            content_type="application/json",
        )

    def test_returns_count_for_a_single_item(self):
        response = self._post_counts(
            [{"id": "card-1", "body": {"graphIds": [str(self.graph.graphid)]}}]
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"counts": {"card-1": 2}})

    def test_returns_counts_for_multiple_items_independently(self):
        response = self._post_counts(
            [
                {"id": "card-1", "body": {"graphIds": [str(self.graph.graphid)]}},
                {"id": "card-2", "body": {"graphIds": []}},
            ]
        )

        self.assertEqual(response.status_code, 200)
        counts = response.json()["counts"]
        self.assertEqual(counts["card-1"], 2)
        self.assertEqual(counts["card-2"], 2)

    def test_empty_items_returns_empty_counts(self):
        response = self._post_counts([])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"counts": {}})

    def test_malformed_item_falls_back_to_none_and_other_items_still_succeed(self):
        response = self._post_counts(
            [
                {"id": "malformed", "body": {"graphIds": "not-a-list"}},
                {"id": "good", "body": {"graphIds": [str(self.graph.graphid)]}},
            ]
        )

        self.assertEqual(response.status_code, 200)
        counts = response.json()["counts"]
        self.assertIsNone(counts["malformed"])
        self.assertEqual(counts["good"], 2)
