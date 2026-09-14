"""
Tests for grouping and measuring by a node value.

Grouping by a resource field is covered with the rest of that capability, in
tests/test_resource_field_search.py.

python manage.py test tests.integration.utils.search.test_aggregation --settings="tests.test_settings"
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from arches.app.models.models import ResourceInstance
from arches.app.utils.permission_backend import assign_perm

from arches_search.utils.readable_nodes import ReadableNodes
from arches_search.utils.search.aggregation import build_aggregations
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
