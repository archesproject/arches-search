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


class NumberAdvancedSearchFacetIntegrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        ordered_suffix = uuid.uuid4().hex[:8]
        cls.ordered_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_number_ordered_{ordered_suffix}",
            isresource=True,
        )
        cls.ordered_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.ordered_number_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{ordered_suffix}",
            alias=f"value_{ordered_suffix}",
            datatype="number",
            graph=cls.ordered_graph,
            nodegroup=cls.ordered_nodegroup,
            istopnode=True,
        )

        cls.lower_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.ordered_graph,
        )
        cls.lower_resource.save()
        cls.higher_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.ordered_graph,
        )
        cls.higher_resource.save()

        cls.lower_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.ordered_nodegroup,
            resourceinstance=cls.lower_resource,
            data={str(cls.ordered_number_node.nodeid): 20},
            provisionaledits=None,
        )
        cls.lower_tile.save()
        cls.higher_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.ordered_nodegroup,
            resourceinstance=cls.higher_resource,
            data={str(cls.ordered_number_node.nodeid): 31},
            provisionaledits=None,
        )
        cls.higher_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        cls.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_number_presence_{presence_suffix}",
            isresource=True,
        )
        cls.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.presence_number_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="number",
            graph=cls.presence_graph,
            nodegroup=cls.presence_nodegroup,
            istopnode=True,
        )

        cls.resource_with_value = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_with_value.save()
        cls.resource_without_value = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_without_value.save()

        cls.tile_with_value = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_with_value,
            data={str(cls.presence_number_node.nodeid): 10},
            provisionaledits=None,
        )
        cls.tile_with_value.save()
        cls.tile_without_value = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_without_value,
            data={},
            provisionaledits=None,
        )
        cls.tile_without_value.save()

        call_command("db_index", "reindex_database")

    def test_equals_matches_the_same_number(self):
        """This checks that the equals facet returns only the resource whose indexed number exactly matches the requested value."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.ordered_graph.slug,
                        "node_alias": self.ordered_number_node.alias,
                        "search_models": [],
                    },
                    "operator": "EQUALS",
                    "operands": [{"type": "LITERAL", "value": 20}],
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

        self.assertEqual(result, {self.lower_resource.resourceinstanceid})

    def test_not_equals_drops_the_same_number(self):
        """This checks that the not equals facet returns only the resource whose indexed number is different from the requested value."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.ordered_graph.slug,
                        "node_alias": self.ordered_number_node.alias,
                        "search_models": [],
                    },
                    "operator": "NOT_EQUALS",
                    "operands": [{"type": "LITERAL", "value": 20}],
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

        self.assertEqual(result, {self.higher_resource.resourceinstanceid})

    def test_less_than_matches_the_smaller_number(self):
        """This checks that the less than facet returns only the resource whose indexed number is below the requested threshold."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.ordered_graph.slug,
                        "node_alias": self.ordered_number_node.alias,
                        "search_models": [],
                    },
                    "operator": "LESS_THAN",
                    "operands": [{"type": "LITERAL", "value": 31}],
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

        self.assertEqual(result, {self.lower_resource.resourceinstanceid})

    def test_greater_than_matches_the_larger_number(self):
        """This checks that the greater than facet returns only the resource whose indexed number is above the requested threshold."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.ordered_graph.slug,
                        "node_alias": self.ordered_number_node.alias,
                        "search_models": [],
                    },
                    "operator": "GREATER_THAN",
                    "operands": [{"type": "LITERAL", "value": 20}],
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

        self.assertEqual(result, {self.higher_resource.resourceinstanceid})

    def test_less_than_or_equals_keeps_the_boundary_value(self):
        """This checks that the less than or equals facet includes the resource whose indexed number sits exactly on the boundary."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.ordered_graph.slug,
                        "node_alias": self.ordered_number_node.alias,
                        "search_models": [],
                    },
                    "operator": "LESS_THAN_OR_EQUALS",
                    "operands": [{"type": "LITERAL", "value": 20}],
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

        self.assertEqual(result, {self.lower_resource.resourceinstanceid})

    def test_greater_than_or_equals_keeps_the_boundary_value(self):
        """This checks that the greater than or equals facet includes the resource whose indexed number sits exactly on the boundary."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.ordered_graph.slug,
                        "node_alias": self.ordered_number_node.alias,
                        "search_models": [],
                    },
                    "operator": "GREATER_THAN_OR_EQUALS",
                    "operands": [{"type": "LITERAL", "value": 31}],
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

        self.assertEqual(result, {self.higher_resource.resourceinstanceid})

    def test_between_matches_the_value_inside_the_range(self):
        """This checks that the between facet returns only the resource whose indexed number falls inside the requested range."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.ordered_graph.slug,
                        "node_alias": self.ordered_number_node.alias,
                        "search_models": [],
                    },
                    "operator": "BETWEEN",
                    "operands": [
                        {"type": "LITERAL", "value": 10},
                        {"type": "LITERAL", "value": 30},
                    ],
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

        self.assertEqual(result, {self.lower_resource.resourceinstanceid})

    def test_not_between_matches_the_value_outside_the_range(self):
        """This checks that the not between facet returns only the resource whose indexed number falls outside the requested range."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.ordered_graph.slug,
                        "node_alias": self.ordered_number_node.alias,
                        "search_models": [],
                    },
                    "operator": "NOT_BETWEEN",
                    "operands": [
                        {"type": "LITERAL", "value": 10},
                        {"type": "LITERAL", "value": 30},
                    ],
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

        self.assertEqual(result, {self.higher_resource.resourceinstanceid})

    def test_has_no_value_matches_the_resource_without_a_number_row(self):
        """This checks that the has no value facet returns only the resource whose number tile indexed no value at all."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.presence_graph.slug,
                        "node_alias": self.presence_number_node.alias,
                        "search_models": [],
                    },
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

    def test_has_any_value_matches_the_resource_with_a_number_row(self):
        """This checks that the has any value facet returns only the resource whose number tile indexed a real value."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.presence_graph.slug,
                        "node_alias": self.presence_number_node.alias,
                        "search_models": [],
                    },
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
