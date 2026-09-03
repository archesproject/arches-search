"""
Tests for filtering, sorting, and grouping search results by ResourceInstance
system-level fields.

Covers:
  - Registry discovery: which fields are exposed is derived from the model, and
    sensitive related-model columns are unreachable by construction.
  - Payload validation, including that an IS_CURRENT_USER clause carrying a
    user id is rejected rather than silently ignored.
  - Resolver/queryset behavior, including the AnonymousUser case and the
    guarantee that a resource-field filter can only narrow what the permission
    framework already allows.
  - resource_field sorting (label ordering, nulls last) and grouping.

python manage.py test tests.test_resource_field_search --settings="tests.test_settings"
"""

import json
import uuid

from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from arches.app.models.models import (
    GraphModel,
    ResourceInstance,
    ResourceInstanceLifecycle,
    ResourceInstanceLifecycleState,
)
from arches.app.utils.permission_backend import assign_perm

from arches_search.utils.advanced_search.advanced_search import (
    SearchCompiler,
    SearchPayload,
)
from arches_search.utils.resource_field_search.field_registry import (
    OPERATOR_AFTER,
    OPERATOR_BEFORE,
    OPERATOR_CONTAINS,
    OPERATOR_EQUALS,
    OPERATOR_HAS_ANY_VALUE,
    OPERATOR_HAS_NO_VALUE,
    OPERATOR_IN,
    OPERATOR_IS_CURRENT_USER,
    OPERATOR_IS_NOT_CURRENT_USER,
    OPERATOR_RANGE,
    OPERATOR_STARTS_WITH,
    get_resource_field_registry,
)
from arches_search.utils.resource_field_search.grouping import (
    GROUP_BY_TYPE_RESOURCE_FIELD,
    resolve_group_by_path,
)
from arches_search.utils.resource_field_search.resolver import (
    MATCH_NOTHING,
    build_resource_field_filter,
)
from arches_search.utils.resource_field_search.validators import (
    validate_resource_field_filters,
)
from arches_search.utils.search_aggregation import build_aggregations
from arches_search.utils.search_sort import (
    DIRECTION_ASC,
    DIRECTION_DESC,
    SORT_TYPE_RESOURCE_FIELD,
    SortResolver,
)

# ---------------------------------------------------------------------------
# Registry discovery
# ---------------------------------------------------------------------------


class ResourceFieldRegistryTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.registry = get_resource_field_registry()

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

    def test_json_backed_fields_are_not_exposed(self):
        # name/descriptors are I18n_TextField/JSONField, which have no operator
        # vocabulary. They fall out of discovery without a name-based denylist.
        self.assertIsNone(self.registry.get("name"))
        self.assertIsNone(self.registry.get("descriptors"))

    def test_sensitive_user_columns_are_unreachable(self):
        for probe in [
            "principaluser__password",
            "principaluser__is_superuser",
            "principaluser__is_staff",
            "principaluser__email",
            "principaluser__last_login",
            "principaluser__groups",
        ]:
            self.assertIsNone(
                self.registry.get(probe), f"{probe} must not be queryable"
            )

    def test_multi_hop_traversal_is_unreachable(self):
        self.assertIsNone(self.registry.get("principaluser__groups__permissions"))

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
        groupable = {descriptor.name for descriptor in self.registry.groupable()}
        self.assertIn("resource_instance_lifecycle_state", groupable)
        self.assertIn("principaluser", groupable)
        self.assertNotIn("createdtime", groupable)
        self.assertNotIn("resourceinstanceid", groupable)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class ResourceFieldFilterValidationTests(SimpleTestCase):
    def test_none_is_allowed(self):
        validate_resource_field_filters(None)

    def test_non_list_raises(self):
        with self.assertRaises(ValidationError):
            validate_resource_field_filters({"field": "principaluser"})

    def test_unknown_field_raises(self):
        with self.assertRaises(ValidationError):
            validate_resource_field_filters(
                [{"field": "not_a_field", "operator": OPERATOR_EQUALS, "value": 1}]
            )

    def test_sensitive_field_raises(self):
        with self.assertRaises(ValidationError):
            validate_resource_field_filters(
                [
                    {
                        "field": "principaluser__password",
                        "operator": OPERATOR_EQUALS,
                        "value": "x",
                    }
                ]
            )

    def test_operator_not_supported_for_field_raises(self):
        with self.assertRaises(ValidationError):
            validate_resource_field_filters(
                [{"field": "createdtime", "operator": OPERATOR_CONTAINS, "value": "x"}]
            )

    def test_is_current_user_rejects_supplied_value(self):
        # Supplying a value here is an attempt to filter as somebody else; it
        # must fail loudly rather than be quietly discarded.
        with self.assertRaises(ValidationError):
            validate_resource_field_filters(
                [
                    {
                        "field": "principaluser",
                        "operator": OPERATOR_IS_CURRENT_USER,
                        "value": 1,
                    }
                ]
            )

    def test_is_current_user_without_value_is_valid(self):
        validate_resource_field_filters(
            [{"field": "principaluser", "operator": OPERATOR_IS_CURRENT_USER}]
        )

    def test_in_requires_non_empty_list(self):
        with self.assertRaises(ValidationError):
            validate_resource_field_filters(
                [
                    {
                        "field": "resource_instance_lifecycle_state",
                        "operator": OPERATOR_IN,
                        "value": [],
                    }
                ]
            )

    def test_missing_value_raises(self):
        with self.assertRaises(ValidationError):
            validate_resource_field_filters(
                [{"field": "legacyid", "operator": OPERATOR_EQUALS}]
            )


# ---------------------------------------------------------------------------
# Filtering, sorting and grouping against real rows
# ---------------------------------------------------------------------------


