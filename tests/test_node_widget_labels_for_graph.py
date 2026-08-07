import uuid

from django.test import TestCase

from arches.app.models.models import (
    CardModel,
    CardXNodeXWidget,
    GraphModel,
    Node,
    NodeGroup,
    Widget,
)

from arches_search.utils.node_widget_labels_for_graph import (
    get_nodes_with_widget_labels_for_graph,
)

# python manage.py test tests.test_node_widget_labels_for_graph --settings="tests.test_settings"


class NodeWidgetLabelsForGraphTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="Test Graph",
            slug="test-node-widget-labels",
            isresource=True,
        )

        cls.part_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(), parentnodegroup=None
        )

        cls.has_part_node = Node.objects.create(
            nodeid=cls.part_nodegroup.nodegroupid,
            name="has_part",
            alias="has_part",
            datatype="semantic",
            graph=cls.graph,
            nodegroup=cls.part_nodegroup,
            istopnode=False,
        )
        cls.part_name_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="part_Name",
            alias="part_name",
            datatype="semantic",
            graph=cls.graph,
            nodegroup=cls.part_nodegroup,
            istopnode=False,
        )
        cls.part_name_content_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="part_Name_content",
            alias="part_name_content",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.part_nodegroup,
            istopnode=False,
        )

        cls.part_card = CardModel.objects.create(
            cardid=uuid.uuid4(),
            name="Part",
            nodegroup=cls.part_nodegroup,
            graph=cls.graph,
        )

        cls.widget = Widget.objects.first()
        CardXNodeXWidget.objects.create(
            node=cls.part_name_content_node,
            card=cls.part_card,
            widget=cls.widget,
            label="Content",
        )

    def _nodes_by_id(self):
        nodes = get_nodes_with_widget_labels_for_graph(self.graph.graphid)
        return {node["id"]: node for node in nodes}

    def test_widget_less_non_root_node_is_omitted(self):
        nodes_by_id = self._nodes_by_id()

        self.assertNotIn(str(self.part_name_node.nodeid), nodes_by_id)

    def test_widget_backed_leaf_is_selectable_and_parented_to_card(self):
        nodes_by_id = self._nodes_by_id()

        leaf = nodes_by_id[str(self.part_name_content_node.nodeid)]
        self.assertNotIn("selectable", leaf)
        self.assertEqual(leaf["card_x_node_x_widget_label"], "Content")
        self.assertEqual(leaf["semantic_parent_id"], str(self.has_part_node.nodeid))

    def test_widget_less_nodegroup_root_is_not_selectable(self):
        nodes_by_id = self._nodes_by_id()

        card_header = nodes_by_id[str(self.has_part_node.nodeid)]
        self.assertEqual(card_header["selectable"], False)
