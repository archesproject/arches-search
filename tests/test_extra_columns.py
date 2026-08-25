"""Tests for the extra_columns feature (issue #213): attaching additional
node values, addressed by graph_slug + node_alias, onto paginated search
results. See arches_search/utils/extra_columns.py.

python manage.py test tests.test_extra_columns --settings="tests.test_settings"

Requires PERMISSION_FRAMEWORK to be set to
arches_default_deny.ArchesDefaultDenyPermissionFramework (see test_settings.py).

Response shape: each resource's "extra_columns" dict is scoped to that
resource's own graph and keyed by plain node_alias (no graph_slug prefix --
a resource belongs to exactly one graph, so node_alias alone is unambiguous
once scoped). A key is present (possibly as []) only when the requested node
resolves, is permitted, AND belongs to that resource's graph; otherwise the
key is simply absent -- "doesn't exist", "not permitted", and "wrong graph"
are all indistinguishable as key-absence, preserving the enumeration-oracle
guarantee without padding every resource with irrelevant keys.
"""

import json
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    ResourceXResource,
    TileModel,
)
from arches.app.utils.permission_backend import assign_perm

from arches_search.utils.extra_columns import (
    attach_extra_columns,
    resolve_node_refs,
    validate_extra_columns,
)


def _string_tile_data(node, value):
    return {str(node.nodeid): {"en": {"value": value, "direction": "ltr"}}}


class ExtraColumnsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="extra_columns_user", password="password123"
        )

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="extra-columns-test-graph",
            isresource=True,
            is_active=True,
        )

        # Single-cardinality "name" node -- permitted for the test user.
        cls.name_nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.name_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Name",
            alias="name",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.name_nodegroup,
            istopnode=True,
        )

        # Cardinality-N "language" node -- also permitted; used to confirm
        # multiple tiles for one resource are all returned, uncapped.
        cls.language_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(), cardinality="n"
        )
        cls.language_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Language",
            alias="language",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.language_nodegroup,
            istopnode=False,
        )

        # Single-cardinality "private_note" node -- deliberately NOT granted
        # read_nodegroup, to prove a resource-readable user still can't pull
        # its value through extra_columns.
        cls.restricted_nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.restricted_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Private note",
            alias="private_note",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.restricted_nodegroup,
            istopnode=False,
        )

        assign_perm("read_nodegroup", cls.user, cls.name_nodegroup)
        assign_perm("read_nodegroup", cls.user, cls.language_nodegroup)
        # A nodegroup with *zero* explicit permission records is open to
        # everyone by default under Arches' guardian-based nodegroup
        # permissions (see get_nodegroups_by_perm_for_user_or_group's
        # "if no explicit permissions, object is considered accessible by
        # all" fallback) -- restricting it for this user requires granting
        # some *other* permission (never read_nodegroup) so the permission
        # checker finds explicit-but-insufficient perms for this user,
        # rather than no perms at all. Mirrors
        # tests.test_node_filter_config_api's identical pattern.
        assign_perm("write_nodegroup", cls.user, cls.restricted_nodegroup)

        cls.resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )
        assign_perm("view_resourceinstance", cls.user, cls.resource)

        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.name_nodegroup,
            resourceinstance=cls.resource,
            data=_string_tile_data(cls.name_node, "Jane Doe"),
            provisionaledits=None,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.language_nodegroup,
            resourceinstance=cls.resource,
            data=_string_tile_data(cls.language_node, "English"),
            provisionaledits=None,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.language_nodegroup,
            resourceinstance=cls.resource,
            data=_string_tile_data(cls.language_node, "French"),
            provisionaledits=None,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.restricted_nodegroup,
            resourceinstance=cls.resource,
            data=_string_tile_data(cls.restricted_node, "sensitive value"),
            provisionaledits=None,
        )

    # --- resolve_node_refs / attach_extra_columns (direct, unit-level) ---

    def test_resolve_node_refs_omits_unpermitted_node(self):
        resolved = resolve_node_refs(
            [
                {"graph_slug": self.graph.slug, "node_alias": "name"},
                {"graph_slug": self.graph.slug, "node_alias": "private_note"},
            ],
            self.user,
        )
        self.assertIn((self.graph.slug, "name"), resolved)
        self.assertNotIn((self.graph.slug, "private_note"), resolved)

    def test_resolve_node_refs_omits_unresolved_pair(self):
        resolved = resolve_node_refs(
            [{"graph_slug": self.graph.slug, "node_alias": "does_not_exist"}],
            self.user,
        )
        self.assertEqual(resolved, {})

    def test_attach_extra_columns_returns_value_for_permitted_node(self):
        result = attach_extra_columns(
            [self.resource],
            [{"graph_slug": self.graph.slug, "node_alias": "name"}],
            self.user,
        )
        values = result[str(self.resource.pk)]["name"]
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["display_value"], "Jane Doe")

    def test_attach_extra_columns_key_absent_without_nodegroup_permission(self):
        result = attach_extra_columns(
            [self.resource],
            [{"graph_slug": self.graph.slug, "node_alias": "private_note"}],
            self.user,
        )
        self.assertNotIn("private_note", result[str(self.resource.pk)])

    def test_attach_extra_columns_unresolved_node_key_absent_not_error(self):
        result = attach_extra_columns(
            [self.resource],
            [{"graph_slug": self.graph.slug, "node_alias": "does_not_exist"}],
            self.user,
        )
        self.assertNotIn("does_not_exist", result[str(self.resource.pk)])

    def test_attach_extra_columns_returns_every_tile_uncapped(self):
        result = attach_extra_columns(
            [self.resource],
            [{"graph_slug": self.graph.slug, "node_alias": "language"}],
            self.user,
        )
        values = result[str(self.resource.pk)]["language"]
        display_values = {value["display_value"] for value in values}
        self.assertEqual(len(values), 2)
        self.assertEqual(display_values, {"English", "French"})

    def test_attach_extra_columns_absent_spec_returns_empty_dict_per_resource(self):
        result = attach_extra_columns([self.resource], None, self.user)
        self.assertEqual(result, {str(self.resource.pk): {}})

    def test_validate_extra_columns_rejects_missing_node_alias(self):
        with self.assertRaises(Exception):
            validate_extra_columns([{"graph_slug": self.graph.slug}])

    def test_validate_extra_columns_accepts_well_formed_entries(self):
        validate_extra_columns(
            [{"graph_slug": self.graph.slug, "node_alias": "name"}]
        )  # should not raise

    # --- SimpleSearchAPI (end-to-end) ---

    def setUp(self):
        self.client.force_login(self.user)

    def _post_search(self, body):
        return self.client.post(
            reverse("arches_search"),
            json.dumps(body),
            content_type="application/json",
        )

    def _resource_from_response(self, response):
        resources = response.json()["resources"]
        return next(
            r for r in resources if r["resourceinstanceid"] == str(self.resource.pk)
        )

    def test_search_response_always_includes_extra_columns_key(self):
        response = self._post_search({"graphIds": [str(self.graph.graphid)]})
        self.assertEqual(response.status_code, 200)
        resource = self._resource_from_response(response)
        self.assertEqual(resource["extra_columns"], {})

    def test_search_response_includes_permitted_extra_column_value(self):
        response = self._post_search(
            {
                "graphIds": [str(self.graph.graphid)],
                "extra_columns": [
                    {"graph_slug": self.graph.slug, "node_alias": "name"}
                ],
            }
        )
        self.assertEqual(response.status_code, 200)
        resource = self._resource_from_response(response)
        self.assertEqual(
            resource["extra_columns"]["name"][0]["display_value"], "Jane Doe"
        )

    def test_search_response_key_absent_for_restricted_extra_column(self):
        response = self._post_search(
            {
                "graphIds": [str(self.graph.graphid)],
                "extra_columns": [
                    {"graph_slug": self.graph.slug, "node_alias": "private_note"}
                ],
            }
        )
        self.assertEqual(response.status_code, 200)
        resource = self._resource_from_response(response)
        self.assertNotIn("private_note", resource["extra_columns"])

    def test_search_response_400_for_malformed_extra_columns(self):
        response = self._post_search(
            {
                "graphIds": [str(self.graph.graphid)],
                "extra_columns": [{"graph_slug": self.graph.slug}],
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_search_response_200_for_unresolved_and_unpermitted_nodes_alike(self):
        """Enumeration-oracle guard: an unresolved node and an unpermitted
        node must be indistinguishable in the response -- both absent."""
        unresolved_response = self._post_search(
            {
                "graphIds": [str(self.graph.graphid)],
                "extra_columns": [
                    {"graph_slug": self.graph.slug, "node_alias": "does_not_exist"}
                ],
            }
        )
        unpermitted_response = self._post_search(
            {
                "graphIds": [str(self.graph.graphid)],
                "extra_columns": [
                    {"graph_slug": self.graph.slug, "node_alias": "private_note"}
                ],
            }
        )
        self.assertEqual(unresolved_response.status_code, 200)
        self.assertEqual(unpermitted_response.status_code, 200)

        unresolved_resource = self._resource_from_response(unresolved_response)
        unpermitted_resource = self._resource_from_response(unpermitted_response)
        self.assertNotIn("does_not_exist", unresolved_resource["extra_columns"])
        self.assertNotIn("private_note", unpermitted_resource["extra_columns"])

    def test_search_response_returns_multiple_requested_columns_together(self):
        response = self._post_search(
            {
                "graphIds": [str(self.graph.graphid)],
                "extra_columns": [
                    {"graph_slug": self.graph.slug, "node_alias": "name"},
                    {"graph_slug": self.graph.slug, "node_alias": "language"},
                ],
            }
        )
        self.assertEqual(response.status_code, 200)
        resource = self._resource_from_response(response)
        self.assertEqual(
            resource["extra_columns"]["name"][0]["display_value"], "Jane Doe"
        )
        self.assertEqual(len(resource["extra_columns"]["language"]), 2)


class ExtraColumnsMixedGraphTest(TestCase):
    """A search-results page can span multiple graphs. A requested column
    that only applies to one of them must not error, and must not appear at
    all on resources from a graph where the node doesn't exist -- this is
    the actual bug this test class exists to pin down: person:name_content
    style keys must never show up on a non-person resource, not even as []."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="extra_columns_mixed_graph_user", password="password123"
        )

        cls.graph_a = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="extra-columns-mixed-graph-a",
            isresource=True,
            is_active=True,
        )
        cls.graph_b = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="extra-columns-mixed-graph-b",
            isresource=True,
            is_active=True,
        )

        cls.nodegroup_a = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.node_a = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Name",
            alias="name",
            datatype="string",
            graph=cls.graph_a,
            nodegroup=cls.nodegroup_a,
            istopnode=True,
        )
        assign_perm("read_nodegroup", cls.user, cls.nodegroup_a)

        cls.resource_a = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph_a
        )
        cls.resource_b = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph_b
        )
        assign_perm("view_resourceinstance", cls.user, cls.resource_a)
        assign_perm("view_resourceinstance", cls.user, cls.resource_b)

        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.nodegroup_a,
            resourceinstance=cls.resource_a,
            data=_string_tile_data(cls.node_a, "Only on graph A"),
            provisionaledits=None,
        )

    def test_attach_extra_columns_key_absent_for_non_matching_graph(self):
        result = attach_extra_columns(
            [self.resource_a, self.resource_b],
            [{"graph_slug": self.graph_a.slug, "node_alias": "name"}],
            self.user,
        )
        self.assertEqual(
            result[str(self.resource_a.pk)]["name"][0]["display_value"],
            "Only on graph A",
        )
        self.assertNotIn("name", result[str(self.resource_b.pk)])

    def test_search_response_key_absent_for_non_matching_graph_resource(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("arches_search"),
            json.dumps(
                {
                    "graphIds": [str(self.graph_a.graphid), str(self.graph_b.graphid)],
                    "extra_columns": [
                        {"graph_slug": self.graph_a.slug, "node_alias": "name"}
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        resources = {r["resourceinstanceid"]: r for r in response.json()["resources"]}
        resource_a = resources[str(self.resource_a.pk)]
        resource_b = resources[str(self.resource_b.pk)]

        self.assertEqual(
            resource_a["extra_columns"]["name"][0]["display_value"],
            "Only on graph A",
        )
        self.assertNotIn("name", resource_b["extra_columns"])


class ExtraColumnsAdvancedSearchAPITest(TestCase):
    """Same feature, exercised through AdvancedSearchAPI end-to-end, since
    it has a meaningfully different queryset-construction path than
    SimpleSearchAPI."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="extra_columns_advanced_user", password="password123"
        )

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="extra-columns-advanced-search-graph",
            isresource=True,
            is_active=True,
        )
        cls.nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Name",
            alias="name",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
        )
        assign_perm("read_nodegroup", cls.user, cls.nodegroup)

        cls.resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )
        assign_perm("view_resourceinstance", cls.user, cls.resource)

        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.nodegroup,
            resourceinstance=cls.resource,
            data=_string_tile_data(cls.node, "Jane Doe"),
            provisionaledits=None,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _advanced_search_body(self, extra_columns=None):
        body = {
            "graph_slug": self.graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }
        if extra_columns is not None:
            body["extra_columns"] = extra_columns
        return body

    def test_advanced_search_response_includes_extra_column_value(self):
        response = self.client.post(
            reverse("advanced_search"),
            json.dumps(
                self._advanced_search_body(
                    extra_columns=[
                        {"graph_slug": self.graph.slug, "node_alias": "name"}
                    ]
                )
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        resources = response.json()["resources"]
        resource = next(
            r for r in resources if r["resourceinstanceid"] == str(self.resource.pk)
        )
        self.assertEqual(
            resource["extra_columns"]["name"][0]["display_value"], "Jane Doe"
        )

    def test_advanced_search_response_400_for_malformed_extra_columns(self):
        response = self.client.post(
            reverse("advanced_search"),
            json.dumps(
                self._advanced_search_body(extra_columns=[{"node_alias": "name"}])
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class ExtraColumnsResourceInstanceLeakTest(TestCase):
    """A resource-instance column must not leak the related resource's name
    to a caller who can't read that related resource -- neither via
    `details` nor via `display_value` (ResourceInstanceDataType.get_details
    is what feeds both, independently, so both must be redacted) nor via the
    raw `node_value`."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="extra_columns_ri_user", password="password123"
        )

        cls.target_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="extra-columns-ri-target-graph",
            isresource=True,
            is_active=True,
        )
        cls.readable_target = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.target_graph,
            name="Readable Target",
            descriptors={
                "en": {"name": "Readable Target", "description": "", "map_popup": ""}
            },
        )
        cls.unreadable_target = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.target_graph,
            name="Secret Target",
            descriptors={
                "en": {"name": "Secret Target", "description": "", "map_popup": ""}
            },
        )
        assign_perm("view_resourceinstance", cls.user, cls.readable_target)
        # Deliberately no view_resourceinstance grant for unreadable_target.

        cls.source_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="extra-columns-ri-source-graph",
            isresource=True,
            is_active=True,
        )
        cls.nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.ri_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Related",
            alias="related",
            datatype="resource-instance-list",
            graph=cls.source_graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
        )
        assign_perm("read_nodegroup", cls.user, cls.nodegroup)

        cls.source_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.source_graph
        )
        assign_perm("view_resourceinstance", cls.user, cls.source_resource)

        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.nodegroup,
            resourceinstance=cls.source_resource,
            data={
                str(cls.ri_node.nodeid): [
                    {
                        "resourceId": str(cls.readable_target.pk),
                        "ontologyProperty": "",
                        "inverseOntologyProperty": "",
                        "resourceXresourceId": str(uuid.uuid4()),
                    },
                    {
                        "resourceId": str(cls.unreadable_target.pk),
                        "ontologyProperty": "",
                        "inverseOntologyProperty": "",
                        "resourceXresourceId": str(uuid.uuid4()),
                    },
                ]
            },
            provisionaledits=None,
        )
        # ResourceInstanceDataType.get_related_resources resolves display
        # names via actual ResourceXResource rows, not just the tile's
        # stored resourceId values -- without these, get_details() can't
        # resolve either target and both come back as "Missing".
        ResourceXResource.objects.create(
            from_resource=cls.source_resource, to_resource=cls.readable_target
        )
        ResourceXResource.objects.create(
            from_resource=cls.source_resource, to_resource=cls.unreadable_target
        )

    def test_unreadable_related_resource_is_dropped_from_details(self):
        result = attach_extra_columns(
            [self.source_resource],
            [{"graph_slug": self.source_graph.slug, "node_alias": "related"}],
            self.user,
        )
        values = result[str(self.source_resource.pk)]["related"]
        self.assertEqual(len(values), 1)

        detail_resource_ids = {d["resource_id"] for d in values[0]["details"]}
        self.assertIn(str(self.readable_target.pk), detail_resource_ids)
        self.assertNotIn(str(self.unreadable_target.pk), detail_resource_ids)

    def test_unreadable_related_resource_name_is_not_in_display_value(self):
        result = attach_extra_columns(
            [self.source_resource],
            [{"graph_slug": self.source_graph.slug, "node_alias": "related"}],
            self.user,
        )
        display_value = result[str(self.source_resource.pk)]["related"][0][
            "display_value"
        ]

        self.assertIn("Readable Target", display_value)
        self.assertNotIn("Secret Target", display_value)

    def test_unreadable_related_resource_id_is_not_in_node_value(self):
        result = attach_extra_columns(
            [self.source_resource],
            [{"graph_slug": self.source_graph.slug, "node_alias": "related"}],
            self.user,
        )
        node_value = result[str(self.source_resource.pk)]["related"][0]["node_value"]
        node_value_resource_ids = {v["resourceId"] for v in node_value}

        self.assertIn(str(self.readable_target.pk), node_value_resource_ids)
        self.assertNotIn(str(self.unreadable_target.pk), node_value_resource_ids)


class ExtraColumnsScalarDatatypesTest(TestCase):
    """Quick sanity sweep across a few single-table scalar datatypes to
    catch datatype-specific crashes (e.g. DateDataType.get_display_value
    reads node.config["dateFormat"] directly)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="extra_columns_scalar_user", password="password123"
        )
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="extra-columns-scalar-graph",
            isresource=True,
            is_active=True,
        )
        cls.nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.date_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Date",
            alias="a_date",
            datatype="date",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
            config={"dateFormat": "YYYY-MM-DD"},
        )
        cls.number_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Number",
            alias="a_number",
            datatype="number",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        cls.boolean_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Boolean",
            alias="a_boolean",
            datatype="boolean",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
            config={"trueLabel": "Yes", "falseLabel": "No"},
        )
        assign_perm("read_nodegroup", cls.user, cls.nodegroup)

        cls.resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )
        assign_perm("view_resourceinstance", cls.user, cls.resource)

        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.nodegroup,
            resourceinstance=cls.resource,
            data={
                str(cls.date_node.nodeid): "2024-03-15",
                str(cls.number_node.nodeid): 42,
                str(cls.boolean_node.nodeid): True,
            },
            provisionaledits=None,
        )

    def test_date_number_boolean_columns_do_not_crash(self):
        result = attach_extra_columns(
            [self.resource],
            [
                {"graph_slug": self.graph.slug, "node_alias": "a_date"},
                {"graph_slug": self.graph.slug, "node_alias": "a_number"},
                {"graph_slug": self.graph.slug, "node_alias": "a_boolean"},
            ],
            self.user,
        )
        columns = result[str(self.resource.pk)]
        self.assertEqual(columns["a_date"][0]["node_value"], "2024-03-15")
        self.assertEqual(columns["a_number"][0]["node_value"], 42)
        self.assertEqual(columns["a_boolean"][0]["node_value"], True)


