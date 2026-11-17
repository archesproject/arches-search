import json
import uuid
from unittest import mock

from django.contrib.auth.models import Group, User
from django.db.models import QuerySet
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import GraphModel, ResourceInstance
from arches.app.utils.permission_backend import assign_perm

from arches_resource_sets.models import ResourceSet, ResourceSetMember

from arches_search.models.models import SavedSearch

# python manage.py test tests.test_resource_sets --settings="tests.test_settings"


class SearchResultsResourceSetAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = User.objects.create_user(
            username="set_member", password="password123"
        )
        cls.other = User.objects.create_user(username="set_other", password="x")
        group = Group.objects.create(name="test_resource_set_group")
        cls.member.groups.add(group)

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug="test-resource-set", isresource=True
        )
        cls.granted = ResourceInstance.objects.create(graph=cls.graph)
        cls.restricted = ResourceInstance.objects.create(graph=cls.graph)
        assign_perm("view_resourceinstance", group, cls.granted)

    def setUp(self):
        self.client.force_login(self.member)

    def save_results(self):
        response = self.client.post(
            reverse("search_results_resource_sets"),
            json.dumps({"graph_slugs": [self.graph.slug], "name": "My set"}),
            content_type="application/json",
        )
        return response, json.loads(response.content)

    def search_within_set(self, resource_set):
        return self.client.post(
            reverse("search"),
            json.dumps(
                {
                    "graph_slugs": [self.graph.slug],
                    "resource_set_id": str(resource_set.pk),
                }
            ),
            content_type="application/json",
        )

    def test_saves_viewable_results_as_a_set_and_a_saved_search(self):
        response, saved = self.save_results()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            set(
                ResourceSetMember.objects.filter(
                    resource_set_id=saved["resource_set_id"]
                ).values_list("resource_instance_id", flat=True)
            ),
            {self.granted.pk},
        )
        self.assertEqual(
            SavedSearch.objects.get(pk=saved["saved_search_id"]).query_definition,
            {"resourceSetId": saved["resource_set_id"]},
        )

    def test_failed_save_leaves_nothing_behind(self):
        with mock.patch.object(QuerySet, "bulk_create", side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                self.save_results()

        self.assertFalse(ResourceSet.objects.exists())
        self.assertFalse(SavedSearch.objects.exists())

    def test_lists_only_sets_saved_from_search(self):
        ResourceSet.objects.create(owner=self.member, name="Made elsewhere")
        self.save_results()

        listed = self.client.get(reverse("saved_searches")).json()

        self.assertEqual([item["name"] for item in listed], ["My set"])

    def test_deleting_the_saved_search_deletes_its_set(self):
        _, saved = self.save_results()

        self.client.delete(
            reverse("saved_search", kwargs={"savedsearchid": saved["saved_search_id"]})
        )

        self.assertFalse(
            ResourceSet.objects.filter(pk=saved["resource_set_id"]).exists()
        )

    def test_deleting_a_saved_search_never_deletes_another_users_set(self):
        others_set = ResourceSet.objects.create(owner=self.other, name="Theirs")
        saved_search = SavedSearch.objects.create(
            name="Points at theirs",
            query_definition={"resourceSetId": str(others_set.pk)},
            creator=self.member,
        )

        self.client.delete(
            reverse("saved_search", kwargs={"savedsearchid": saved_search.pk})
        )

        self.assertTrue(ResourceSet.objects.filter(pk=others_set.pk).exists())

    def test_search_within_own_set_returns_only_its_members(self):
        # Viewable but not in the set, so only the set can be keeping it out.
        outside = ResourceInstance.objects.create(graph=self.graph)
        assign_perm("view_resourceinstance", self.member.groups.first(), outside)
        own_set = ResourceSet.objects.create(owner=self.member, name="Mine")
        ResourceSetMember.objects.create(
            resource_set=own_set, resource_instance=self.granted
        )

        response = self.search_within_set(own_set)

        self.assertEqual(
            [r["resourceinstanceid"] for r in response.json()["resources"]],
            [str(self.granted.pk)],
        )

    def test_cannot_search_within_another_users_set(self):
        others_set = ResourceSet.objects.create(owner=self.other, name="Theirs")

        response = self.search_within_set(others_set)

        self.assertEqual(response.status_code, 400)
