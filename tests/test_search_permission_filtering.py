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
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
            descriptors={"en": {"name": "Granted Resource"}},
        )
        cls.granted_resource.save()

        cls.restricted_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
            descriptors={"en": {"name": "Restricted Resource"}},
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
            resource["resourceinstanceid"] for resource in response.json()["resources"]
        }

    # --- SearchAPI: graph_ids scoping (no advanced_search_query) ---

    def test_search_excludes_ungranted_resource_for_member(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("search"),
            json.dumps({"graph_ids": [str(self.graph.graphid)]}),
            content_type="application/json",
        )

        ids = self._search_ids(response)
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("granted resource visible"):
            self.assertIn(str(self.granted_resource.resourceinstanceid), ids)
        with self.subTest("restricted resource hidden"):
            self.assertNotIn(str(self.restricted_resource.resourceinstanceid), ids)

    def test_search_excludes_all_resources_for_outsider(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse("search"),
            json.dumps({"graph_ids": [str(self.graph.graphid)]}),
            content_type="application/json",
        )

        ids = self._search_ids(response)
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("granted resource hidden"):
            self.assertNotIn(str(self.granted_resource.resourceinstanceid), ids)
        with self.subTest("restricted resource hidden"):
            self.assertNotIn(str(self.restricted_resource.resourceinstanceid), ids)

    def test_search_owner_sees_owned_resource(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse("search"),
            json.dumps({"graph_ids": [str(self.graph.graphid)]}),
            content_type="application/json",
        )

        ids = self._search_ids(response)
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("owned resource visible"):
            self.assertIn(str(self.owned_resource.resourceinstanceid), ids)

    def test_search_superuser_sees_all_resources(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("search"),
            json.dumps({"graph_ids": [str(self.graph.graphid)]}),
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

    # --- SearchAPI: advanced_search_query ---

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

    def test_search_with_advanced_search_query_excludes_ungranted_resource_for_member(
        self,
    ):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("search"),
            json.dumps({"advanced_search_query": self._advanced_search_body()}),
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

    # --- ResourceNamesForPayloadAPI ---

    def _resource_names_payload(self):
        return {
            "clauses": [
                {
                    "operands": [
                        {
                            "type": "LITERAL",
                            "value": [
                                {
                                    "resourceId": str(
                                        self.granted_resource.resourceinstanceid
                                    )
                                },
                                {
                                    "resourceId": str(
                                        self.restricted_resource.resourceinstanceid
                                    )
                                },
                            ],
                        }
                    ],
                }
            ],
            "groups": [],
        }

    def test_resource_names_for_payload_excludes_ungranted_resource_for_member(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("resource_names_for_payload"),
            json.dumps(self._resource_names_payload()),
            content_type="application/json",
        )

        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        names_by_id = response.json()
        with self.subTest("granted resource name visible"):
            self.assertIn(str(self.granted_resource.resourceinstanceid), names_by_id)
        with self.subTest("restricted resource name hidden"):
            self.assertNotIn(
                str(self.restricted_resource.resourceinstanceid), names_by_id
            )

    # --- AdvancedSearchSQLAPI ---

    def test_advanced_search_sql_applies_permission_filter_for_member(self):
        """Member and superuser SQL for the same query must differ: the superuser's compiled queryset is unfiltered, the member's gains a permission-scoping subquery. Before this fix the two were identical regardless of who asked."""
        body = self._advanced_search_body()

        self.client.force_login(self.member)
        member_response = self.client.post(
            reverse("advanced_search_sql"),
            json.dumps(body),
            content_type="application/json",
        )

        self.client.force_login(self.admin)
        admin_response = self.client.post(
            reverse("advanced_search_sql"),
            json.dumps(body),
            content_type="application/json",
        )

        with self.subTest("status codes"):
            self.assertEqual(member_response.status_code, 200)
            self.assertEqual(admin_response.status_code, 200)
        with self.subTest("member SQL is permission-scoped"):
            self.assertNotEqual(
                member_response.json()["sql"], admin_response.json()["sql"]
            )

    def test_resource_names_for_payload_superuser_sees_all_names(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("resource_names_for_payload"),
            json.dumps(self._resource_names_payload()),
            content_type="application/json",
        )

        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        names_by_id = response.json()
        with self.subTest("granted resource name visible"):
            self.assertIn(str(self.granted_resource.resourceinstanceid), names_by_id)
        with self.subTest("restricted resource name visible"):
            self.assertIn(str(self.restricted_resource.resourceinstanceid), names_by_id)
