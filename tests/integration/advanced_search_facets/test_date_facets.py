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
from arches.app.utils.date_utils import ExtendedDateFormat
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)


class DateAdvancedSearchFacetIntegrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        edtf = ExtendedDateFormat()

        cls.date_2020_01_09 = edtf.to_sortable_date(2020, 1, 9)
        cls.date_2020_01_10 = edtf.to_sortable_date(2020, 1, 10)
        cls.date_2020_01_15 = edtf.to_sortable_date(2020, 1, 15)
        cls.date_2020_01_20 = edtf.to_sortable_date(2020, 1, 20)
        cls.date_2020_01_25 = edtf.to_sortable_date(2020, 1, 25)
        cls.date_2020_01_31 = edtf.to_sortable_date(2020, 1, 31)

        ordered_suffix = uuid.uuid4().hex[:8]
        cls.ordered_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_date_ordered_{ordered_suffix}",
            isresource=True,
        )
        cls.ordered_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.ordered_date_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{ordered_suffix}",
            alias=f"value_{ordered_suffix}",
            datatype="date",
            graph=cls.ordered_graph,
            nodegroup=cls.ordered_nodegroup,
            istopnode=True,
        )

        cls.earlier_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.ordered_graph,
        )
        cls.earlier_resource.save()
        cls.later_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.ordered_graph,
        )
        cls.later_resource.save()

        cls.earlier_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.ordered_nodegroup,
            resourceinstance=cls.earlier_resource,
            data={str(cls.ordered_date_node.nodeid): "2020-01-20"},
            provisionaledits=None,
        )
        cls.earlier_tile.save()
        cls.later_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.ordered_nodegroup,
            resourceinstance=cls.later_resource,
            data={str(cls.ordered_date_node.nodeid): "2020-01-31"},
            provisionaledits=None,
        )
        cls.later_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        cls.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_date_presence_{presence_suffix}",
            isresource=True,
        )
        cls.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.presence_date_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="date",
            graph=cls.presence_graph,
            nodegroup=cls.presence_nodegroup,
            istopnode=True,
        )

        cls.resource_with_date = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_with_date.save()
        cls.resource_without_date = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_without_date.save()

        cls.tile_with_date = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_with_date,
            data={str(cls.presence_date_node.nodeid): "2020-01-20"},
            provisionaledits=None,
        )
        cls.tile_with_date.save()
        cls.tile_without_date = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_without_date,
            data={},
            provisionaledits=None,
        )
        cls.tile_without_date.save()

        call_command("db_index", "reindex_database")

    def test_equals_matches_the_same_date(self):
        """This checks that the equals facet returns only the resource whose indexed date exactly matches the requested day."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_date_node.alias]
                    ],
                    "operator": "EQUALS",
                    "operands": [{"type": "LITERAL", "value": self.date_2020_01_20}],
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

        self.assertEqual(result, {self.earlier_resource.resourceinstanceid})

    def test_not_equals_drops_the_same_date(self):
        """This checks that the not equals facet returns only the resource whose indexed date is different from the requested day."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_date_node.alias]
                    ],
                    "operator": "NOT_EQUALS",
                    "operands": [{"type": "LITERAL", "value": self.date_2020_01_20}],
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

        self.assertEqual(result, {self.later_resource.resourceinstanceid})

    def test_less_than_matches_the_smaller_date(self):
        """This checks that the less than facet returns only the resource whose indexed date is before the requested day."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_date_node.alias]
                    ],
                    "operator": "LESS_THAN",
                    "operands": [{"type": "LITERAL", "value": self.date_2020_01_31}],
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

        self.assertEqual(result, {self.earlier_resource.resourceinstanceid})

    def test_greater_than_matches_the_larger_date(self):
        """This checks that the greater than facet returns only the resource whose indexed date is after the requested day."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_date_node.alias]
                    ],
                    "operator": "GREATER_THAN",
                    "operands": [{"type": "LITERAL", "value": self.date_2020_01_20}],
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

        self.assertEqual(result, {self.later_resource.resourceinstanceid})

    def test_less_than_or_equals_keeps_the_boundary_value(self):
        """This checks that the less than or equals facet includes the resource whose indexed date sits exactly on the boundary."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_date_node.alias]
                    ],
                    "operator": "LESS_THAN_OR_EQUALS",
                    "operands": [{"type": "LITERAL", "value": self.date_2020_01_20}],
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

        self.assertEqual(result, {self.earlier_resource.resourceinstanceid})

    def test_greater_than_or_equals_keeps_the_boundary_value(self):
        """This checks that the greater than or equals facet includes the resource whose indexed date sits exactly on the boundary."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_date_node.alias]
                    ],
                    "operator": "GREATER_THAN_OR_EQUALS",
                    "operands": [{"type": "LITERAL", "value": self.date_2020_01_31}],
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

        self.assertEqual(result, {self.later_resource.resourceinstanceid})

    def test_between_matches_the_value_inside_the_range(self):
        """This checks that the between facet returns only the resource whose indexed date falls inside the requested window."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_date_node.alias]
                    ],
                    "operator": "BETWEEN",
                    "operands": [
                        {"type": "LITERAL", "value": self.date_2020_01_15},
                        {"type": "LITERAL", "value": self.date_2020_01_25},
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

        self.assertEqual(result, {self.earlier_resource.resourceinstanceid})

    def test_not_between_matches_the_value_outside_the_range(self):
        """This checks that the not between facet returns only the resource whose indexed date falls outside the requested window."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_date_node.alias]
                    ],
                    "operator": "NOT_BETWEEN",
                    "operands": [
                        {"type": "LITERAL", "value": self.date_2020_01_15},
                        {"type": "LITERAL", "value": self.date_2020_01_25},
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

        self.assertEqual(result, {self.later_resource.resourceinstanceid})

    def test_has_no_value_matches_the_resource_without_a_date_row(self):
        """This checks that the has no value facet returns only the resource whose date tile indexed no value at all."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.presence_graph.slug, self.presence_date_node.alias]
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

        self.assertEqual(result, {self.resource_without_date.resourceinstanceid})

    def test_has_any_value_matches_the_resource_with_a_date_row(self):
        """This checks that the has any value facet returns only the resource whose date tile indexed a real value."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.presence_graph.slug, self.presence_date_node.alias]
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

        self.assertEqual(result, {self.resource_with_date.resourceinstanceid})
