"""Tests for the extra_columns feature (issue #213). See
arches_search/utils/extra_columns.py.

python manage.py test tests.test_extra_columns --settings="tests.test_settings"

Response shape: each resource's "extra_columns" dict is scoped to that
resource's own graph, keyed by plain node_alias. A key is present (as a
possibly-empty list) only when the node resolves, is permitted, and belongs
to that resource's graph; otherwise it's absent -- "doesn't exist", "not
permitted", and "wrong graph" are all indistinguishable as key-absence.
"""

import json
import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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
    validate_extra_columns,
)


def _make_nodegroup_and_node(graph, alias, datatype, *, cardinality="1", config=None):
    nodegroup = NodeGroup.objects.create(
        nodegroupid=uuid.uuid4(), cardinality=cardinality
    )
    node = Node.objects.create(
        nodeid=uuid.uuid4(),
        name=alias,
        alias=alias,
        datatype=datatype,
        graph=graph,
        nodegroup=nodegroup,
        istopnode=True,
        config=config or {},
    )
    return nodegroup, node


def _add_sibling_node(graph, nodegroup, alias, datatype, *, config=None):
    return Node.objects.create(
        nodeid=uuid.uuid4(),
        name=alias,
        alias=alias,
        datatype=datatype,
        graph=graph,
        nodegroup=nodegroup,
        istopnode=False,
        config=config or {},
    )


def _tile(nodegroup, resource, data):
    return TileModel.objects.create(
        tileid=uuid.uuid4(),
        nodegroup=nodegroup,
        resourceinstance=resource,
        data=data,
        provisionaledits=None,
    )


def _string_value(node, value):
    return {str(node.nodeid): {"en": {"value": value, "direction": "ltr"}}}


def _related_resource_link(target):
    return {
        "resourceId": str(target.pk),
        "ontologyProperty": "",
        "inverseOntologyProperty": "",
        "resourceXresourceId": str(uuid.uuid4()),
    }


class ExtraColumnsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="extra_columns_user", password="password123"
        )

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="extra-columns-graph",
            isresource=True,
            is_active=True,
        )
        cls.other_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="extra-columns-other-graph",
            isresource=True,
            is_active=True,
        )

        cls.name_nodegroup, cls.name_node = _make_nodegroup_and_node(
            cls.graph, "name", "string"
        )
        cls.language_nodegroup, cls.language_node = _make_nodegroup_and_node(
            cls.graph, "language", "string", cardinality="n"
        )
        # Deliberately restricted below via a conflicting (non-read) permission --
        # a nodegroup with zero explicit permission records defaults OPEN to
        # everyone, so omitting a grant wouldn't actually restrict it.
        cls.private_nodegroup, cls.private_node = _make_nodegroup_and_node(
            cls.graph, "private_note", "string"
        )
        cls.related_nodegroup, cls.related_node = _make_nodegroup_and_node(
            cls.graph, "related", "resource-instance-list"
        )
        # No "dateFormat" configured -- DateDataType.get_display_value raises
        # an uncaught KeyError, exercising per-column failure isolation.
        cls.broken_nodegroup, cls.broken_node = _make_nodegroup_and_node(
            cls.graph, "broken_date", "date"
        )
        cls.scalar_nodegroup, cls.date_node = _make_nodegroup_and_node(
            cls.graph, "a_date", "date", config={"dateFormat": "YYYY-MM-DD"}
        )
        cls.number_node = _add_sibling_node(
            cls.graph, cls.scalar_nodegroup, "a_number", "number"
        )
        cls.boolean_node = _add_sibling_node(
            cls.graph,
            cls.scalar_nodegroup,
            "a_boolean",
            "boolean",
            config={"trueLabel": "Yes", "falseLabel": "No"},
        )

        for nodegroup in (
            cls.name_nodegroup,
            cls.language_nodegroup,
            cls.related_nodegroup,
            cls.broken_nodegroup,
            cls.scalar_nodegroup,
        ):
            assign_perm("read_nodegroup", cls.user, nodegroup)
        assign_perm("write_nodegroup", cls.user, cls.private_nodegroup)

        cls.resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )
        cls.other_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.other_graph
        )
        cls.readable_target = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.other_graph,
            descriptors={
                "en": {"name": "Readable Target", "description": "", "map_popup": ""}
            },
        )
        cls.unreadable_target = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.other_graph,
            descriptors={
                "en": {"name": "Secret Target", "description": "", "map_popup": ""}
            },
        )
        for resource in (cls.resource, cls.other_resource, cls.readable_target):
            assign_perm("view_resourceinstance", cls.user, resource)
        # unreadable_target deliberately has no view_resourceinstance grant.

        _tile(
            cls.name_nodegroup, cls.resource, _string_value(cls.name_node, "Jane Doe")
        )
        _tile(
            cls.language_nodegroup,
            cls.resource,
            _string_value(cls.language_node, "English"),
        )
        _tile(
            cls.language_nodegroup,
            cls.resource,
            _string_value(cls.language_node, "French"),
        )
        _tile(
            cls.private_nodegroup,
            cls.resource,
            _string_value(cls.private_node, "sensitive value"),
        )
        _tile(
            cls.broken_nodegroup,
            cls.resource,
            {str(cls.broken_node.nodeid): "2024-03-15"},
        )
        _tile(
            cls.scalar_nodegroup,
            cls.resource,
            {
                str(cls.date_node.nodeid): "2024-03-15",
                str(cls.number_node.nodeid): 42,
                str(cls.boolean_node.nodeid): True,
            },
        )
        _tile(
            cls.related_nodegroup,
            cls.resource,
            {
                str(cls.related_node.nodeid): [
                    _related_resource_link(cls.readable_target),
                    _related_resource_link(cls.unreadable_target),
                ]
            },
        )
        # get_related_resources resolves display names via actual
        # ResourceXResource rows, not just the tile's resourceId values.
        ResourceXResource.objects.create(
            from_resource=cls.resource, to_resource=cls.readable_target
        )
        ResourceXResource.objects.create(
            from_resource=cls.resource, to_resource=cls.unreadable_target
        )

    def setUp(self):
        self.client.force_login(self.user)

    # --- attach_extra_columns() / validate_extra_columns() (unit) ---

    def test_permitted_node_returns_value(self):
        result = attach_extra_columns(
            [self.resource],
            [{"graph_slug": self.graph.slug, "node_alias": "name"}],
            self.user,
        )
        self.assertEqual(
            result[str(self.resource.pk)]["name"][0]["display_value"], "Jane Doe"
        )

    def test_restricted_nodegroup_key_absent(self):
        result = attach_extra_columns(
            [self.resource],
            [{"graph_slug": self.graph.slug, "node_alias": "private_note"}],
            self.user,
        )
        self.assertNotIn("private_note", result[str(self.resource.pk)])

    def test_unresolved_node_key_absent(self):
        result = attach_extra_columns(
            [self.resource],
            [{"graph_slug": self.graph.slug, "node_alias": "does_not_exist"}],
            self.user,
        )
        self.assertNotIn("does_not_exist", result[str(self.resource.pk)])

    def test_cardinality_n_returns_every_tile_uncapped(self):
        result = attach_extra_columns(
            [self.resource],
            [{"graph_slug": self.graph.slug, "node_alias": "language"}],
            self.user,
        )
        values = result[str(self.resource.pk)]["language"]
        self.assertEqual({v["display_value"] for v in values}, {"English", "French"})

    def test_no_spec_returns_empty_dict(self):
        self.assertEqual(
            attach_extra_columns([self.resource], None, self.user),
            {str(self.resource.pk): {}},
        )

    def test_column_absent_for_resource_on_different_graph(self):
        result = attach_extra_columns(
            [self.resource, self.other_resource],
            [{"graph_slug": self.graph.slug, "node_alias": "name"}],
            self.user,
        )
        self.assertEqual(
            result[str(self.resource.pk)]["name"][0]["display_value"], "Jane Doe"
        )
        self.assertNotIn("name", result[str(self.other_resource.pk)])

    def test_related_resource_permission_redacts_details_display_value_and_node_value(
        self,
    ):
        result = attach_extra_columns(
            [self.resource],
            [{"graph_slug": self.graph.slug, "node_alias": "related"}],
            self.user,
        )
        value = result[str(self.resource.pk)]["related"][0]
        readable_id, unreadable_id = str(self.readable_target.pk), str(
            self.unreadable_target.pk
        )

        detail_ids = {d["resource_id"] for d in value["details"]}
        self.assertIn(readable_id, detail_ids)
        self.assertNotIn(unreadable_id, detail_ids)

        self.assertIn("Readable Target", value["display_value"])
        self.assertNotIn("Secret Target", value["display_value"])

        node_value_ids = {v["resourceId"] for v in value["node_value"]}
        self.assertIn(readable_id, node_value_ids)
        self.assertNotIn(unreadable_id, node_value_ids)

    def test_scalar_datatypes_do_not_crash(self):
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

    def test_broken_column_isolated_from_others(self):
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

    def test_validate_rejects_malformed_entry(self):
        with self.assertRaises(ValidationError):
            validate_extra_columns([{"graph_slug": self.graph.slug}])

    # --- SimpleSearchAPI / AdvancedSearchAPI (end-to-end wiring) ---

    def _post_simple_search(self, extra_columns=None, graph=None):
        body = {"graphIds": [str((graph or self.graph).graphid)]}
        if extra_columns is not None:
            body["extra_columns"] = extra_columns
        return self.client.post(
            reverse("arches_search"), json.dumps(body), content_type="application/json"
        )

    def _resource_from_response(self, response, resource=None):
        target = str((resource or self.resource).pk)
        return next(
            r for r in response.json()["resources"] if r["resourceinstanceid"] == target
        )

    def test_simple_search_always_includes_extra_columns_key(self):
        response = self._post_simple_search()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._resource_from_response(response)["extra_columns"], {})

    def test_simple_search_returns_permitted_value(self):
        response = self._post_simple_search(
            extra_columns=[{"graph_slug": self.graph.slug, "node_alias": "name"}]
        )
        self.assertEqual(response.status_code, 200)
        resource = self._resource_from_response(response)
        self.assertEqual(
            resource["extra_columns"]["name"][0]["display_value"], "Jane Doe"
        )

    def test_simple_search_400_for_malformed_spec(self):
        response = self._post_simple_search(
            extra_columns=[{"graph_slug": self.graph.slug}]
        )
        self.assertEqual(response.status_code, 400)

    def test_simple_search_unresolved_and_unpermitted_are_indistinguishable(self):
        """Enumeration-oracle guard: an unresolved node and an unpermitted node
        must look identical in the response -- both simply absent."""
        unresolved = self._resource_from_response(
            self._post_simple_search(
                extra_columns=[
                    {"graph_slug": self.graph.slug, "node_alias": "does_not_exist"}
                ]
            )
        )
        unpermitted = self._resource_from_response(
            self._post_simple_search(
                extra_columns=[
                    {"graph_slug": self.graph.slug, "node_alias": "private_note"}
                ]
            )
        )
        self.assertNotIn("does_not_exist", unresolved["extra_columns"])
        self.assertNotIn("private_note", unpermitted["extra_columns"])

    def test_advanced_search_returns_permitted_value(self):
        body = {
            "graph_slug": self.graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [],
            "groups": [],
            "aggregations": [],
            "relationship": None,
            "extra_columns": [{"graph_slug": self.graph.slug, "node_alias": "name"}],
        }
        response = self.client.post(
            reverse("advanced_search"),
            json.dumps(body),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        resource = self._resource_from_response(response)
        self.assertEqual(
            resource["extra_columns"]["name"][0]["display_value"], "Jane Doe"
        )
