"""API-level tests for the graphId -> graphIds (multi-select) change in
SimpleSearchAPI, in particular the pagination-total behavior: with no
graphIds, `total_results` falls back to `all_resource_count` (the
type-agnostic count); with graphIds present, it should reflect the
graph-scoped result count instead."""

import io
import json
import uuid

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    TileModel,
)
from arches.app.utils.permission_backend import assign_perm

# python manage.py test tests.test_simple_search_api --settings="tests.test_settings"


class SimpleSearchAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="simple_search_user", password="password123"
        )

        cls.graph_a = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="simple-search-api-test-mineral",
            isresource=True,
            is_active=True,
        )
        cls.graph_b = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="simple-search-api-test-site",
            isresource=True,
            is_active=True,
        )
        cls.nodegroup_a = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.nodegroup_b = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.node_a = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="mineral_name",
            alias="mineral_name",
            datatype="string",
            graph=cls.graph_a,
            nodegroup=cls.nodegroup_a,
            istopnode=True,
        )
        cls.node_b = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="site_name",
            alias="site_name",
            datatype="string",
            graph=cls.graph_b,
            nodegroup=cls.nodegroup_b,
            istopnode=True,
        )

        cls.amber_mineral = cls._create_resource(
            cls.graph_a, cls.nodegroup_a, cls.node_a, "amber specimen"
        )
        cls.amber_site = cls._create_resource(
            cls.graph_b, cls.nodegroup_b, cls.node_b, "amber excavation site"
        )

        assign_perm("view_resourceinstance", cls.user, cls.amber_mineral)
        assign_perm("view_resourceinstance", cls.user, cls.amber_site)

        call_command("arches_search", "reindex_database", stdout=io.StringIO())

    @classmethod
    def _create_resource(cls, graph, nodegroup, node, text):
        resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=graph
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=nodegroup,
            resourceinstance=resource,
            data={str(node.nodeid): {"en": {"value": text, "direction": "ltr"}}},
            provisionaledits=None,
        )
        return resource

    def setUp(self):
        self.client.force_login(self.user)

    def _post_search(self, body):
        return self.client.post(
            reverse("arches_search"),
            json.dumps(body),
            content_type="application/json",
        )

    def test_no_graph_ids_returns_matches_from_every_graph(self):
        response = self._post_search({"terms": [{"text": "amber"}], "graphIds": []})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        resource_ids = {r["resourceinstanceid"] for r in data["resources"]}
        self.assertEqual(
            resource_ids,
            {
                str(self.amber_mineral.resourceinstanceid),
                str(self.amber_site.resourceinstanceid),
            },
        )
        self.assertEqual(data["pagination"]["total_results"], 2)
        self.assertEqual(data["all_resource_count"], 2)

    def test_missing_graph_ids_behaves_like_empty(self):
        response = self._post_search({"terms": [{"text": "amber"}]})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["pagination"]["total_results"], 2)

    def test_single_graph_id_scopes_results_and_pagination_total(self):
        response = self._post_search(
            {
                "terms": [{"text": "amber"}],
                "graphIds": [str(self.graph_a.graphid)],
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        resource_ids = {r["resourceinstanceid"] for r in data["resources"]}
        self.assertEqual(resource_ids, {str(self.amber_mineral.resourceinstanceid)})
        # Scoped: total_results must reflect the graph-scoped count (1), not
        # all_resource_count (2, the type-agnostic count across all graphs).
        self.assertEqual(data["pagination"]["total_results"], 1)
        self.assertEqual(data["all_resource_count"], 2)

    def test_multiple_graph_ids_unions_results_and_pagination_total(self):
        response = self._post_search(
            {
                "terms": [{"text": "amber"}],
                "graphIds": [str(self.graph_a.graphid), str(self.graph_b.graphid)],
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        resource_ids = {r["resourceinstanceid"] for r in data["resources"]}
        self.assertEqual(
            resource_ids,
            {
                str(self.amber_mineral.resourceinstanceid),
                str(self.amber_site.resourceinstanceid),
            },
        )
        self.assertEqual(data["pagination"]["total_results"], 2)

    def test_resource_type_counts_cover_every_graph_regardless_of_graph_ids(self):
        response = self._post_search(
            {
                "terms": [{"text": "amber"}],
                "graphIds": [str(self.graph_a.graphid)],
            }
        )

        self.assertEqual(response.status_code, 200)
        counts_by_graph_id = {
            row["graph_id"]: row["count"]
            for row in response.json()["resource_type_counts"]
        }
        self.assertEqual(counts_by_graph_id[str(self.graph_a.graphid)], 1)
        self.assertEqual(counts_by_graph_id[str(self.graph_b.graphid)], 1)
