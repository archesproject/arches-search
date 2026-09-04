"""
Tests for the resource-field capability itself: which fields are queryable, and
sorting and grouping search results by them.

The RESOURCE_FIELD clause subject that filters on these fields is an advanced
search concern and is tested with the other subject types, in
tests/integration/utils/advanced_search/test_resource_field_subject.py.

Covers:
  - Registry discovery: which fields are exposed is derived from the model, and
    sensitive related-model columns are unreachable by construction.
  - resource_field sorting (label ordering, nulls last) and grouping.
  - The HTTP surface, end to end.

python manage.py test tests.test_resource_field_search --settings="tests.test_settings"
"""

import json
import uuid

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import (
    GraphModel,
    ResourceInstance,
    ResourceInstanceLifecycle,
    ResourceInstanceLifecycleState,
)

from arches_search.utils.resource_field_search.field_registry import (
    get_resource_instance_fields,
)
from arches_search.utils.resource_field_search.grouping import (
    GROUP_BY_TYPE_RESOURCE_FIELD,
    resolve_group_by_path,
)
from arches_search.utils.search.aggregation import build_aggregations
from arches_search.utils.search.sorting import (
    DIRECTION_ASC,
    DIRECTION_DESC,
    SORT_TYPE_RESOURCE_FIELD,
    SortResolver,
)


# Named for readability only: production never branches on these, they are
# seeded as AdvancedSearchFacet rows.
OPERATOR_EQUALS = "EQUALS"
OPERATOR_IN = "IN"
OPERATOR_CONTAINS = "CONTAINS"
OPERATOR_STARTS_WITH = "STARTS_WITH"
OPERATOR_RANGE = "RANGE"
OPERATOR_BEFORE = "BEFORE"
OPERATOR_AFTER = "AFTER"
OPERATOR_HAS_ANY_VALUE = "HAS_ANY_VALUE"
OPERATOR_HAS_NO_VALUE = "HAS_NO_VALUE"
OPERATOR_IS_CURRENT_USER = "IS_CURRENT_USER"
OPERATOR_IS_NOT_CURRENT_USER = "IS_NOT_CURRENT_USER"


def resource_field_clause(field, operator, *operand_values):
    """A LITERAL clause whose subject is a column on the resource row."""
    return {
        "type": "LITERAL",
        "quantifier": "ANY",
        "subject": {"type": "RESOURCE_FIELD", "field": field},
        "operator": operator,
        "operands": [
            {"type": "LITERAL", "value": operand_value}
            for operand_value in operand_values
        ],
    }


def advanced_search_query(graph_slug, *clauses, logic="AND"):
    return {
        "graph_slug": graph_slug,
        "scope": "RESOURCE",
        "logic": logic,
        "clauses": list(clauses),
        "groups": [],
        "aggregations": [],
        "relationship": None,
    }


class ResourceInstanceFieldRegistryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.registry = get_resource_instance_fields()

    def test_discovers_scalar_and_relation_fields(self):
        for expected in [
            "createdtime",
            "legacyid",
            "graph",
            "principaluser",
            "resource_instance_lifecycle_state",
        ]:
            self.assertIsNotNone(
                self.registry.get(expected), f"{expected} should be queryable"
            )

    def test_i18n_text_fields_are_queryable(self):
        """name is an I18n_TextField; it is searched in the active language."""
        descriptor = self.registry.get("name")

        self.assertIsNotNone(descriptor)
        self.assertIn(OPERATOR_CONTAINS, descriptor.operators)

    def test_untyped_json_fields_are_not_exposed(self):
        """descriptors is a bare JSONField with no facet rows, so it never appears."""
        self.assertIsNone(self.registry.get("descriptors"))

    def test_unreachable_paths_are_not_registered(self):
        """Only a field's own name and its one label hop are ever registered."""
        for probe in ("principaluser__password", "principaluser__groups__permissions"):
            with self.subTest(probe=probe):
                self.assertIsNone(self.registry.get(probe))

    def test_user_relation_exposes_username_hop_and_identity_operators(self):
        principaluser = self.registry.get("principaluser")
        self.assertTrue(principaluser.is_user_relation)
        self.assertIn(OPERATOR_IS_CURRENT_USER, principaluser.operators)
        self.assertIn(OPERATOR_IS_NOT_CURRENT_USER, principaluser.operators)
        self.assertIsNotNone(self.registry.get("principaluser__username"))

    def test_identity_operators_only_on_user_relations(self):
        lifecycle_state = self.registry.get("resource_instance_lifecycle_state")
        self.assertNotIn(OPERATOR_IS_CURRENT_USER, lifecycle_state.operators)

    def test_operators_follow_field_class(self):
        self.assertIn(OPERATOR_CONTAINS, self.registry.get("legacyid").operators)
        # A foreign key compares by key, so a substring operator is meaningless.
        self.assertNotIn(
            OPERATOR_CONTAINS, self.registry.get("principaluser").operators
        )

    def test_only_bounded_cardinality_fields_are_groupable(self):
        groupable = {field.name for field in self.registry.all() if field.is_groupable}
        self.assertIn("resource_instance_lifecycle_state", groupable)
        self.assertIn("principaluser", groupable)
        self.assertNotIn("createdtime", groupable)
        self.assertNotIn("resourceinstanceid", groupable)


