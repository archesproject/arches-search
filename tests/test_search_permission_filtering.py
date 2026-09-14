import json
import uuid

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import GraphModel, ResourceInstance, TileModel
from arches.app.utils.permission_backend import assign_perm

from arches_search.models.models import TermSearch
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.advanced_search.metadata.node_alias_metadata import (
    build_node_alias_metadata_for_payload_query,
)
from arches_search.utils.readable_nodes import ReadableNodes
from arches_search.utils.search import SearchCompiler, SearchPayload
from arches_search.utils.search.additional_data import node_values
from arches_search.utils.term_search.matching import get_related_resources_by_text
from tests.integration.utils.advanced_search.test_advanced_search import (
    AdvancedSearchSetupMixin,
    PERSON_A_ID,
    PERSON_C_ID,
    PERSON_D_ID,
)

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

    # --- SearchAPI: graph_slugs scoping (no advanced_search_query) ---

    def test_search_excludes_ungranted_resource_for_member(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("search"),
            json.dumps({"graph_slugs": [self.graph.slug]}),
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
            json.dumps({"graph_slugs": [self.graph.slug]}),
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
            json.dumps({"graph_slugs": [self.graph.slug]}),
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
            json.dumps({"graph_slugs": [self.graph.slug]}),
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
            json.dumps(
                {
                    "graph_slugs": [self.graph.slug],
                    "advanced_search_queries": [self._advanced_search_body()],
                }
            ),
            content_type="application/json",
        )

        ids = self._search_ids(response)
        with self.subTest("status code"):
            self.assertEqual(response.status_code, 200)
        with self.subTest("granted resource visible"):
            self.assertIn(str(self.granted_resource.resourceinstanceid), ids)
        with self.subTest("restricted resource hidden"):
            self.assertNotIn(str(self.restricted_resource.resourceinstanceid), ids)

    # --- SearchCompiler: pre_filter ---

    def test_pre_filter_cannot_surface_an_ungranted_resource(self):
        results = (
            SearchCompiler(
                SearchPayload(
                    graph_slugs=[self.graph.slug],
                    term_search=None,
                    advanced_search_queries=None,
                ),
                self.member,
                pre_filter=ResourceInstance.objects.filter(
                    resourceinstanceid__in=[
                        self.granted_resource.resourceinstanceid,
                        self.restricted_resource.resourceinstanceid,
                    ]
                ),
            )
            .compile()
            .results
        )

        ids = set(results.values_list("resourceinstanceid", flat=True))
        with self.subTest("granted resource visible"):
            self.assertIn(self.granted_resource.resourceinstanceid, ids)
        with self.subTest("restricted resource hidden"):
            self.assertNotIn(self.restricted_resource.resourceinstanceid, ids)

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