class ResourceFieldPredicateTests(SimpleTestCase):
    """
    Each operator compiles to the ORM predicate it claims to.

    No database: build_resource_field_filter() is a pure translation from a
    filter entry to a Q, so the whole operator vocabulary is checked here rather
    than paying for a fixture per operator.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.registry = get_resource_field_registry()

    def _predicate(self, field, operator, value=None, user=AnonymousUser()):
        entry = {"field": field, "operator": operator}
        if value is not None:
            entry["value"] = value
        return build_resource_field_filter(user, [entry], registry=self.registry)

    def test_scalar_operators_compile_to_expected_lookups(self):
        cases = [
            (OPERATOR_EQUALS, "legacyid", "abc", Q(legacyid="abc")),
            (OPERATOR_IN, "legacyid", ["a", "b"], Q(legacyid__in=["a", "b"])),
            (OPERATOR_CONTAINS, "legacyid", "ab", Q(legacyid__icontains="ab")),
            (OPERATOR_STARTS_WITH, "legacyid", "ab", Q(legacyid__istartswith="ab")),
        ]
        for operator, field, value, expected in cases:
            with self.subTest(operator=operator):
                self.assertEqual(self._predicate(field, operator, value), expected)

    def test_date_operators_compile_to_expected_lookups(self):
        cases = [
            (
                OPERATOR_RANGE,
                {"from": "2020-01-01", "to": "2020-12-31"},
                Q(createdtime__range=("2020-01-01", "2020-12-31")),
            ),
            (OPERATOR_BEFORE, "2020-01-01", Q(createdtime__lt="2020-01-01")),
            (OPERATOR_AFTER, "2020-01-01", Q(createdtime__gt="2020-01-01")),
        ]
        for operator, value, expected in cases:
            with self.subTest(operator=operator):
                self.assertEqual(
                    self._predicate("createdtime", operator, value), expected
                )

    def test_presence_operators_compile_to_isnull_lookups(self):
        self.assertEqual(
            self._predicate("principaluser", OPERATOR_HAS_ANY_VALUE),
            Q(principaluser_id__isnull=False),
        )
        self.assertEqual(
            self._predicate("principaluser", OPERATOR_HAS_NO_VALUE),
            Q(principaluser_id__isnull=True),
        )

    def test_is_not_current_user_keeps_creatorless_resources(self):
        """A bare ~Q would drop NULL-creator rows under SQL three-valued logic."""
        user = User(id=42, username="someone")
        predicate = self._predicate(
            "principaluser", OPERATOR_IS_NOT_CURRENT_USER, user=user
        )

        self.assertEqual(
            predicate, ~Q(principaluser_id=42) | Q(principaluser_id__isnull=True)
        )

    def test_anonymous_is_not_current_user_constrains_nothing(self):
        """There is no identity to exclude, so the filter must not narrow."""
        self.assertIsNone(
            self._predicate("principaluser", OPERATOR_IS_NOT_CURRENT_USER)
        )

    def test_unknown_field_matches_nothing_rather_than_widening(self):
        predicate = self._predicate("no_such_field", OPERATOR_EQUALS, "x")

        self.assertEqual(predicate, MATCH_NOTHING)

    def test_unsupported_operator_raises_rather_than_silently_passing(self):
        with self.assertRaises(ValueError):
            self._predicate("legacyid", "NOT_AN_OPERATOR", "x")

    def test_no_entries_produces_no_predicate(self):
        self.assertIsNone(
            build_resource_field_filter(AnonymousUser(), [], registry=self.registry)
        )

    def test_entries_are_and_ed_together(self):
        combined = build_resource_field_filter(
            AnonymousUser(),
            [
                {"field": "legacyid", "operator": OPERATOR_CONTAINS, "value": "ab"},
                {"field": "principaluser", "operator": OPERATOR_HAS_NO_VALUE},
            ],
            registry=self.registry,
        )

        self.assertEqual(
            combined, Q(legacyid__icontains="ab") & Q(principaluser_id__isnull=True)
        )


class ResourceFieldValueShapeValidationTests(SimpleTestCase):
    """
    Each operator rejects a malformed value rather than passing it to the ORM.

    A bad shape that reaches the query layer surfaces as a 500 (or, worse, a
    silently wrong result set), so these are 400s raised up front.
    """

    def _assert_rejected(self, operator, field, value):
        with self.assertRaises(ValidationError):
            validate_resource_field_filters(
                [{"field": field, "operator": operator, "value": value}]
            )

    def _assert_accepted(self, operator, field, value):
        validate_resource_field_filters(
            [{"field": field, "operator": operator, "value": value}]
        )

    def test_in_requires_a_non_empty_list(self):
        # A relation field, since IN is only offered for FK/UUID fields -- using
        # a text field here would fail on operator support, not value shape.
        field = "resource_instance_lifecycle_state"
        for value in ([], "not-a-list", None):
            with self.subTest(value=value):
                self._assert_rejected(OPERATOR_IN, field, value)
        self._assert_accepted(OPERATOR_IN, field, [str(uuid.uuid4())])

    def test_range_requires_both_bounds(self):
        for value in ({"from": "2020-01-01"}, {"to": "2020-01-01"}, {}, "nope"):
            with self.subTest(value=value):
                self._assert_rejected(OPERATOR_RANGE, "createdtime", value)
        self._assert_accepted(
            OPERATOR_RANGE, "createdtime", {"from": "2020-01-01", "to": "2020-12-31"}
        )

    def test_text_operators_require_a_non_empty_string(self):
        for operator in (OPERATOR_CONTAINS, OPERATOR_STARTS_WITH):
            for value in ("", ["a"], 5):
                with self.subTest(operator=operator, value=value):
                    self._assert_rejected(operator, "legacyid", value)
            self._assert_accepted(operator, "legacyid", "ab")

    def test_single_value_operators_reject_collections(self):
        for operator in (OPERATOR_EQUALS, OPERATOR_BEFORE, OPERATOR_AFTER):
            for value in (["a"], {"from": "x"}):
                with self.subTest(operator=operator, value=value):
                    self._assert_rejected(operator, "createdtime", value)

    def test_non_list_payload_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_resource_field_filters({"field": "legacyid"})

    def test_non_object_entry_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_resource_field_filters(["legacyid"])

    def test_none_payload_is_accepted_as_no_filters(self):
        self.assertIsNone(validate_resource_field_filters(None))


class ResourceFieldSearchDataTests(TestCase):
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
        cls.state_draft = ResourceInstanceLifecycleState.objects.create(
            name="Draft",
            action_label="Draft",
            is_initial_state=True,
            resource_instance_lifecycle=lifecycle,
        )
        cls.state_submitted = ResourceInstanceLifecycleState.objects.create(
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

    def _filtered_ids(self, user, filter_entries):
        predicate = build_resource_field_filter(user, filter_entries)
        queryset = ResourceInstance.objects.filter(graph=self.graph)
        if predicate is not None:
            queryset = queryset.filter(predicate)
        return set(queryset.values_list("resourceinstanceid", flat=True))

    # --- identity ---

    def test_is_current_user_returns_only_own_resources(self):
        self.assertEqual(
            self._filtered_ids(
                self.owner,
                [{"field": "principaluser", "operator": OPERATOR_IS_CURRENT_USER}],
            ),
            {self.owned_draft.pk, self.owned_submitted.pk},
        )

    def test_is_current_user_matches_nothing_for_anonymous(self):
        # AnonymousUser.id is None; a naive equality filter would compile to
        # "principaluser_id IS NULL" and surface every creator-less resource.
        matched = self._filtered_ids(
            AnonymousUser(),
            [{"field": "principaluser", "operator": OPERATOR_IS_CURRENT_USER}],
        )
        self.assertEqual(matched, set())
        self.assertNotIn(self.unowned.pk, matched)

    def test_is_not_current_user_includes_creatorless_resources(self):
        # A bare negation would drop NULL rows under three-valued logic.
        self.assertEqual(
            self._filtered_ids(
                self.owner,
                [{"field": "principaluser", "operator": OPERATOR_IS_NOT_CURRENT_USER}],
            ),
            {self.other_draft.pk, self.unowned.pk},
        )

    def test_filter_by_username_hop(self):
        self.assertEqual(
            self._filtered_ids(
                self.owner,
                [
                    {
                        "field": "principaluser__username",
                        "operator": OPERATOR_EQUALS,
                        "value": "rf_other",
                    }
                ],
            ),
            {self.other_draft.pk},
        )

    # --- lifecycle state ---

    def test_filter_by_lifecycle_state_in(self):
        self.assertEqual(
            self._filtered_ids(
                self.owner,
                [
                    {
                        "field": "resource_instance_lifecycle_state",
                        "operator": OPERATOR_IN,
                        "value": [str(self.state_submitted.pk)],
                    }
                ],
            ),
            {self.owned_submitted.pk},
        )

    def test_filters_combine_with_and(self):
        self.assertEqual(
            self._filtered_ids(
                self.owner,
                [
                    {"field": "principaluser", "operator": OPERATOR_IS_CURRENT_USER},
                    {
                        "field": "resource_instance_lifecycle_state",
                        "operator": OPERATOR_IN,
                        "value": [str(self.state_draft.pk)],
                    },
                ],
            ),
            {self.owned_draft.pk},
        )

    # --- permission bounding ---

    def test_filter_cannot_surface_resources_the_user_cannot_see(self):
        """
        A resource-field filter only narrows; the permission framework remains
        the authority on what is visible.
        """
        payload = SearchPayload(
            graph_ids=[str(self.graph.graphid)],
            node_agnostic_filters=None,
            advanced_search_query=None,
            resource_field_filters=[
                {
                    "field": "principaluser__username",
                    "operator": OPERATOR_EQUALS,
                    "value": "rf_owner",
                }
            ],
        )
        visible = set(
            SearchCompiler(payload, self.member)
            .compile()
            .results.values_list("resourceinstanceid", flat=True)
        )
        self.assertEqual(visible, set())

        # The same filter, run by someone who may see those rows, does match.
        owner_visible = set(
            SearchCompiler(payload, self.owner)
            .compile()
            .results.values_list("resourceinstanceid", flat=True)
        )
        self.assertEqual(owner_visible, {self.owned_draft.pk, self.owned_submitted.pk})

    def test_granted_resource_still_requires_the_filter_to_match(self):
        assign_perm("view_resourceinstance", self.group, self.other_draft)
        payload = SearchPayload(
            graph_ids=[str(self.graph.graphid)],
            node_agnostic_filters=None,
            advanced_search_query=None,
            resource_field_filters=[
                {
                    "field": "resource_instance_lifecycle_state",
                    "operator": OPERATOR_IN,
                    "value": [str(self.state_submitted.pk)],
                }
            ],
        )
        visible = set(
            SearchCompiler(payload, self.member)
            .compile()
            .results.values_list("resourceinstanceid", flat=True)
        )
        # other_draft is visible to member but is not in the requested state.
        self.assertEqual(visible, set())

    # --- sorting ---

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

    # --- grouping ---

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


# ---------------------------------------------------------------------------
# HTTP surface
# ---------------------------------------------------------------------------


class ResourceFieldSearchAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="rf_api_user", password="pw")
        cls.stranger = User.objects.create_user(username="rf_api_other", password="pw")
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
                "graph_ids": [str(self.graph.graphid)],
                "resource_field_filters": [
                    {"field": "principaluser", "operator": OPERATOR_IS_CURRENT_USER}
                ],
            }
        )
        self.assertEqual(response.status_code, 200)
        ids = {
            resource["resourceinstanceid"] for resource in response.json()["resources"]
        }
        self.assertEqual(ids, {str(self.mine.resourceinstanceid)})

    def test_spoofed_current_user_value_is_rejected(self):
        self.client.force_login(self.user)
        response = self._search(
            {
                "graph_ids": [str(self.graph.graphid)],
                "resource_field_filters": [
                    {
                        "field": "principaluser",
                        "operator": OPERATOR_IS_CURRENT_USER,
                        "value": self.stranger.id,
                    }
                ],
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_unreachable_field_is_rejected(self):
        self.client.force_login(self.user)
        response = self._search(
            {
                "graph_ids": [str(self.graph.graphid)],
                "resource_field_filters": [
                    {
                        "field": "principaluser__password",
                        "operator": OPERATOR_EQUALS,
                        "value": "x",
                    }
                ],
            }
        )
        self.assertEqual(response.status_code, 400)

    def test_sort_by_resource_field_end_to_end(self):
        self.client.force_login(self.user)
        response = self._search(
            {
                "graph_ids": [str(self.graph.graphid)],
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

    def test_metadata_endpoint_lists_fields_and_lifecycle_choices(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("resource_field_metadata"),
            {"graph_ids": [str(self.graph.graphid)]},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()["fields"]
        by_name = {entry["field"]: entry for entry in payload}

        with self.subTest("exposes lifecycle state with choices"):
            lifecycle = by_name["resource_instance_lifecycle_state"]
            self.assertEqual(lifecycle["kind"], "CHOICE")
            self.assertIn(
                str(self.state.pk),
                {choice["value"] for choice in lifecycle["choices"]},
            )

        with self.subTest("exposes creator as a user field"):
            self.assertEqual(by_name["principaluser"]["kind"], "USER")
            self.assertIn(
                OPERATOR_IS_CURRENT_USER, by_name["principaluser"]["operators"]
            )

        with self.subTest("does not advertise sensitive columns"):
            self.assertNotIn("principaluser__password", by_name)
            self.assertNotIn("principaluser__is_superuser", by_name)
