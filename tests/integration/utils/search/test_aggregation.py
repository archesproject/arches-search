"""
Tests for aggregations: what a request may ask for, and grouping by a node value.

Grouping by a resource field is covered with the rest of that capability, in
tests/test_resource_field_search.py.

python manage.py test tests.integration.utils.search.test_aggregation --settings="tests.test_settings"
"""

import json
import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from arches.app.models.models import GraphModel, ResourceInstance
from arches.app.utils.permission_backend import assign_perm

from arches_search.utils.readable_nodes import ReadableNodes
from arches_search.utils.search.aggregation import build_aggregations
from arches_search.utils.search.validation import validate_aggregations
from tests.integration.utils.advanced_search.test_advanced_search import (
    AdvancedSearchSetupMixin,
)


def _node_group(node_alias, alias, graph_slug="person"):
    return {
        "type": "NODE",
        "graph_slug": graph_slug,
        "node_alias": node_alias,
        "alias": alias,
    }


def _resource_count(alias="total"):
    return {
        "type": "RESOURCE_FIELD",
        "field": "resourceinstanceid",
        "fn": "Count",
        "alias": alias,
    }


def _aggregation(**overrides):
    """Resources per nickname, with any key replaced or added."""
    aggregation = {
        "name": "by_nickname",
        "group_by": [_node_group("nickname", "nickname")],
        "metrics": [_resource_count()],
    }
    aggregation.update(overrides)
    return aggregation


class AggregationValidationTests(SimpleTestCase):
    def test_none_is_allowed(self):
        validate_aggregations(None)

    def test_a_well_formed_aggregation_passes(self):
        validate_aggregations(
            [
                _aggregation(
                    aggregate=[
                        {
                            "alias": "distinct_nicknames",
                            "fn": "Count",
                            "field": "nickname",
                            "distinct": True,
                        }
                    ]
                )
            ]
        )

    def test_keys_that_used_to_reach_the_orm_are_refused(self):
        nickname = _node_group("nickname", "nickname")
        cases = {
            "where on an aggregation": _aggregation(
                where={"principaluser__username": "admin"}
            ),
            "where on a node spec": _aggregation(
                group_by=[{**nickname, "where": {"value__startswith": "A"}}]
            ),
            "search_table on a node spec": _aggregation(
                group_by=[{**nickname, "search_table": "auth_user"}]
            ),
            "kwargs on a simple aggregate": _aggregation(
                aggregate=[
                    {
                        "alias": "nicknames",
                        "fn": "Count",
                        "field": "nickname",
                        "kwargs": {"distinct": True},
                    }
                ]
            ),
        }
        for description, aggregation in cases.items():
            with self.subTest(description), self.assertRaises(ValidationError):
                validate_aggregations([aggregation])

    def test_a_simple_aggregate_can_only_read_a_grouped_column(self):
        # A path is how a column outside the search results would be read; a
        # metric alias is refused too, since an aggregate cannot be aggregated.
        for field in ("principaluser__password", "resourceinstanceid", "total"):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                validate_aggregations(
                    [
                        _aggregation(
                            aggregate=[{"alias": "leak", "fn": "Max", "field": field}]
                        )
                    ]
                )

    def test_only_listed_functions_are_allowed(self):
        for fn in ("RawSQL", "Subquery", "Func", "count"):
            with self.subTest(fn=fn), self.assertRaises(ValidationError):
                validate_aggregations(
                    [_aggregation(metrics=[{**_resource_count(), "fn": fn}])]
                )

    def test_an_aggregation_must_group_by_something(self):
        # With nothing to group by, the rows themselves would come back.
        without_group_by = _aggregation()
        del without_group_by["group_by"]

        for aggregation in (without_group_by, _aggregation(group_by=[])):
            with (
                self.subTest(aggregation=aggregation),
                self.assertRaises(ValidationError),
            ):
                validate_aggregations([aggregation])

    def test_aliases_must_be_annotation_names_that_collide_with_nothing(self):
        for alias in ("", "1st", "a__b", "has space", "graph", "resourceinstanceid"):
            with self.subTest(alias=alias), self.assertRaises(ValidationError):
                validate_aggregations(
                    [_aggregation(group_by=[_node_group("nickname", alias)])]
                )

    def test_result_names_and_column_aliases_must_be_unique(self):
        cases = {
            "two aggregations with one name": [_aggregation(), _aggregation()],
            "a metric reusing a group_by alias": [
                _aggregation(metrics=[_resource_count("nickname")])
            ],
        }
        for description, aggregations in cases.items():
            with self.subTest(description), self.assertRaises(ValidationError):
                validate_aggregations(aggregations)

    def test_distinct_is_refused_where_the_function_cannot_take_it(self):
        with self.assertRaises(ValidationError):
            validate_aggregations(
                [
                    _aggregation(
                        aggregate=[
                            {
                                "alias": "latest",
                                "fn": "Max",
                                "field": "nickname",
                                "distinct": True,
                            }
                        ]
                    )
                ]
            )