class NodePermissionFilteringTest(AdvancedSearchSetupMixin, TestCase):
    """
    A node in a nodegroup the user cannot read must behave exactly like a node
    that does not exist, everywhere a search touches node data.

    The restricted user is denied the nodegroups holding person first_name and
    last_name, person birth_date, and dog favorite_person. Person A's last name,
    "CHILD", is therefore unreadable to them; its nickname, "ALPHA", is not.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = User.objects.create_superuser(
            username="node_perm_admin",
            password="password123",
            email="node_perm_admin@example.com",
        )
        cls.restricted = User.objects.create_user(
            username="node_perm_restricted", password="password123"
        )
        for nodegroup in (cls.alias, cls.birth_date, cls.favorite_person):
            assign_perm("no_access_to_nodegroup", cls.restricted, nodegroup)
        # Resource permissions are not what is under test, so the restricted
        # user may see person A itself.
        assign_perm("view_resourceinstance", cls.restricted, cls.person_a)

    @staticmethod
    def _person_payload(*clauses, relationship=None, groups=()):
        return {
            "graph_slug": "person",
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": list(clauses),
            "groups": list(groups),
            "aggregations": [],
            "relationship": relationship,
        }

    @staticmethod
    def _node_clause(node_alias, operator, *operand_values):
        return {
            "type": "LITERAL",
            "quantifier": "ANY",
            "subject": {
                "type": "NODE",
                "graph_slug": "person",
                "node_alias": node_alias,
                "search_models": [],
            },
            "operator": operator,
            "operands": [
                {"type": "LITERAL", "value": operand_value}
                for operand_value in operand_values
            ],
        }

    def _compile_as(self, user, payload):
        return set(
            AdvancedSearchQueryCompiler(payload, user=user)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

    def _refusal_as(self, user, payload):
        with self.assertRaises(ValidationError) as raised:
            self._compile_as(user, payload)
        return raised.exception.messages[0]

    # --- clauses ---

    def test_a_clause_on_an_unreadable_node_is_refused_like_an_unknown_node(self):
        # HAS_NO_VALUE is the case that matters most: if an unreadable node
        # were merely treated as empty, it would match every resource.
        for operator, operand_values in (("EQUALS", ["FOO"]), ("HAS_NO_VALUE", [])):
            with self.subTest(operator=operator):
                unreadable = self._refusal_as(
                    self.restricted,
                    self._person_payload(
                        self._node_clause("first_name", operator, *operand_values)
                    ),
                )
                unknown = self._refusal_as(
                    self.admin,
                    self._person_payload(
                        self._node_clause("no_such_node", operator, *operand_values)
                    ),
                )
                self.assertEqual(
                    unreadable.replace("first_name", "<node>"),
                    unknown.replace("no_such_node", "<node>"),
                )

    def test_a_clause_on_a_readable_node_still_filters(self):
        with self.subTest("a user who can read the node"):
            self.assertEqual(
                self._compile_as(
                    self.admin,
                    self._person_payload(
                        self._node_clause("first_name", "EQUALS", "FOO")
                    ),
                ),
                {PERSON_A_ID},
            )
        with self.subTest("a restricted user, on a node left readable to them"):
            self.assertIn(
                PERSON_A_ID,
                self._compile_as(
                    self.restricted,
                    self._person_payload(
                        self._node_clause("fingernail_length", "GREATER_THAN", 0)
                    ),
                ),
            )

    def test_a_relationship_through_an_unreadable_node_is_refused(self):
        favorite_person = {
            "type": "NODE",
            "graph_slug": "dog",
            "node_alias": "favorite_person",
        }
        payload = self._person_payload(
            {
                "type": "RELATED",
                "quantifier": "ANY",
                "subject": {**favorite_person, "search_models": []},
                "operator": "HAS_ANY_VALUE",
                "operands": [],
            },
            relationship={
                "path": favorite_person,
                "is_inverse": True,
                "traversal_quantifier": "ANY",
            },
            groups=[
                {
                    "graph_slug": "dog",
                    "scope": "RESOURCE",
                    "logic": "AND",
                    "clauses": [],
                    "groups": [],
                    "aggregations": [],
                    "relationship": None,
                }
            ],
        )

        with self.subTest("refused for the restricted user"):
            self._refusal_as(self.restricted, payload)
        with self.subTest("followed for a user who can read it"):
            self.assertEqual(
                self._compile_as(self.admin, payload),
                {PERSON_A_ID, PERSON_C_ID, PERSON_D_ID},
            )

    def test_a_search_models_subject_skips_values_of_unreadable_nodes(self):
        def matches_as(user, text):
            return self._compile_as(
                user,
                self._person_payload(
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": {
                            "type": "SEARCH_MODELS",
                            "graph_slug": "person",
                            "node_alias": "",
                            "search_models": ["TermSearch"],
                        },
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": text}],
                    }
                ),
            )

        with self.subTest("an unreadable value does not match"):
            self.assertNotIn(PERSON_A_ID, matches_as(self.restricted, "CHILD"))
        with self.subTest("a readable value on the same resource does"):
            self.assertIn(PERSON_A_ID, matches_as(self.restricted, "ALPHA"))
        with self.subTest("the unreadable value matches for a user who can read it"):
            self.assertIn(PERSON_A_ID, matches_as(self.admin, "CHILD"))

    # --- term search and suggestions ---

    def test_term_search_skips_values_of_unreadable_nodes(self):
        def matches_as(user, text):
            return set(
                get_related_resources_by_text(
                    [text], self.person_graph.graphid, ReadableNodes(user), max_hops=0
                ).values_list("resourceinstanceid", flat=True)
            )

        with self.subTest("an unreadable value does not match"):
            self.assertNotIn(PERSON_A_ID, matches_as(self.restricted, "CHILD"))
        with self.subTest("a readable value on the same resource does"):
            self.assertIn(PERSON_A_ID, matches_as(self.restricted, "ALPHA"))
        with self.subTest("the unreadable value matches for a user who can read it"):
            self.assertIn(PERSON_A_ID, matches_as(self.admin, "CHILD"))

    def test_term_suggestions_skip_values_of_unreadable_nodes(self):
        def suggestions_as(user, text):
            self.client.force_login(user)
            response = self.client.get(reverse("term_suggestion_search"), {"q": text})
            return [result["text"] for result in response.json()["results"]]

        with self.subTest("an unreadable value is not suggested"):
            self.assertNotIn("CHILD", suggestions_as(self.restricted, "CHILD"))
        with self.subTest("a readable value on the same resource is"):
            self.assertIn("ALPHA", suggestions_as(self.restricted, "ALPHA"))
        with self.subTest(
            "the unreadable value is suggested to a user who can read it"
        ):
            self.assertIn("CHILD", suggestions_as(self.admin, "CHILD"))

    # --- what the search reports about nodes ---

    def test_projection_omits_an_unreadable_node(self):
        node_key = ("person", "first_name")

        self.assertNotIn(
            node_key, node_values.resolve([node_key], ReadableNodes(self.restricted))
        )
        self.assertIn(
            node_key, node_values.resolve([node_key], ReadableNodes(self.admin))
        )

    def test_node_metadata_omits_an_unreadable_node(self):
        payload = self._person_payload(self._node_clause("first_name", "EQUALS", "FOO"))
        node_key = ("person", "first_name")

        self.assertNotIn(
            node_key,
            build_node_alias_metadata_for_payload_query(
                payload, ReadableNodes(self.restricted)
            ),
        )
        self.assertIn(
            node_key,
            build_node_alias_metadata_for_payload_query(
                payload, ReadableNodes(self.admin)
            ),
        )

    def test_date_bounds_ignore_an_unreadable_date_node(self):
        def bounds_as(user):
            self.client.force_login(user)
            response = self.client.get(
                reverse("node_date_bounds_for_graph", args=[self.person_graph.graphid]),
                {"node_alias": "birth_date"},
            )
            return response.json()

        self.assertEqual(
            bounds_as(self.restricted), {"min_value": None, "max_value": None}
        )
        self.assertEqual(bounds_as(self.admin), {"min_value": 1000, "max_value": 2000})

    # --- endpoints that compile a payload ---

    def _person_search_body(self):
        return {
            "graph_slugs": ["person"],
            "advanced_search_queries": [
                self._person_payload(self._node_clause("first_name", "EQUALS", "FOO"))
            ],
        }

    def test_a_map_context_naming_an_unreadable_node_is_a_400(self):
        self.client.force_login(self.restricted)
        response = self.client.post(
            reverse("search_mvt_context"),
            json.dumps(self._person_search_body()),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_a_tile_for_a_node_its_viewer_cannot_read_is_empty(self):
        # Created by someone who can read the node, then drawn for someone who can't.
        self.client.force_login(self.admin)
        context_id = self.client.post(
            reverse("search_mvt_context"),
            json.dumps(self._person_search_body()),
            content_type="application/json",
        ).json()["context_id"]

        self.client.force_login(self.restricted)
        response = self.client.get(reverse("search_mvt", args=[context_id, 0, 0, 0]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_the_sql_view_refuses_an_unreadable_node_with_a_400(self):
        self.client.force_login(self.restricted)
        response = self.client.post(
            reverse("advanced_search_sql"),
            json.dumps(
                self._person_payload(self._node_clause("first_name", "EQUALS", "FOO"))
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    # --- cost ---

    def test_nothing_is_added_when_every_node_is_readable(self):
        readable_nodes = ReadableNodes(self.admin)
        rows = TermSearch.objects.filter(graph_slug="person")

        self.assertIs(readable_nodes.exclude_unreadable_rows(rows), rows)
        self.assertIsNot(
            ReadableNodes(self.restricted).exclude_unreadable_rows(rows), rows
        )
