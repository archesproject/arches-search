import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import GraphModel, Node, NodeGroup
from arches.app.utils.permission_backend import assign_perm

from arches_search.models.models import NodeFilterConfig

# python manage.py test tests.test_node_filter_config_api --settings="tests.test_settings"


class NodeFilterConfigAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="nfc_admin", password="password123", email="nfc_admin@example.com"
        )
        cls.regular = User.objects.create_user(
            username="regular", password="password123"
        )

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="test-node-filter",
            isresource=True,
        )
        cls.other_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="other-graph",
            isresource=True,
        )

        cls.nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.restricted_nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())

        cls.name_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Name",
            alias="name",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
            config={"some": "config"},
        )
        cls.date_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Date",
            alias="date",
            datatype="date",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        cls.restricted_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Restricted",
            alias="restricted",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.restricted_nodegroup,
            istopnode=False,
        )

    def _url(self, graph_id):
        return reverse("node_filter_config_for_graph", kwargs={"graph_id": graph_id})

    def test_returns_empty_when_no_config_exists(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url(self.graph.graphid))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"nodes": []})

    def test_returns_empty_when_config_has_no_nodes(self):
        NodeFilterConfig.objects.create(graph=self.graph, config={"nodes": []})

        self.client.force_login(self.admin)
        response = self.client.get(self._url(self.graph.graphid))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"nodes": []})

    def test_returns_nodes_listed_in_config(self):
        NodeFilterConfig.objects.create(
            graph=self.graph,
            config={
                "nodes": [
                    {"node_alias": "name", "label": "Custom Name", "sortorder": 1},
                    {"node_alias": "date", "sortorder": 2},
                ]
            },
        )

        self.client.force_login(self.admin)
        response = self.client.get(self._url(self.graph.graphid))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["graph_id"], str(self.graph.graphid))
        self.assertEqual(data["slug"], "filtering")
        self.assertEqual(len(data["nodes"]), 2)

        aliases = [n["node_alias"] for n in data["nodes"]]
        self.assertIn("name", aliases)
        self.assertIn("date", aliases)

        name_entry = next(n for n in data["nodes"] if n["node_alias"] == "name")
        self.assertEqual(name_entry["label"], "Custom Name")
        self.assertEqual(name_entry["sortorder"], 1)
        self.assertEqual(name_entry["datatype"], "string")
        self.assertEqual(name_entry["node_id"], str(self.name_node.nodeid))
        self.assertEqual(name_entry["nodegroup_id"], str(self.nodegroup.nodegroupid))
        self.assertEqual(name_entry["config"], {"some": "config"})

    def test_label_falls_back_to_node_name(self):
        NodeFilterConfig.objects.create(
            graph=self.graph,
            config={"nodes": [{"node_alias": "name"}]},
        )

        self.client.force_login(self.admin)
        response = self.client.get(self._url(self.graph.graphid))

        entry = response.json()["nodes"][0]
        self.assertEqual(entry["label"], "Name")
        self.assertEqual(entry["sortorder"], 0)

    def test_unknown_alias_is_skipped(self):
        NodeFilterConfig.objects.create(
            graph=self.graph,
            config={
                "nodes": [
                    {"node_alias": "name"},
                    {"node_alias": "does_not_exist"},
                ]
            },
        )

        self.client.force_login(self.admin)
        response = self.client.get(self._url(self.graph.graphid))

        data = response.json()
        self.assertEqual(len(data["nodes"]), 1)
        self.assertEqual(data["nodes"][0]["node_alias"], "name")

    def test_slug_query_param_selects_config(self):
        NodeFilterConfig.objects.create(
            graph=self.graph,
            slug="filtering",
            config={"nodes": [{"node_alias": "name"}]},
        )
        NodeFilterConfig.objects.create(
            graph=self.graph,
            slug="alternate",
            config={"nodes": [{"node_alias": "date"}]},
        )

        self.client.force_login(self.admin)
        response = self.client.get(self._url(self.graph.graphid), {"slug": "alternate"})

        data = response.json()
        self.assertEqual(data["slug"], "alternate")
        aliases = [n["node_alias"] for n in data["nodes"]]
        self.assertEqual(aliases, ["date"])

    def test_default_slug_is_filtering(self):
        NodeFilterConfig.objects.create(
            graph=self.graph,
            slug="other",
            config={"nodes": [{"node_alias": "name"}]},
        )

        self.client.force_login(self.admin)
        response = self.client.get(self._url(self.graph.graphid))

        self.assertEqual(response.json(), {"nodes": []})

    def test_scoped_to_requested_graph(self):
        NodeFilterConfig.objects.create(
            graph=self.graph,
            config={"nodes": [{"node_alias": "name"}]},
        )

        self.client.force_login(self.admin)
        response = self.client.get(self._url(self.other_graph.graphid))

        self.assertEqual(response.json(), {"nodes": []})

    def test_permission_filters_out_unreadable_nodegroups(self):
        NodeFilterConfig.objects.create(
            graph=self.graph,
            config={
                "nodes": [
                    {"node_alias": "name"},
                    {"node_alias": "restricted"},
                ]
            },
        )
        # Grant read on the open nodegroup so it has explicit perms for this user.
        assign_perm("read_nodegroup", self.regular, self.nodegroup)
        # Give write (but NOT read) on the restricted nodegroup so the checker
        # finds explicit perms but read_nodegroup is not among them.
        assign_perm("write_nodegroup", self.regular, self.restricted_nodegroup)

        self.client.force_login(self.regular)
        response = self.client.get(self._url(self.graph.graphid))

        self.assertEqual(response.status_code, 200)
        aliases = [n["node_alias"] for n in response.json()["nodes"]]
        self.assertIn("name", aliases)
        self.assertNotIn("restricted", aliases)
