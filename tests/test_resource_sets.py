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

# python manage.py test tests.test_resource_sets --settings="tests.test_settings"


class SearchResultsResourceSetAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = User.objects.create_user(
            username="set_member", password="password123"
        )
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

    def post_search(self):
        return self.client.post(
            reverse("search_results_resource_sets"),
            json.dumps({"graph_slugs": [self.graph.slug], "name": "My set"}),
            content_type="application/json",
        )

    def test_set_holds_only_resources_the_user_may_view(self):
        response = self.post_search()

        self.assertEqual(response.status_code, 201)
        resource_set_id = json.loads(response.content)["resource_set_id"]
        self.assertEqual(
            set(
                ResourceSetMember.objects.filter(
                    resource_set_id=resource_set_id
                ).values_list("resource_instance_id", flat=True)
            ),
            {self.granted.pk},
        )

    def test_failed_save_leaves_no_set_behind(self):
        # Fails adding the members, after the set itself was created.
        with mock.patch.object(QuerySet, "bulk_create", side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                self.post_search()

        self.assertFalse(ResourceSet.objects.exists())
        self.assertFalse(ResourceSetMember.objects.exists())

    def test_cannot_delete_another_users_set(self):
        other = User.objects.create_user(username="set_other", password="x")
        others_set = ResourceSet.objects.create(owner=other, name="Theirs")

        response = self.client.delete(
            reverse(
                "search_results_resource_set",
                kwargs={"resource_set_id": others_set.pk},
            )
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ResourceSet.objects.filter(pk=others_set.pk).exists())

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

    def test_search_within_own_set_returns_only_its_members(self):
        # Viewable but not in the set, so only the set can be keeping it out.
        outside = ResourceInstance.objects.create(graph=self.graph)
        assign_perm("view_resourceinstance", self.member.groups.first(), outside)
        own_set = ResourceSet.objects.create(owner=self.member, name="Mine")
        ResourceSetMember.objects.create(
            resource_set=own_set, resource_instance=self.granted
        )

        response = self.search_within_set(own_set)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [
                resource["resourceinstanceid"]
                for resource in response.json()["resources"]
            ],
            [str(self.granted.pk)],
        )

    def test_cannot_search_within_another_users_set(self):
        other = User.objects.create_user(username="set_other", password="x")
        others_set = ResourceSet.objects.create(owner=other, name="Theirs")
        ResourceSetMember.objects.create(
            resource_set=others_set, resource_instance=self.granted
        )

        response = self.search_within_set(others_set)

        self.assertEqual(response.status_code, 400)