class ResourceFieldFixtureMixin:
    """
    Two users, a group, and four resources on one graph: two owned by `owner`
    (one draft, one submitted), one owned by `other`, and one with no creator
    recorded -- the case a naive "created by me" filter would wrongly match.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(username="rf_owner", password="pw")
        cls.other = User.objects.create_user(username="rf_other", password="pw")
        cls.member = User.objects.create_user(username="rf_member", password="pw")
        cls.group = Group.objects.create(name="test_resource_field_group")
        cls.member.groups.add(cls.group)

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug="test-resource-field", isresource=True
        )

        lifecycle = ResourceInstanceLifecycle.objects.create(name="rf lifecycle")
        # Ids ordered against the labels on purpose: with random uuid4s a
        # label-order test passes or fails on chance.
        cls.state_draft = ResourceInstanceLifecycleState.objects.create(
            pk=uuid.UUID("ffffffff-0000-0000-0000-00000000000d"),
            name="Draft",
            action_label="Draft",
            is_initial_state=True,
            resource_instance_lifecycle=lifecycle,
        )
        cls.state_submitted = ResourceInstanceLifecycleState.objects.create(
            pk=uuid.UUID("00000000-0000-0000-0000-00000000005b"),
            name="Submitted",
            action_label="Submit",
            resource_instance_lifecycle=lifecycle,
        )

        cls.owned_draft = cls._make_resource(
            cls.graph, cls.owner, cls.state_draft, "owned draft"
        )
        cls.owned_submitted = cls._make_resource(
            cls.graph, cls.owner, cls.state_submitted, "owned submitted"
        )
        cls.other_draft = cls._make_resource(
            cls.graph, cls.other, cls.state_draft, "other draft"
        )
        # No creator recorded — the case a naive "created by me" filter would
        # wrongly match for an anonymous request.
        cls.unowned = cls._make_resource(cls.graph, None, cls.state_draft, "unowned")

    @staticmethod
    def _make_resource(graph, principaluser, lifecycle_state, label):
        resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=graph,
            principaluser=principaluser,
            resource_instance_lifecycle_state=lifecycle_state,
            descriptors={"en": {"name": label}},
        )
        resource.save()
        return resource


class ResourceFieldSortingAndGroupingTests(ResourceFieldFixtureMixin, TestCase):
    def _sorted_ids(self, sort_specs):
        queryset = ResourceInstance.objects.filter(graph=self.graph)
        return list(
            SortResolver(sort_specs)
            .apply(queryset)
            .values_list("resourceinstanceid", flat=True)
        )

    def test_sort_by_lifecycle_state_orders_by_label(self):
        ascending = self._sorted_ids(
            [
                {
                    "type": SORT_TYPE_RESOURCE_FIELD,
                    "field": "resource_instance_lifecycle_state",
                    "direction": DIRECTION_ASC,
                }
            ]
        )
        # "Draft" sorts before "Submitted" by label, not by primary key.
        submitted_position = ascending.index(self.owned_submitted.pk)
        self.assertEqual(submitted_position, len(ascending) - 1)

    def test_sort_by_nullable_field_puts_nulls_last_in_both_directions(self):
        for direction in (DIRECTION_ASC, DIRECTION_DESC):
            ordered = self._sorted_ids(
                [
                    {
                        "type": SORT_TYPE_RESOURCE_FIELD,
                        "field": "principaluser",
                        "direction": direction,
                    }
                ]
            )
            self.assertEqual(
                ordered[-1],
                self.unowned.pk,
                f"creator-less resource should sort last ({direction})",
            )

    def test_sort_rejects_unknown_resource_field(self):
        with self.assertRaises(ValidationError):
            SortResolver(
                [
                    {
                        "type": SORT_TYPE_RESOURCE_FIELD,
                        "field": "principaluser__password",
                        "direction": DIRECTION_ASC,
                    }
                ]
            )

    def test_group_by_resource_field(self):
        results = build_aggregations(
            ResourceInstance.objects.filter(graph=self.graph),
            [
                {
                    "name": "by_state",
                    "group_by": [
                        {
                            "type": GROUP_BY_TYPE_RESOURCE_FIELD,
                            "field": "resource_instance_lifecycle_state",
                            "alias": "state",
                        }
                    ],
                    "metrics": [
                        {
                            "type": GROUP_BY_TYPE_RESOURCE_FIELD,
                            "alias": "total",
                            "fn": "Count",
                            "field": "resourceinstanceid",
                        }
                    ],
                }
            ],
        )
        counts = {str(row["state"]): row["total"] for row in results["by_state"]}
        self.assertEqual(counts[str(self.state_draft.pk)], 3)
        self.assertEqual(counts[str(self.state_submitted.pk)], 1)

    def test_group_by_rejects_unbounded_cardinality_field(self):
        with self.assertRaises(ValidationError):
            resolve_group_by_path({"field": "createdtime"})

    def test_group_by_rejects_unknown_field(self):
        with self.assertRaises(ValidationError):
            resolve_group_by_path({"field": "principaluser__password"})


class ResourceFieldSearchAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="rf_api_user", password="pw")
        cls.stranger = User.objects.create_user(username="rf_api_other", password="pw")
        cls.admin = User.objects.create_superuser(
            username="rf_api_admin", email="rf@example.com", password="pw"
        )
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug="test-resource-field-api", isresource=True
        )
        lifecycle = ResourceInstanceLifecycle.objects.create(name="rf api lifecycle")
        cls.state = ResourceInstanceLifecycleState.objects.create(
            name="Api Draft",
            action_label="Draft",
            is_initial_state=True,
            resource_instance_lifecycle=lifecycle,
        )
        cls.graph.resource_instance_lifecycle = lifecycle
        cls.graph.save()

        cls.mine = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
            principaluser=cls.user,
            resource_instance_lifecycle_state=cls.state,
        )
        cls.mine.save()
        cls.theirs = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
            principaluser=cls.stranger,
            resource_instance_lifecycle_state=cls.state,
        )
        cls.theirs.save()

    def _search(self, body):
        return self.client.post(
            reverse("search"), json.dumps(body), content_type="application/json"
        )

    def test_is_current_user_filter_end_to_end(self):
        self.client.force_login(self.user)
        response = self._search(
            {
                "graph_slugs": [self.graph.slug],
                "advanced_search_queries": [
                    advanced_search_query(
                        self.graph.slug,
                        resource_field_clause(
                            "principaluser", OPERATOR_IS_CURRENT_USER
                        ),
                    )
                ],
            }
        )
        self.assertEqual(response.status_code, 200)
        ids = {
            resource["resourceinstanceid"] for resource in response.json()["resources"]
        }
        self.assertEqual(ids, {str(self.mine.resourceinstanceid)})

    def test_spoofed_current_user_operand_is_rejected(self):
        self.client.force_login(self.user)
        response = self._search(
            {
                "graph_slugs": [self.graph.slug],
                "advanced_search_queries": [
                    advanced_search_query(
                        self.graph.slug,
                        resource_field_clause(
                            "principaluser", OPERATOR_IS_CURRENT_USER, self.stranger.id
                        ),
                    )
                ],
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_unreachable_field_is_rejected(self):
        self.client.force_login(self.user)
        response = self._search(
            {
                "graph_slugs": [self.graph.slug],
                "advanced_search_queries": [
                    advanced_search_query(
                        self.graph.slug,
                        resource_field_clause(
                            "principaluser__password", OPERATOR_EQUALS, "x"
                        ),
                    )
                ],
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_sort_by_resource_field_end_to_end(self):
        # As a superuser, so both creators' resources are visible and the
        # ordering is observable at all.
        self.client.force_login(self.admin)
        response = self._search(
            {
                "graph_slugs": [self.graph.slug],
                "sort": [
                    {
                        "type": SORT_TYPE_RESOURCE_FIELD,
                        "field": "principaluser__username",
                        "direction": DIRECTION_ASC,
                    }
                ],
            }
        )
        self.assertEqual(response.status_code, 200)

        username_by_id = {
            self.user.pk: self.user.username,
            self.stranger.pk: self.stranger.username,
        }
        creators = [
            username_by_id[resource["principaluser_id"]]
            for resource in response.json()["resources"]
            if resource["principaluser_id"] in username_by_id
        ]
        self.assertEqual(creators, ["rf_api_other", "rf_api_user"])

    def test_metadata_endpoint_lists_fields_and_lifecycle_choices(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("resource_field_metadata"),
            {"graph_slugs": [self.graph.slug]},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()["fields"]
        by_name = {entry["field"]: entry for entry in payload}

        with self.subTest("exposes lifecycle state with choices"):
            lifecycle = by_name["resource_instance_lifecycle_state"]
            self.assertEqual(lifecycle["kind"], "ForeignKey")
            self.assertIn(
                str(self.state.pk),
                {choice["value"] for choice in lifecycle["choices"]},
            )

        with self.subTest("exposes creator as a user field"):
            self.assertTrue(by_name["principaluser"]["is_user_relation"])
            self.assertIn(
                OPERATOR_IS_CURRENT_USER, by_name["principaluser"]["operators"]
            )

        with self.subTest("does not advertise sensitive columns"):
            self.assertNotIn("principaluser__password", by_name)
            self.assertNotIn("principaluser__is_superuser", by_name)
