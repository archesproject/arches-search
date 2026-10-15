import uuid

from django.contrib.auth.models import User
from django.test import TestCase

from arches.app.models.models import (
    CardModel,
    CardXNodeXWidget,
    GraphModel,
    Node,
    NodeGroup,
    Widget,
)
from arches.app.utils.permission_backend import assign_perm

from arches_search.utils.advanced_search.metadata.node_widget_labels_for_graph import (
    get_nodes_with_widget_labels_for_graph,
)
from arches_search.utils.readable_nodes import ReadableNodes

# python manage.py test tests.test_node_widget_labels_for_graph --settings="tests.test_settings"


class NodeWidgetLabelsForGraphTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="reader", password="reader")
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
        nodes = get_nodes_with_widget_labels_for_graph(
            self.graph.graphid, ReadableNodes(self.user)
        )
        return {node["id"]: node for node in nodes}

    def test_nodes_the_user_cannot_read_are_omitted(self):
        assign_perm("write_nodegroup", self.user, self.part_nodegroup)

        nodes_by_id = self._nodes_by_id()

        self.assertNotIn(str(self.part_name_content_node.nodeid), nodes_by_id)

    def test_nodes_under_an_unreadable_parent_are_omitted(self):
        detail_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(), parentnodegroup=self.part_nodegroup
        )
        Node.objects.create(
            nodeid=detail_nodegroup.nodegroupid,
            name="detail",
            alias="detail",
            datatype="semantic",
            graph=self.graph,
            nodegroup=detail_nodegroup,
            istopnode=False,
        )
        detail_content_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="detail_content",
            alias="detail_content",
            datatype="string",
            graph=self.graph,
            nodegroup=detail_nodegroup,
            istopnode=False,
        )
        detail_card = CardModel.objects.create(
            cardid=uuid.uuid4(),
            name="Detail",
            nodegroup=detail_nodegroup,
            graph=self.graph,
        )
        CardXNodeXWidget.objects.create(
            node=detail_content_node,
            card=detail_card,
            widget=self.widget,
            label="Detail content",
        )
        assign_perm("write_nodegroup", self.user, self.part_nodegroup)

        nodes_by_id = self._nodes_by_id()

        self.assertNotIn(str(detail_content_node.nodeid), nodes_by_id)
        self.assertNotIn(f"card-group:{self.part_nodegroup.nodegroupid}", nodes_by_id)

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
