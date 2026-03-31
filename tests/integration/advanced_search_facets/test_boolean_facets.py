import uuid

from django.core.management import call_command
from django.test import TestCase

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    TileModel,
)
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)


class BooleanAdvancedSearchFacetIntegrationTestCase(TestCase):
    def setUp(self):
        truth_suffix = uuid.uuid4().hex[:8]
        self.truth_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_boolean_truth_{truth_suffix}",
            isresource=True,
        )
        self.truth_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.truth_boolean_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{truth_suffix}",
            alias=f"value_{truth_suffix}",
            datatype="boolean",
            graph=self.truth_graph,
            nodegroup=self.truth_nodegroup,
            istopnode=True,
        )

        self.true_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.truth_graph,
        )
        self.true_resource.save()
        self.false_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.truth_graph,
        )
        self.false_resource.save()

        self.true_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.truth_nodegroup,
            resourceinstance=self.true_resource,
            data={str(self.truth_boolean_node.nodeid): True},
            provisionaledits=None,
        )
        self.true_tile.save()
        self.false_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.truth_nodegroup,
            resourceinstance=self.false_resource,
            data={str(self.truth_boolean_node.nodeid): False},
            provisionaledits=None,
        )
        self.false_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        self.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_boolean_presence_{presence_suffix}",
            isresource=True,
        )
        self.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.presence_boolean_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="boolean",
            graph=self.presence_graph,
            nodegroup=self.presence_nodegroup,
            istopnode=True,
        )

        self.resource_with_value = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.presence_graph,
        )
        self.resource_with_value.save()
        self.resource_without_value = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.presence_graph,
        )
        self.resource_without_value.save()

        self.tile_with_value = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.presence_nodegroup,
            resourceinstance=self.resource_with_value,
            data={str(self.presence_boolean_node.nodeid): True},
            provisionaledits=None,
        )
        self.tile_with_value.save()
        self.tile_without_value = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.presence_nodegroup,
            resourceinstance=self.resource_without_value,
            data={},
            provisionaledits=None,
        )
        self.tile_without_value.save()

        call_command("db_index", "reindex_database")

    def test_is_true_matches_the_resource_with_a_true_boolean_value(self):
        """This checks that the is true facet returns only the resource whose indexed boolean value is true."""
        payload = {
            "graph_slug": self.truth_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.truth_graph.slug, self.truth_boolean_node.alias]],
                    "operator": "IS_TRUE",
                    "operands": [{"type": "LITERAL", "value": True}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.true_resource.resourceinstanceid})

    def test_is_false_matches_the_resource_with_a_false_boolean_value(self):
        """This checks that the is false facet returns only the resource whose indexed boolean value is false."""
        payload = {
            "graph_slug": self.truth_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.truth_graph.slug, self.truth_boolean_node.alias]],
                    "operator": "IS_FALSE",
                    "operands": [{"type": "LITERAL", "value": True}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.false_resource.resourceinstanceid})

    def test_has_no_value_matches_only_the_resource_without_a_boolean_row(self):
        """This checks that the has no value facet returns only the resource whose boolean tile indexed no value at all."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.presence_graph.slug, self.presence_boolean_node.alias]
                    ],
                    "operator": "HAS_NO_VALUE",
                    "operands": [],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.resource_without_value.resourceinstanceid})

    def test_has_any_value_matches_only_the_resource_with_a_boolean_row(self):
        """This checks that the has any value facet returns only the resource whose boolean tile indexed a real value."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.presence_graph.slug, self.presence_boolean_node.alias]
                    ],
                    "operator": "HAS_ANY_VALUE",
                    "operands": [],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.resource_with_value.resourceinstanceid})