class ExtraColumnsColumnFailureIsolationTest(TestCase):
    """A single node whose datatype implementation raises (here: a real,
    reproduced case -- DateDataType.get_display_value raises an uncaught
    KeyError when node.config lacks "dateFormat", which a hand-created or
    otherwise incompletely-configured node can hit) must not take down
    every other requested column, or the whole search response. This is
    distinct from a permission/resolution failure: the node did resolve and
    does belong to this resource's graph, so its key is still present, just
    empty -- the fetch itself is what failed."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="extra_columns_isolation_user", password="password123"
        )
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="extra-columns-isolation-graph",
            isresource=True,
            is_active=True,
        )
        cls.nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.broken_date_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Broken Date",
            alias="broken_date",
            datatype="date",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
            config={},  # missing "dateFormat" -- triggers an uncaught KeyError
        )
        cls.name_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Name",
            alias="name",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        assign_perm("read_nodegroup", cls.user, cls.nodegroup)

        cls.resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )
        assign_perm("view_resourceinstance", cls.user, cls.resource)

        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.nodegroup,
            resourceinstance=cls.resource,
            data={
                str(cls.broken_date_node.nodeid): "2024-03-15",
                str(cls.name_node.nodeid): {
                    "en": {"value": "Jane Doe", "direction": "ltr"}
                },
            },
            provisionaledits=None,
        )

    def test_broken_column_returns_empty_without_affecting_others(self):
        result = attach_extra_columns(
            [self.resource],
            [
                {"graph_slug": self.graph.slug, "node_alias": "broken_date"},
                {"graph_slug": self.graph.slug, "node_alias": "name"},
            ],
            self.user,
        )
        columns = result[str(self.resource.pk)]
        self.assertEqual(columns["broken_date"], [])
        self.assertEqual(columns["name"][0]["display_value"], "Jane Doe")
