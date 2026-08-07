import json
import uuid

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import GraphModel, ResourceInstance, TileModel
from arches.app.utils.permission_backend import assign_perm

from arches_search.models.models import TermSearch

# python manage.py test tests.test_search_permission_filtering --settings="tests.test_settings"
#
# Requires PERMISSION_FRAMEWORK to be set to
# arches_default_deny.ArchesDefaultDenyPermissionFramework (see settings.py).


class SearchPermissionFilteringTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="perm_admin",
            password="password123",
            email="perm_admin@example.com",
        )
        cls.member = User.objects.create_user(
            username="perm_member", password="password123"
        )
        cls.outsider = User.objects.create_user(
            username="perm_outsider", password="password123"
        )

        cls.group = Group.objects.create(name="test_search_permission_group")
        cls.member.groups.add(cls.group)

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="test-search-permission",
            isresource=True,
        )

        cls.granted_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )
        cls.granted_resource.save()

        cls.restricted_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )
        cls.restricted_resource.save()

        cls.owned_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
            principaluser=cls.outsider,
        )
        cls.owned_resource.save()

        assign_perm("view_resourceinstance", cls.group, cls.granted_resource)

        granted_tile = TileModel.objects.create(resourceinstance=cls.granted_resource)
        TermSearch.objects.create(
            tileid=granted_tile,
            resourceinstanceid=cls.granted_resource,
            graph_slug=cls.graph.slug,
            node_alias="name",
            language="en",
            datatype="string",
            value="alderaan expedition",
        )

        restricted_tile = TileModel.objects.create(
            resourceinstance=cls.restricted_resource
        )
        TermSearch.objects.create(
            tileid=restricted_tile,
            resourceinstanceid=cls.restricted_resource,
            graph_slug=cls.graph.slug,
            node_alias="name",
            language="en",
            datatype="string",
            value="alderaan archives",
        )

    def _search_ids(self, response):
        return {
            resource["resourceinstanceid"]
            for resource in response.json()["resources"]
        }

    # --- SimpleSearchAPI ---

    def test_simple_search_excludes_ungranted_resource_for_member(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("arches_search"),
            json.dumps({"graphId": str(self.graph.graphid)}),
            content_type="application/json",
        )

        ids = self._search_ids(response)
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("granted resource visible"):
            self.assertIn(str(self.granted_resource.resourceinstanceid), ids)
        with self.subTest("restricted resource hidden"):
            self.assertNotIn(str(self.restricted_resource.resourceinstanceid), ids)

    def test_simple_search_excludes_all_resources_for_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse("arches_search"),
            json.dumps({"graphId": str(self.graph.graphid)}),
            content_type="application/json",
        )

        ids = self._search_ids(response)
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("granted resource hidden"):
            self.assertNotIn(str(self.granted_resource.resourceinstanceid), ids)
        with self.subTest("restricted resource hidden"):
            self.assertNotIn(str(self.restricted_resource.resourceinstanceid), ids)

    def test_simple_search_owner_sees_owned_resource(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse("arches_search"),
            json.dumps({"graphId": str(self.graph.graphid)}),
            content_type="application/json",
        )

        ids = self._search_ids(response)
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("owned resource visible"):
            self.assertIn(str(self.owned_resource.resourceinstanceid), ids)

    def test_simple_search_superuser_sees_all_resources(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("arches_search"),
            json.dumps({"graphId": str(self.graph.graphid)}),
            content_type="application/json",
        )

        ids = self._search_ids(response)
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("granted resource visible"):
            self.assertIn(str(self.granted_resource.resourceinstanceid), ids)
        with self.subTest("restricted resource visible"):
            self.assertIn(str(self.restricted_resource.resourceinstanceid), ids)
        with self.subTest("owned resource visible"):
            self.assertIn(str(self.owned_resource.resourceinstanceid), ids)

    # --- AdvancedSearchAPI ---

    def _advanced_search_body(self):
        return {
            "graph_slug": self.graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

    def test_advanced_search_excludes_ungranted_resource_for_member(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("advanced_search"),
            json.dumps(self._advanced_search_body()),
            content_type="application/json",
        )

        ids = self._search_ids(response)
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("granted resource visible"):
            self.assertIn(str(self.granted_resource.resourceinstanceid), ids)
        with self.subTest("restricted resource hidden"):
            self.assertNotIn(str(self.restricted_resource.resourceinstanceid), ids)

    # --- TermSuggestionView ---

    def test_term_suggestions_excludes_terms_from_ungranted_resource(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("term_suggestion_search"), {"q": "alderaan"})

        values = [result["text"] for result in response.json()["results"]]
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("granted term visible"):
            self.assertIn("alderaan expedition", values)
        with self.subTest("restricted term hidden"):
            self.assertNotIn("alderaan archives", values)

    def test_term_suggestions_superuser_sees_all_terms(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("term_suggestion_search"), {"q": "alderaan"})

        values = [result["text"] for result in response.json()["results"]]
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("granted term visible"):
            self.assertIn("alderaan expedition", values)
        with self.subTest("restricted term visible"):
            self.assertIn("alderaan archives", values)
