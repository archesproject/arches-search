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


class EdtfAdvancedSearchFacetIntegrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        edtf = ExtendedDateFormat()

        cls.date_2020_01_10 = edtf.to_sortable_date(2020, 1, 10)
        cls.date_2020_01_12 = edtf.to_sortable_date(2020, 1, 12)
        cls.date_2020_01_13 = edtf.to_sortable_date(2020, 1, 13)
        cls.date_2020_01_14 = edtf.to_sortable_date(2020, 1, 14)
        cls.date_2020_01_15 = edtf.to_sortable_date(2020, 1, 15)
        cls.date_2020_01_18 = edtf.to_sortable_date(2020, 1, 18)
        cls.date_2020_01_20 = edtf.to_sortable_date(2020, 1, 20)
        cls.date_2020_01_21 = edtf.to_sortable_date(2020, 1, 21)
        cls.date_2020_01_25 = edtf.to_sortable_date(2020, 1, 25)
        cls.date_2020_01_31 = edtf.to_sortable_date(2020, 1, 31)
        cls.date_2020_02_01 = edtf.to_sortable_date(2020, 2, 1)

        ordered_suffix = uuid.uuid4().hex[:8]
        cls.ordered_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_ordered_{ordered_suffix}",
            isresource=True,
        )
        cls.ordered_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.ordered_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{ordered_suffix}",
            alias=f"value_{ordered_suffix}",
            datatype="edtf",
            graph=cls.ordered_graph,
            nodegroup=cls.ordered_nodegroup,
            istopnode=True,
        )
        cls.ordered_first_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.ordered_graph,
        )
        cls.ordered_first_resource.save()
        cls.ordered_second_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.ordered_graph,
        )
        cls.ordered_second_resource.save()
        cls.ordered_first_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.ordered_nodegroup,
            resourceinstance=cls.ordered_first_resource,
            data={str(cls.ordered_edtf_node.nodeid): "2020-01-20"},
            provisionaledits=None,
        )
        cls.ordered_first_tile.save()
        cls.ordered_second_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.ordered_nodegroup,
            resourceinstance=cls.ordered_second_resource,
            data={str(cls.ordered_edtf_node.nodeid): "2020-01-31"},
            provisionaledits=None,
        )
        cls.ordered_second_tile.save()

        overlap_suffix = uuid.uuid4().hex[:8]
        cls.overlap_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_overlap_{overlap_suffix}",
            isresource=True,
        )
        cls.overlap_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.overlap_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{overlap_suffix}",
            alias=f"value_{overlap_suffix}",
            datatype="edtf",
            graph=cls.overlap_graph,
            nodegroup=cls.overlap_nodegroup,
            istopnode=True,
        )
        cls.overlapping_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.overlap_graph,
        )
        cls.overlapping_resource.save()
        cls.non_overlapping_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.overlap_graph,
        )
        cls.non_overlapping_resource.save()
        cls.overlapping_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.overlap_nodegroup,
            resourceinstance=cls.overlapping_resource,
            data={str(cls.overlap_edtf_node.nodeid): "2020-01-15/2020-01-25"},
            provisionaledits=None,
        )
        cls.overlapping_tile.save()
        cls.non_overlapping_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.overlap_nodegroup,
            resourceinstance=cls.non_overlapping_resource,
            data={str(cls.overlap_edtf_node.nodeid): "2020-01-21/2020-01-31"},
            provisionaledits=None,
        )
        cls.non_overlapping_tile.save()

        during_suffix = uuid.uuid4().hex[:8]
        cls.during_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_during_{during_suffix}",
            isresource=True,
        )
        cls.during_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.during_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{during_suffix}",
            alias=f"value_{during_suffix}",
            datatype="edtf",
            graph=cls.during_graph,
            nodegroup=cls.during_nodegroup,
            istopnode=True,
        )
        cls.during_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.during_graph,
        )
        cls.during_resource.save()
        cls.not_during_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.during_graph,
        )
        cls.not_during_resource.save()
        cls.during_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.during_nodegroup,
            resourceinstance=cls.during_resource,
            data={str(cls.during_edtf_node.nodeid): "2020-01-12/2020-01-18"},
            provisionaledits=None,
        )
        cls.during_tile.save()
        cls.not_during_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.during_nodegroup,
            resourceinstance=cls.not_during_resource,
            data={str(cls.during_edtf_node.nodeid): "2020-01-10/2020-01-25"},
            provisionaledits=None,
        )
        cls.not_during_tile.save()

        contains_suffix = uuid.uuid4().hex[:8]
        cls.contains_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_contains_{contains_suffix}",
            isresource=True,
        )
        cls.contains_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.contains_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{contains_suffix}",
            alias=f"value_{contains_suffix}",
            datatype="edtf",
            graph=cls.contains_graph,
            nodegroup=cls.contains_nodegroup,
            istopnode=True,
        )
        cls.contains_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.contains_graph,
        )
        cls.contains_resource.save()
        cls.not_contains_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.contains_graph,
        )
        cls.not_contains_resource.save()
        cls.contains_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.contains_nodegroup,
            resourceinstance=cls.contains_resource,
            data={str(cls.contains_edtf_node.nodeid): "2020-01-10/2020-01-20"},
            provisionaledits=None,
        )
        cls.contains_tile.save()
        cls.not_contains_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.contains_nodegroup,
            resourceinstance=cls.not_contains_resource,
            data={str(cls.contains_edtf_node.nodeid): "2020-01-13/2020-01-14"},
            provisionaledits=None,
        )
        cls.not_contains_tile.save()

        starts_suffix = uuid.uuid4().hex[:8]
        cls.starts_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_starts_{starts_suffix}",
            isresource=True,
        )
        cls.starts_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.starts_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{starts_suffix}",
            alias=f"value_{starts_suffix}",
            datatype="edtf",
            graph=cls.starts_graph,
            nodegroup=cls.starts_nodegroup,
            istopnode=True,
        )
        cls.starts_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.starts_graph,
        )
        cls.starts_match_resource.save()
        cls.starts_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.starts_graph,
        )
        cls.starts_other_resource.save()
        cls.starts_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.starts_nodegroup,
            resourceinstance=cls.starts_match_resource,
            data={str(cls.starts_edtf_node.nodeid): "2020-01-10/2020-01-20"},
            provisionaledits=None,
        )
        cls.starts_match_tile.save()
        cls.starts_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.starts_nodegroup,
            resourceinstance=cls.starts_other_resource,
            data={str(cls.starts_edtf_node.nodeid): "2020-01-11/2020-01-20"},
            provisionaledits=None,
        )
        cls.starts_other_tile.save()

        finishes_suffix = uuid.uuid4().hex[:8]
        cls.finishes_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_finishes_{finishes_suffix}",
            isresource=True,
        )
        cls.finishes_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.finishes_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{finishes_suffix}",
            alias=f"value_{finishes_suffix}",
            datatype="edtf",
            graph=cls.finishes_graph,
            nodegroup=cls.finishes_nodegroup,
            istopnode=True,
        )
        cls.finishes_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.finishes_graph,
        )
        cls.finishes_match_resource.save()
        cls.finishes_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.finishes_graph,
        )
        cls.finishes_other_resource.save()
        cls.finishes_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.finishes_nodegroup,
            resourceinstance=cls.finishes_match_resource,
            data={str(cls.finishes_edtf_node.nodeid): "2020-01-10/2020-01-20"},
            provisionaledits=None,
        )
        cls.finishes_match_tile.save()
        cls.finishes_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.finishes_nodegroup,
            resourceinstance=cls.finishes_other_resource,
            data={str(cls.finishes_edtf_node.nodeid): "2020-01-10/2020-01-21"},
            provisionaledits=None,
        )
        cls.finishes_other_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        cls.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_presence_{presence_suffix}",
            isresource=True,
        )
        cls.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.presence_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="edtf",
            graph=cls.presence_graph,
            nodegroup=cls.presence_nodegroup,
            istopnode=True,
        )
        cls.resource_with_edtf = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_with_edtf.save()
        cls.resource_without_edtf = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_without_edtf.save()
        cls.tile_with_edtf = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_with_edtf,
            data={str(cls.presence_edtf_node.nodeid): "2020-01-20"},
            provisionaledits=None,
        )
        cls.tile_with_edtf.save()
        cls.tile_without_edtf = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_without_edtf,
            data={},
            provisionaledits=None,
        )
        cls.tile_without_edtf.save()

        call_command("db_index", "reindex_database")

    def test_equals_matches_the_same_interval(self):
        """This checks whether the equals facet returns the resource whose EDTF row should match the requested value."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_edtf_node.alias]
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

        self.assertEqual(result, {self.ordered_first_resource.resourceinstanceid})

    def test_not_equals_excludes_the_same_interval(self):
        """This checks whether the not equals facet returns the resource whose EDTF row should differ from the requested value."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_edtf_node.alias]
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

        self.assertEqual(result, {self.ordered_second_resource.resourceinstanceid})

    def test_less_than_matches_the_interval_before_the_threshold(self):
        """This checks whether the less than facet returns the resource whose EDTF row should sit before the requested threshold."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_edtf_node.alias]
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

        self.assertEqual(result, {self.ordered_first_resource.resourceinstanceid})

    def test_greater_than_matches_the_interval_after_the_threshold(self):
        """This checks whether the greater than facet returns the resource whose EDTF row should sit after the requested threshold."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_edtf_node.alias]
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

        self.assertEqual(result, {self.ordered_second_resource.resourceinstanceid})

    def test_less_than_or_equals_keeps_the_boundary_interval(self):
        """This checks whether the less than or equals facet includes the resource that should sit on the requested boundary."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_edtf_node.alias]
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

        self.assertEqual(result, {self.ordered_first_resource.resourceinstanceid})

    def test_greater_than_or_equals_keeps_the_boundary_interval(self):
        """This checks whether the greater than or equals facet includes the resource that should sit on the requested boundary."""
        payload = {
            "graph_slug": self.ordered_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.ordered_graph.slug, self.ordered_edtf_node.alias]
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

        self.assertEqual(result, {self.ordered_second_resource.resourceinstanceid})

    def test_overlaps_matches_the_interval_that_crosses_the_requested_window(self):
        """This checks whether the overlaps facet returns the resource whose EDTF range crosses into the requested window."""
        payload = {
            "graph_slug": self.overlap_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.overlap_graph.slug, self.overlap_edtf_node.alias]
                    ],
                    "operator": "OVERLAPS",
                    "operands": [
                        {"type": "LITERAL", "value": self.date_2020_01_10},
                        {"type": "LITERAL", "value": self.date_2020_01_20},
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

        self.assertEqual(result, {self.overlapping_resource.resourceinstanceid})

    def test_during_matches_the_interval_fully_inside_the_requested_window(self):
        """This checks whether the during facet returns the resource whose EDTF range sits fully inside the requested window."""
        payload = {
            "graph_slug": self.during_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.during_graph.slug, self.during_edtf_node.alias]],
                    "operator": "DURING",
                    "operands": [
                        {"type": "LITERAL", "value": self.date_2020_01_10},
                        {"type": "LITERAL", "value": self.date_2020_01_20},
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

        self.assertEqual(result, {self.during_resource.resourceinstanceid})

    def test_contains_matches_the_interval_that_wraps_the_requested_window(self):
        """This checks whether the contains facet returns the resource whose EDTF range wraps around the requested window."""
        payload = {
            "graph_slug": self.contains_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.contains_graph.slug, self.contains_edtf_node.alias]
                    ],
                    "operator": "CONTAINS",
                    "operands": [
                        {"type": "LITERAL", "value": self.date_2020_01_12},
                        {"type": "LITERAL", "value": self.date_2020_01_18},
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

        self.assertEqual(result, {self.contains_resource.resourceinstanceid})

    def test_starts_at_matches_the_interval_with_the_requested_start(self):
        """This checks whether the starts at facet returns the resource whose EDTF range starts on the requested day."""
        payload = {
            "graph_slug": self.starts_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.starts_graph.slug, self.starts_edtf_node.alias]],
                    "operator": "STARTS_AT",
                    "operands": [{"type": "LITERAL", "value": self.date_2020_01_10}],
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

        self.assertEqual(result, {self.starts_match_resource.resourceinstanceid})

    def test_finishes_at_matches_the_interval_with_the_requested_end(self):
        """This checks whether the finishes at facet returns the resource whose EDTF range ends on the requested day."""
        payload = {
            "graph_slug": self.finishes_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.finishes_graph.slug, self.finishes_edtf_node.alias]
                    ],
                    "operator": "FINISHES_AT",
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

        self.assertEqual(result, {self.finishes_match_resource.resourceinstanceid})

    def test_has_no_value_matches_the_resource_without_an_edtf_row(self):
        """This checks whether the has no value facet returns only the resource whose EDTF tile indexed no value at all."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.presence_graph.slug, self.presence_edtf_node.alias]
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

        self.assertEqual(result, {self.resource_without_edtf.resourceinstanceid})

    def test_has_any_value_matches_the_resource_with_an_edtf_row(self):
        """This checks whether the has any value facet returns only the resource whose EDTF tile indexed a real range value."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.presence_graph.slug, self.presence_edtf_node.alias]
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

        self.assertEqual(result, {self.resource_with_edtf.resourceinstanceid})
