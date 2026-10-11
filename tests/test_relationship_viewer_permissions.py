import uuid

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    ResourceXResource,
    TileModel,
)
from arches.app.utils.permission_backend import assign_perm

from arches_search.models.models import TermSearch

# python manage.py test tests.test_relationship_viewer_permissions --settings="tests.test_settings"
#
# Requires PERMISSION_FRAMEWORK to be set to
# arches_default_deny.ArchesDefaultDenyPermissionFramework (see settings.py).


class RelationshipViewerPermissionTest(TestCase):
    """
    The seed links to a readable neighbor, to a hidden resource, and, through a
    node the member may not read, to a secret neighbor. The hidden resource
    links on to a resource that is only reachable through it:

        seed ── link ──▶ neighbor
        seed ── link ──▶ hidden ── link ──▶ beyond
        seed ── secret link ──▶ secret neighbor

    The member may read every resource but the hidden one, and no node in the
    restricted nodegroup, so they should see only the seed and the neighbor.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="rv_perm_admin",
            password="password123",
            email="rv_perm_admin@example.com",
        )
        cls.member = User.objects.create_user(
            username="rv_perm_member", password="password123"
        )
        group = Group.objects.create(name="test_relationship_viewer_group")
        cls.member.groups.add(group)

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="test-relationship-viewer",
            isresource=True,
        )
        open_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(), cardinality="n"
        )
        cls.restricted_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(), cardinality="n"
        )
        link_node = cls._create_node("link", "resource-instance", open_nodegroup)
        secret_link_node = cls._create_node(
            "secret_link", "resource-instance", cls.restricted_nodegroup
        )
        cls._create_node("name", "string", open_nodegroup)
        cls._create_node("secret_note", "string", cls.restricted_nodegroup)

        cls.seed = cls._create_resource("Seed")
        cls.neighbor = cls._create_resource("Neighbor")
        cls.hidden = cls._create_resource("Hidden")
        cls.beyond = cls._create_resource("Beyond")
        cls.secret_neighbor = cls._create_resource("Secret Neighbor")

        cls._relate(cls.seed, cls.neighbor, link_node)
        cls._relate(cls.seed, cls.hidden, link_node)
        cls._relate(cls.hidden, cls.beyond, link_node)
        cls._relate(cls.seed, cls.secret_neighbor, secret_link_node)

        seed_tile = TileModel.objects.create(resourceinstance=cls.seed)
        for node_alias, value in (("name", "seed name"), ("secret_note", "classified")):
            TermSearch.objects.create(
                tileid=seed_tile,
                resourceinstanceid=cls.seed,
                graph_slug=cls.graph.slug,
                node_alias=node_alias,
                language="en",
                datatype="string",
                value=value,
            )

        for resource in (cls.seed, cls.neighbor, cls.beyond, cls.secret_neighbor):
            assign_perm("view_resourceinstance", group, resource)
        assign_perm("no_access_to_nodegroup", cls.member, cls.restricted_nodegroup)

    @classmethod
    def _create_node(cls, alias, datatype, nodegroup):
        return Node.objects.create(
            nodeid=uuid.uuid4(),
            name=alias,
            alias=alias,
            datatype=datatype,
            graph=cls.graph,
            nodegroup=nodegroup,
            istopnode=False,
        )

    @classmethod
    def _create_resource(cls, name):
        resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
            descriptors={"en": {"name": name}},
        )
        resource.save()
        return resource

    @classmethod
    def _relate(cls, from_resource, to_resource, node):
        now = timezone.now()
        ResourceXResource.objects.create(
            from_resource=from_resource,
            from_resource_graph=cls.graph,
            to_resource=to_resource,
            to_resource_graph=cls.graph,
            node=node,
            created=now,
            modified=now,
        )

    def _graph_as(self, user, *seeds, depth=2):
        self.client.force_login(user)
        response = self.client.get(
            reverse("relationship_viewer"),
            {
                "resource_ids": ",".join(
                    str(seed.resourceinstanceid) for seed in seeds
                ),
                "depth": depth,
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    @staticmethod
    def _ids(*resources):
        return {str(resource.resourceinstanceid) for resource in resources}

    @staticmethod
    def _node_ids(graph):
        return {node["id"] for node in graph["nodes"]}

    @staticmethod
    def _node(graph, resource):
        return next(
            node
            for node in graph["nodes"]
            if node["id"] == str(resource.resourceinstanceid)
        )

    def test_member_sees_only_readable_resources_through_readable_relations(self):
        graph = self._graph_as(self.member, self.seed)

        with self.subTest("nodes"):
            self.assertEqual(self._node_ids(graph), self._ids(self.seed, self.neighbor))
        with self.subTest("edges"):
            self.assertEqual(
                {(edge["source"], edge["target"]) for edge in graph["edges"]},
                {
                    (
                        str(self.seed.resourceinstanceid),
                        str(self.neighbor.resourceinstanceid),
                    )
                },
            )

    def test_related_count_ignores_hidden_resources_and_relations(self):
        with self.subTest("member"):
            graph = self._graph_as(self.member, self.seed)
            self.assertEqual(self._node(graph, self.seed)["related_count"], 1)
        with self.subTest("superuser"):
            graph = self._graph_as(self.admin, self.seed)
            self.assertEqual(self._node(graph, self.seed)["related_count"], 3)
