import json
import uuid

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from arches_search.models.models import (
    SavedSearch,
    SharedSearchXGroup,
    SharedSearchXUser,
)

# python manage.py test tests.test_saved_search_api --settings="tests.test_settings"

SAMPLE_QUERY = {"groups": [{"op": "and", "clauses": []}]}


class SavedSearchAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username="alice", password="password123")
        cls.bob = User.objects.create_user(username="bob", password="password123")
        cls.carol = User.objects.create_user(username="carol", password="password123")

        cls.shared_group = Group.objects.create(name="test_shared_group")
        cls.alice.groups.add(cls.shared_group)
        cls.bob.groups.add(cls.shared_group)
        # carol is NOT in shared_group

    def _post_search(
        self, name, query_definition=None, description="", users=None, groups=None
    ):
        body = {
            "name": name,
            "description": description,
            "query_definition": query_definition or SAMPLE_QUERY,
        }
        if users is not None:
            body["users"] = users
        if groups is not None:
            body["groups"] = groups
        return self.client.post(
            reverse("saved_searches"),
            json.dumps(body),
            content_type="application/json",
        )

    # --- GET: scope=mine ---

    def test_get_mine_returns_only_own_searches(self):
        SavedSearch.objects.create(
            name="Alice Search", query_definition=SAMPLE_QUERY, creator=self.alice
        )
        SavedSearch.objects.create(
            name="Bob Search", query_definition=SAMPLE_QUERY, creator=self.bob
        )

        self.client.force_login(self.alice)
        response = self.client.get(reverse("saved_searches"), {"scope": "mine"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Alice Search")

    def test_get_mine_returns_full_query_definition(self):
        SavedSearch.objects.create(
            name="Alice Search", query_definition=SAMPLE_QUERY, creator=self.alice
        )

        self.client.force_login(self.alice)
        response = self.client.get(reverse("saved_searches"), {"scope": "mine"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["query_definition"], SAMPLE_QUERY)

    def test_get_mine_includes_creator_info(self):
        SavedSearch.objects.create(
            name="Alice Search", query_definition=SAMPLE_QUERY, creator=self.alice
        )

        self.client.force_login(self.alice)
        response = self.client.get(reverse("saved_searches"), {"scope": "mine"})

        data = response.json()
        self.assertEqual(data[0]["creator"]["username"], "alice")

    def test_get_mine_returns_empty_when_no_searches(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse("saved_searches"), {"scope": "mine"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_defaults_to_mine_scope(self):
        SavedSearch.objects.create(
            name="Alice Search", query_definition=SAMPLE_QUERY, creator=self.alice
        )
        SavedSearch.objects.create(
            name="Bob Search", query_definition=SAMPLE_QUERY, creator=self.bob
        )

        self.client.force_login(self.alice)
        response = self.client.get(reverse("saved_searches"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    # --- GET: scope=shared ---

    def test_get_shared_via_user(self):
        search = SavedSearch.objects.create(
            name="Shared with Bob", query_definition=SAMPLE_QUERY, creator=self.alice
        )
        SharedSearchXUser.objects.create(saved_search=search, user=self.bob)

        self.client.force_login(self.bob)
        response = self.client.get(reverse("saved_searches"), {"scope": "shared"})

        self.assertEqual(response.status_code, 200)
        names = [s["name"] for s in response.json()]
        self.assertIn("Shared with Bob", names)

    def test_get_shared_via_group(self):
        search = SavedSearch.objects.create(
            name="Group Shared", query_definition=SAMPLE_QUERY, creator=self.alice
        )
        SharedSearchXGroup.objects.create(saved_search=search, group=self.shared_group)

        self.client.force_login(self.bob)
        response = self.client.get(reverse("saved_searches"), {"scope": "shared"})

        self.assertEqual(response.status_code, 200)
        names = [s["name"] for s in response.json()]
        self.assertIn("Group Shared", names)

    def test_get_shared_excludes_own_searches(self):
        search = SavedSearch.objects.create(
            name="Alice's Own", query_definition=SAMPLE_QUERY, creator=self.alice
        )
        SharedSearchXGroup.objects.create(saved_search=search, group=self.shared_group)

        self.client.force_login(self.alice)
        response = self.client.get(reverse("saved_searches"), {"scope": "shared"})

        names = [s["name"] for s in response.json()]
        self.assertNotIn("Alice's Own", names)

    def test_get_shared_not_visible_to_unshared_user(self):
        search = SavedSearch.objects.create(
            name="Group Shared", query_definition=SAMPLE_QUERY, creator=self.alice
        )
        SharedSearchXGroup.objects.create(saved_search=search, group=self.shared_group)

        # carol is not in shared_group
        self.client.force_login(self.carol)
        response = self.client.get(reverse("saved_searches"), {"scope": "shared"})

        names = [s["name"] for s in response.json()]
        self.assertNotIn("Group Shared", names)

    def test_get_shared_deduplicates_when_shared_via_both_user_and_group(self):
        search = SavedSearch.objects.create(
            name="Doubly Shared", query_definition=SAMPLE_QUERY, creator=self.alice
        )
        SharedSearchXUser.objects.create(saved_search=search, user=self.bob)
        SharedSearchXGroup.objects.create(saved_search=search, group=self.shared_group)

        self.client.force_login(self.bob)
        response = self.client.get(reverse("saved_searches"), {"scope": "shared"})

        names = [s["name"] for s in response.json()]
        self.assertEqual(names.count("Doubly Shared"), 1)

    # --- GET: search filter ---

    def test_search_filter_matches_name(self):
        SavedSearch.objects.create(
            name="Minerals", query_definition=SAMPLE_QUERY, creator=self.alice
        )
        SavedSearch.objects.create(
            name="Sulfides", query_definition=SAMPLE_QUERY, creator=self.alice
        )

        self.client.force_login(self.alice)
        response = self.client.get(
            reverse("saved_searches"), {"scope": "mine", "search": "Mineral"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Minerals")

    def test_search_filter_matches_description(self):
        SavedSearch.objects.create(
            name="Test",
            description="find sulfide minerals",
            query_definition=SAMPLE_QUERY,
            creator=self.alice,
        )
        SavedSearch.objects.create(
            name="Other",
            description="something else",
            query_definition=SAMPLE_QUERY,
            creator=self.alice,
        )

        self.client.force_login(self.alice)
        response = self.client.get(
            reverse("saved_searches"), {"scope": "mine", "search": "sulfide"}
        )

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Test")

    def test_search_filter_is_case_insensitive(self):
        SavedSearch.objects.create(
            name="Van Gogh Samples", query_definition=SAMPLE_QUERY, creator=self.alice
        )

        self.client.force_login(self.alice)
        response = self.client.get(
            reverse("saved_searches"), {"scope": "mine", "search": "van gogh"}
        )

        self.assertEqual(len(response.json()), 1)

    # --- POST ---

    def test_post_creates_search(self):
        self.client.force_login(self.alice)
        response = self._post_search("New Search")

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "New Search")
        self.assertIn("savedsearchid", data)
        self.assertIn("created_at", data)
        self.assertEqual(data["creator"]["username"], "alice")
        self.assertTrue(
            SavedSearch.objects.filter(name="New Search", creator=self.alice).exists()
        )

    def test_post_with_sharing_creates_user_and_group_links(self):
        self.client.force_login(self.alice)
        response = self._post_search(
            "Shared Search",
            users=[self.bob.pk],
            groups=[self.shared_group.pk],
        )

        self.assertEqual(response.status_code, 201)
        savedsearchid = response.json()["savedsearchid"]
        self.assertTrue(
            SharedSearchXUser.objects.filter(
                saved_search_id=savedsearchid, user=self.bob
            ).exists()
        )
        self.assertTrue(
            SharedSearchXGroup.objects.filter(
                saved_search_id=savedsearchid, group=self.shared_group
            ).exists()
        )

    def test_post_missing_name_returns_400(self):
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse("saved_searches"),
            json.dumps({"query_definition": SAMPLE_QUERY}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_post_blank_name_returns_400(self):
        self.client.force_login(self.alice)
        response = self._post_search("   ")
        self.assertEqual(response.status_code, 400)

    def test_post_missing_query_definition_returns_400(self):
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse("saved_searches"),
            json.dumps({"name": "No Query"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    # --- DELETE ---

    def test_delete_by_creator_succeeds(self):
        search = SavedSearch.objects.create(
            name="To Delete", query_definition=SAMPLE_QUERY, creator=self.alice
        )

        self.client.force_login(self.alice)
        response = self.client.delete(
            reverse("saved_search", kwargs={"savedsearchid": search.savedsearchid})
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(SavedSearch.objects.filter(pk=search.savedsearchid).exists())

    def test_delete_also_removes_sharing_records(self):
        search = SavedSearch.objects.create(
            name="To Delete", query_definition=SAMPLE_QUERY, creator=self.alice
        )
        SharedSearchXUser.objects.create(saved_search=search, user=self.bob)
        SharedSearchXGroup.objects.create(saved_search=search, group=self.shared_group)

        self.client.force_login(self.alice)
        self.client.delete(
            reverse("saved_search", kwargs={"savedsearchid": search.savedsearchid})
        )

        self.assertFalse(
            SharedSearchXUser.objects.filter(
                saved_search_id=search.savedsearchid
            ).exists()
        )
        self.assertFalse(
            SharedSearchXGroup.objects.filter(
                saved_search_id=search.savedsearchid
            ).exists()
        )

    def test_delete_by_non_creator_returns_404(self):
        search = SavedSearch.objects.create(
            name="Alice's Search", query_definition=SAMPLE_QUERY, creator=self.alice
        )

        self.client.force_login(self.bob)
        response = self.client.delete(
            reverse("saved_search", kwargs={"savedsearchid": search.savedsearchid})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(SavedSearch.objects.filter(pk=search.savedsearchid).exists())

    def test_delete_nonexistent_returns_404(self):
        self.client.force_login(self.alice)
        response = self.client.delete(
            reverse("saved_search", kwargs={"savedsearchid": uuid.uuid4()})
        )
        self.assertEqual(response.status_code, 404)
