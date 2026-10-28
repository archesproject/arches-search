import uuid
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from arches.app.models.models import (
    CardModel,
    CardXNodeXWidget,
    GraphModel,
    Node,
    NodeGroup,
    Widget,
)
from arches.app.models.system_settings import settings

from arches_search.models.models import NodeFilterConfig


class FilterConfigsCommandTest(TestCase):
    PLACEHOLDER_CONFIG = {"nodes": [{"node_alias": "custom"}]}

    @classmethod
    def setUpTestData(cls):
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="test-filter-configs",
            isresource=True,
        )
        cls.other_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="other-filter-configs",
            isresource=True,
        )
        cls.branch_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="branch-graph",
            isresource=False,
        )

        cls.nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())

        cls.reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Reference Node",
            alias="reference_node",
            datatype="reference",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
            issearchable=True,
        )
        cls.number_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Number Node",
            alias="number_node",
            datatype="number",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
            issearchable=True,
        )
        cls.string_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="String Node",
            alias="string_node",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
            issearchable=True,
        )
        cls.non_localized_string_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Non-localized String Node",
            alias="non_localized_string_node",
            datatype="non-localized-string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
            issearchable=True,
        )
        cls.unfilterable_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Unfilterable Node",
            alias="unfilterable_node",
            datatype="boolean",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
            issearchable=True,
        )
        cls.unsearchable_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Unsearchable Node",
            alias="unsearchable_node",
            datatype="reference",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
            issearchable=False,
        )
        cls.hidden_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="Hidden Node",
            alias="hidden_node",
            datatype="reference",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
            issearchable=True,
        )

        card = CardModel.objects.create(
            graph=cls.graph, nodegroup=cls.nodegroup, sortorder=0
        )
        widget = Widget.objects.create(
            name="test-widget", component="test-widget", datatype="string"
        )
        # Widget order differs from the alphabetical order of the node names.
        for node, sortorder, visible in [
            (cls.reference_node, 0, True),
            (cls.number_node, 1, True),
            (cls.hidden_node, 2, False),
            (cls.string_node, 3, True),
            (cls.non_localized_string_node, 4, True),
            (cls.unfilterable_node, 5, True),
            (cls.unsearchable_node, 6, True),
        ]:
            CardXNodeXWidget.objects.create(
                node=node,
                card=card,
                widget=widget,
                sortorder=sortorder,
                visible=visible,
            )

    def test_generate_populates_eligible_graphs_with_filtered_ordered_nodes(self):
        call_command("filter_configs", "generate")

        config = NodeFilterConfig.objects.get(graph=self.graph, slug="filtering")
        nodes = config.config["nodes"]
        self.assertEqual(
            [n["node_alias"] for n in nodes],
            ["reference_node", "number_node"],
        )
        for node in nodes:
            self.assertEqual(node["filterable"], False)
            self.assertEqual(node["sortable"], False)

        other_config = NodeFilterConfig.objects.get(
            graph=self.other_graph, slug="filtering"
        )
        self.assertEqual(other_config.config["nodes"], [])

        self.assertFalse(
            NodeFilterConfig.objects.filter(graph=self.branch_graph).exists()
        )
        self.assertFalse(
            NodeFilterConfig.objects.filter(
                graph_id=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID
            ).exists()
        )

    def test_generate_does_not_overwrite_existing_config_by_default(self):
        NodeFilterConfig.objects.create(
            graph=self.graph, slug="filtering", config=self.PLACEHOLDER_CONFIG
        )

        call_command("filter_configs", "generate")

        config = NodeFilterConfig.objects.get(graph=self.graph, slug="filtering")
        self.assertEqual(config.config, self.PLACEHOLDER_CONFIG)

    def test_generate_overwrite_confirmation(self):
        config = NodeFilterConfig.objects.create(
            graph=self.graph, slug="filtering", config=self.PLACEHOLDER_CONFIG
        )
        out = StringIO()

        with patch("builtins.input", return_value="n") as mock_input:
            call_command("filter_configs", "generate", overwrite=True, stdout=out)
        mock_input.assert_called_once()
        self.assertIn("Aborted", out.getvalue())
        config.refresh_from_db()
        self.assertEqual(config.config, self.PLACEHOLDER_CONFIG)

        with patch("builtins.input", return_value="y") as mock_input:
            call_command("filter_configs", "generate", overwrite=True)
        mock_input.assert_called_once()
        config.refresh_from_db()
        aliases = [node["node_alias"] for node in config.config["nodes"]]
        self.assertEqual(aliases, ["reference_node", "number_node"])
