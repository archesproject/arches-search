"""
Tests for projecting node (tile) values onto search results, and for sorting by
one of those values.

python manage.py test tests.test_additional_data --settings="tests.test_settings"
"""

import json
import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    ResourceInstanceLifecycle,
    ResourceInstanceLifecycleState,
    TileModel,
)

from arches_search.utils.search.additional_data import (
    node_values,
    validate_additional_data,
)
from arches_search.utils.search.additional_data.node_values import (
    annotation_name_for,
)
from arches_search.utils.search.sorting import (
    DIRECTION_ASC,
    DIRECTION_DESC,
    SORT_TYPE_NODE,
    SortResolver,
)


class AdditionalDataValidationTests(SimpleTestCase):
    def test_none_is_allowed(self):
        validate_additional_data(None)

    def test_non_list_raises(self):
        with self.assertRaises(ValidationError):
            validate_additional_data(
                {"type": "NODE", "graph_slug": "g", "node_alias": "n"}
            )

    def test_entry_must_be_object(self):
        with self.assertRaises(ValidationError):
            validate_additional_data(["not-an-object"])

    def test_missing_keys_raise(self):
        with self.assertRaises(ValidationError):
            validate_additional_data([{"graph_slug": "g"}])
        with self.assertRaises(ValidationError):
            validate_additional_data([{"node_alias": "n"}])

    def test_valid_entry_passes(self):
        validate_additional_data(
            [{"type": "NODE", "graph_slug": "g", "node_alias": "n"}]
        )

    def test_node_keys_dedupe_and_preserve_order(self):
        keys = node_values.keys(
            [
                {"type": "NODE", "graph_slug": "g", "node_alias": "b"},
                {"type": "NODE", "graph_slug": "g", "node_alias": "a"},
                {"type": "NODE", "graph_slug": "g", "node_alias": "b"},
            ]
        )
        self.assertEqual(keys, [("g", "b"), ("g", "a")])

    def test_annotation_name_is_deterministic_and_unambiguous(self):
        self.assertEqual(
            annotation_name_for("g", "alias"), annotation_name_for("g", "alias")
        )
        # ("a", "b_c") and ("a_b", "c") must not collide.
        self.assertNotEqual(
            annotation_name_for("a", "b_c"), annotation_name_for("a_b", "c")
        )


class AdditionalDataDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="xc_admin", password="pw", email="xc_admin@example.com"
        )

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug="test-extra-columns", isresource=True
        )
        cls.nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(), parentnodegroup=None
        )
        cls.grouping_node = Node.objects.create(
            nodeid=cls.nodegroup.nodegroupid,
            name="info",
            alias="info",
            datatype="semantic",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        cls.title_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Title",
            alias="title",
            datatype="non-localized-string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )

        cls.resource_beta = cls._make_resource("beta")
        cls.resource_alpha = cls._make_resource("alpha")
        cls.resource_without_value = ResourceInstance(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )
        cls.resource_without_value.save()

    @classmethod
    def _make_resource(cls, title):
        resource = ResourceInstance(resourceinstanceid=uuid.uuid4(), graph=cls.graph)
        resource.save()
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            resourceinstance=resource,
            nodegroup=cls.nodegroup,
            data={str(cls.title_node.pk): title},
        )
        return resource

    def _annotated(self):
        keys = [(self.graph.slug, "title")]
        nodes_by_key = node_values.resolve(keys, self.admin)
        queryset, annotation_names = node_values.annotate(
            ResourceInstance.objects.filter(graph=self.graph), nodes_by_key
        )
        return nodes_by_key, queryset, annotation_names

    def test_resolves_and_annotates_node_value(self):
        nodes_by_key, queryset, annotation_names = self._annotated()
        self.assertIn((self.graph.slug, "title"), nodes_by_key)

        annotation = annotation_names[(self.graph.slug, "title")]
        values = {
            str(resource.pk): getattr(resource, annotation) for resource in queryset
        }
        self.assertEqual(values[str(self.resource_alpha.pk)], "alpha")
        self.assertEqual(values[str(self.resource_beta.pk)], "beta")
        self.assertIsNone(values[str(self.resource_without_value.pk)])

    def test_formats_values_as_a_list_of_representations(self):
        nodes_by_key, queryset, annotation_names = self._annotated()
        formatted = node_values.format_values(
            list(queryset), nodes_by_key, annotation_names
        )

        alpha = formatted[str(self.resource_alpha.pk)]["title"]
        self.assertEqual(len(alpha), 1)
        self.assertEqual(alpha[0]["node_value"], "alpha")
        self.assertEqual(alpha[0]["display_value"], "alpha")
        self.assertIn("details", alpha[0])

        # A resource with no tile still gets the key, with no values.
        self.assertEqual(formatted[str(self.resource_without_value.pk)]["title"], [])

    def test_unresolvable_node_is_silently_absent(self):
        nodes_by_key = node_values.resolve(
            [(self.graph.slug, "no_such_alias")], self.admin
        )
        self.assertEqual(nodes_by_key, {})

    def test_sort_by_node_value(self):
        nodes_by_key, queryset, annotation_names = self._annotated()

        ascending = list(
            SortResolver(
                [
                    {
                        "type": SORT_TYPE_NODE,
                        "graph_slug": self.graph.slug,
                        "node_alias": "title",
                        "direction": DIRECTION_ASC,
                    }
                ]
            )
            .apply(queryset, node_column_annotations=annotation_names)
            .values_list("resourceinstanceid", flat=True)
        )
        self.assertEqual(ascending[0], self.resource_alpha.pk)
        self.assertEqual(ascending[1], self.resource_beta.pk)
        # The valueless resource sorts last regardless of direction.
        self.assertEqual(ascending[-1], self.resource_without_value.pk)

        descending = list(
            SortResolver(
                [
                    {
                        "type": SORT_TYPE_NODE,
                        "graph_slug": self.graph.slug,
                        "node_alias": "title",
                        "direction": DIRECTION_DESC,
                    }
                ]
            )
            .apply(queryset, node_column_annotations=annotation_names)
            .values_list("resourceinstanceid", flat=True)
        )
        self.assertEqual(descending[0], self.resource_beta.pk)
        self.assertEqual(descending[-1], self.resource_without_value.pk)

    def test_sort_on_unresolved_column_is_skipped_not_an_error(self):
        queryset = ResourceInstance.objects.filter(graph=self.graph)
        ordered = SortResolver(
            [
                {
                    "type": SORT_TYPE_NODE,
                    "graph_slug": self.graph.slug,
                    "node_alias": "title",
                    "direction": DIRECTION_ASC,
                }
            ]
        ).apply(queryset, node_column_annotations={})
        self.assertEqual(ordered.count(), 3)

    def test_sort_requires_graph_slug_and_node_alias(self):
        with self.assertRaises(ValidationError):
            SortResolver([{"type": SORT_TYPE_NODE, "direction": DIRECTION_ASC}])


class AdditionalDataAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="xc_api_admin", password="pw", email="xc_api@example.com"
        )
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug="test-extra-columns-api", isresource=True
        )
        cls.nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(), parentnodegroup=None
        )
        Node.objects.create(
            nodeid=cls.nodegroup.nodegroupid,
            name="info",
            alias="info",
            datatype="semantic",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        cls.title_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Title",
            alias="title",
            datatype="non-localized-string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        lifecycle = ResourceInstanceLifecycle.objects.create(name="api lifecycle")
        cls.lifecycle_state = ResourceInstanceLifecycleState.objects.create(
            name="Draft",
            action_label="Draft",
            is_initial_state=True,
            resource_instance_lifecycle=lifecycle,
        )
        cls.resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
            principaluser=cls.admin,
            resource_instance_lifecycle_state=cls.lifecycle_state,
        )
        cls.resource.save()
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            resourceinstance=cls.resource,
            nodegroup=cls.nodegroup,
            data={str(cls.title_node.pk): "a projected value"},
        )

    def _search(self, body):
        return self.client.post(
            reverse("search"), json.dumps(body), content_type="application/json"
        )

    def test_additional_data_are_returned_on_each_resource(self):
        self.client.force_login(self.admin)
        response = self._search(
            {
                "graph_slugs": [self.graph.slug],
                "additional_data": [
                    {
                        "type": "NODE",
                        "graph_slug": self.graph.slug,
                        "node_alias": "title",
                    }
                ],
            }
        )
        self.assertEqual(response.status_code, 200)
        resources = response.json()["resources"]
        matching = [
            resource
            for resource in resources
            if resource["resourceinstanceid"] == str(self.resource.resourceinstanceid)
        ]
        self.assertEqual(len(matching), 1)
        title = matching[0]["additional_data"]["node_values"]["title"]
        self.assertEqual(title[0]["display_value"], "a projected value")

    def _additional_data_for(self, entries):
        self.client.force_login(self.admin)
        response = self._search(
            {"graph_slugs": [self.graph.slug], "additional_data": entries}
        )
        self.assertEqual(response.status_code, 200)
        row = next(
            resource
            for resource in response.json()["resources"]
            if resource["resourceinstanceid"] == str(self.resource.pk)
        )
        return row["additional_data"]

    # --- RESOURCE_FIELD entries ---

    def test_a_foreign_key_field_carries_its_label(self):
        """
        The whole point of projecting a resource field: the row already has the
        id, and a reader needs the name.
        """
        additional_data = self._additional_data_for(
            [
                {
                    "type": "RESOURCE_FIELD",
                    "field": "resource_instance_lifecycle_state",
                }
            ]
        )
        state = additional_data["resource_fields"]["resource_instance_lifecycle_state"]

        self.assertEqual(state["value"], str(self.lifecycle_state.pk))
        self.assertEqual(state["label"], "Draft")

    def test_a_field_with_no_label_still_has_the_key(self):
        additional_data = self._additional_data_for(
            [{"type": "RESOURCE_FIELD", "field": "createdtime"}]
        )
        created = additional_data["resource_fields"]["createdtime"]

        self.assertIsNotNone(created["value"])
        self.assertIsNone(created["label"])

    def test_a_field_reached_through_a_relation(self):
        """principaluser__username is a join, so it cannot be read off the row."""
        additional_data = self._additional_data_for(
            [{"type": "RESOURCE_FIELD", "field": "principaluser__username"}]
        )

        self.assertEqual(
            additional_data["resource_fields"]["principaluser__username"]["value"],
            "xc_api_admin",
        )

    def test_both_kinds_in_one_request_are_kept_apart(self):
        additional_data = self._additional_data_for(
            [
                {
                    "type": "NODE",
                    "graph_slug": self.graph.slug,
                    "node_alias": "title",
                },
                {"type": "RESOURCE_FIELD", "field": "principaluser"},
            ]
        )

        self.assertEqual(
            additional_data["node_values"]["title"][0]["display_value"],
            "a projected value",
        )
        self.assertEqual(
            additional_data["resource_fields"]["principaluser"]["label"],
            "xc_api_admin",
        )

    def test_an_unqueryable_field_is_a_400(self):
        # Unlike a node, which is silently omitted -- the registry is public, so
        # naming a bad field is a client bug worth reporting.
        self.client.force_login(self.admin)
        response = self._search(
            {
                "graph_slugs": [self.graph.slug],
                "additional_data": [
                    {"type": "RESOURCE_FIELD", "field": "principaluser__password"}
                ],
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_malformed_additional_data_is_a_400(self):
        self.client.force_login(self.admin)
        response = self._search(
            {
                "graph_slugs": [self.graph.slug],
                # missing type
                "additional_data": [{"graph_slug": self.graph.slug}],
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_sort_by_node_value_end_to_end(self):
        self.client.force_login(self.admin)
        response = self._search(
            {
                "graph_slugs": [self.graph.slug],
                "sort": [
                    {
                        "type": SORT_TYPE_NODE,
                        "graph_slug": self.graph.slug,
                        "node_alias": "title",
                        "direction": DIRECTION_ASC,
                    }
                ],
            }
        )
        self.assertEqual(response.status_code, 200)
