"""Tests for the generic N-hop traversal engine, in isolation from any
particular search-index table (text/geometry/date matching each have their
own tests for how they seed it)."""

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from arches.app.models.models import GraphModel, ResourceInstance, ResourceXResource

from arches_search.utils.node_agnostic_search.relationship_traversal import (
    expand_matches_via_relationships,
)

# python manage.py test tests.test_relationship_traversal --settings="tests.test_settings"


class RelationshipTraversalTests(TestCase):
    """
    target graph <- 1 hop -> bridge graph <- 1 hop -> seed graph

    seed_resource directly matches (it's in the seed id set). target_one_hop is
    connected directly to seed_resource. target_two_hop is connected to
    seed_resource only via bridge_resource (a non-target-graph resource).
    target_unconnected matches nothing at any depth.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username="relationship-traversal-admin",
            email="admin@example.com",
            password="unused",
        )

        cls.target_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug="relationship-traversal-target", isresource=True
        )
        cls.bridge_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug="relationship-traversal-bridge", isresource=True
        )
        cls.seed_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug="relationship-traversal-seed", isresource=True
        )

        cls.seed_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.seed_graph
        )
        cls.bridge_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.bridge_graph
        )
        cls.target_direct = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.target_graph
        )
        cls.target_one_hop = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.target_graph
        )
        cls.target_two_hop = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.target_graph
        )
        cls.target_unconnected = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.target_graph
        )

        # seed_resource -> target_one_hop (1 hop)
        ResourceXResource.objects.create(
            resourcexid=uuid.uuid4(),
            from_resource=cls.seed_resource,
            to_resource=cls.target_one_hop,
            from_resource_graph_id=cls.seed_graph.graphid,
            to_resource_graph_id=cls.target_graph.graphid,
        )
        # seed_resource -> bridge_resource -> target_two_hop (2 hops)
        ResourceXResource.objects.create(
            resourcexid=uuid.uuid4(),
            from_resource=cls.seed_resource,
            to_resource=cls.bridge_resource,
            from_resource_graph_id=cls.seed_graph.graphid,
            to_resource_graph_id=cls.bridge_graph.graphid,
        )
        ResourceXResource.objects.create(
            resourcexid=uuid.uuid4(),
            from_resource=cls.bridge_resource,
            to_resource=cls.target_two_hop,
            from_resource_graph_id=cls.bridge_graph.graphid,
            to_resource_graph_id=cls.target_graph.graphid,
        )

    def _seed_ids(self):
        return ResourceInstance.objects.filter(
            resourceinstanceid__in=[
                self.seed_resource.resourceinstanceid,
                self.target_direct.resourceinstanceid,
            ]
        ).values("resourceinstanceid")

    def _matched_ids(self, max_hops):
        return set(
            expand_matches_via_relationships(
                self._seed_ids(), self.target_graph.graphid, max_hops
            ).values_list("resourceinstanceid", flat=True)
        )

    def test_max_hops_zero_returns_only_direct_target_graph_matches(self):
        self.assertEqual(self._matched_ids(0), {self.target_direct.resourceinstanceid})

    def test_max_hops_one_includes_one_hop_but_not_two_hop(self):
        matches = self._matched_ids(1)
        self.assertEqual(
            matches,
            {self.target_direct.resourceinstanceid, self.target_one_hop.resourceinstanceid},
        )
        self.assertNotIn(self.target_two_hop.resourceinstanceid, matches)

    def test_max_hops_two_includes_direct_one_hop_and_two_hop(self):
        matches = self._matched_ids(2)
        self.assertEqual(
            matches,
            {
                self.target_direct.resourceinstanceid,
                self.target_one_hop.resourceinstanceid,
                self.target_two_hop.resourceinstanceid,
            },
        )

    def test_unconnected_target_resource_never_matches(self):
        matches = self._matched_ids(2)
        self.assertNotIn(self.target_unconnected.resourceinstanceid, matches)

    def test_max_hops_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            expand_matches_via_relationships(
                self._seed_ids(), self.target_graph.graphid, -1
            )
        with self.assertRaises(ValueError):
            expand_matches_via_relationships(
                self._seed_ids(), self.target_graph.graphid, 3
            )