class AggregationRequestTests(TestCase):
    """The request that once read another user's password hash."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="aggregation_admin",
            password="password123",
            email="aggregation_admin@example.com",
        )
        cls.owner = User.objects.create_user(
            username="aggregation_owner", password="password123"
        )
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="aggregation-request",
            isresource=True,
            is_active=True,
        )
        ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph, principaluser=cls.owner
        )

    def test_an_aggregate_over_a_related_column_is_a_400(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("search"),
            json.dumps(
                {
                    "graph_slugs": [self.graph.slug],
                    "aggregations": [
                        {
                            "name": "leak",
                            "aggregate": [
                                {
                                    "alias": "password_hash",
                                    "fn": "Max",
                                    "field": "principaluser__password",
                                }
                            ],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn(self.owner.password, response.content.decode())


class NodeAggregationTests(AdvancedSearchSetupMixin, TestCase):
    """
    Grouping by a node value, resolved the way a clause resolves its subject.

    Each person in the fixture has one nickname: ALPHA, BETA, CHARLIE, DELTA.
    The restricted user cannot read the nodegroup holding first_name.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = User.objects.create_superuser(
            username="node_aggregation_admin",
            password="password123",
            email="node_aggregation_admin@example.com",
        )
        cls.restricted = User.objects.create_user(
            username="node_aggregation_restricted", password="password123"
        )
        assign_perm("no_access_to_nodegroup", cls.restricted, cls.alias)

    def _aggregate_as(self, user, aggregation):
        validate_aggregations([aggregation])
        return build_aggregations(
            ResourceInstance.objects.filter(graph=self.person_graph),
            [aggregation],
            ReadableNodes(user),
        )

    def test_group_by_a_node_value(self):
        results = self._aggregate_as(self.admin, _aggregation())

        self.assertEqual(
            {row["nickname"]: row["total"] for row in results["by_nickname"]},
            {"ALPHA": 1, "BETA": 1, "CHARLIE": 1, "DELTA": 1},
        )

    def test_a_simple_aggregate_over_a_grouped_node_value(self):
        results = self._aggregate_as(
            self.admin,
            _aggregation(
                aggregate=[
                    {
                        "alias": "distinct_nicknames",
                        "fn": "Count",
                        "field": "nickname",
                        "distinct": True,
                    }
                ]
            ),
        )

        self.assertEqual(results["distinct_nicknames"], 4)

    def test_a_readable_node_aggregates_the_same_for_a_restricted_user(self):
        self.assertEqual(
            self._aggregate_as(self.restricted, _aggregation()),
            self._aggregate_as(self.admin, _aggregation()),
        )

    def test_an_unreadable_node_is_refused_like_an_unknown_node(self):
        with self.assertRaises(ValidationError) as unreadable:
            self._aggregate_as(
                self.restricted,
                _aggregation(group_by=[_node_group("first_name", "first_name")]),
            )
        with self.assertRaises(ValidationError) as unknown:
            self._aggregate_as(
                self.admin,
                _aggregation(group_by=[_node_group("no_such_node", "first_name")]),
            )

        self.assertEqual(
            unreadable.exception.messages[0].replace("first_name", "<node>"),
            unknown.exception.messages[0].replace("no_such_node", "<node>"),
        )
