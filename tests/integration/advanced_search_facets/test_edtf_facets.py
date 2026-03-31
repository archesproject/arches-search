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
    def setUp(self):
        edtf = ExtendedDateFormat()

        self.date_2020_01_10 = edtf.to_sortable_date(2020, 1, 10)
        self.date_2020_01_12 = edtf.to_sortable_date(2020, 1, 12)
        self.date_2020_01_13 = edtf.to_sortable_date(2020, 1, 13)
        self.date_2020_01_14 = edtf.to_sortable_date(2020, 1, 14)
        self.date_2020_01_15 = edtf.to_sortable_date(2020, 1, 15)
        self.date_2020_01_18 = edtf.to_sortable_date(2020, 1, 18)
        self.date_2020_01_20 = edtf.to_sortable_date(2020, 1, 20)
        self.date_2020_01_21 = edtf.to_sortable_date(2020, 1, 21)
        self.date_2020_01_25 = edtf.to_sortable_date(2020, 1, 25)
        self.date_2020_01_31 = edtf.to_sortable_date(2020, 1, 31)
        self.date_2020_02_01 = edtf.to_sortable_date(2020, 2, 1)

        ordered_suffix = uuid.uuid4().hex[:8]
        self.ordered_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_ordered_{ordered_suffix}",
            isresource=True,
        )
        self.ordered_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.ordered_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{ordered_suffix}",
            alias=f"value_{ordered_suffix}",
            datatype="edtf",
            graph=self.ordered_graph,
            nodegroup=self.ordered_nodegroup,
            istopnode=True,
        )
        self.ordered_first_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.ordered_graph,
        )
        self.ordered_first_resource.save()
        self.ordered_second_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.ordered_graph,
        )
        self.ordered_second_resource.save()
        self.ordered_first_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.ordered_nodegroup,
            resourceinstance=self.ordered_first_resource,
            data={str(self.ordered_edtf_node.nodeid): "2020-01-20"},
            provisionaledits=None,
        )
        self.ordered_first_tile.save()
        self.ordered_second_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.ordered_nodegroup,
            resourceinstance=self.ordered_second_resource,
            data={str(self.ordered_edtf_node.nodeid): "2020-01-31"},
            provisionaledits=None,
        )
        self.ordered_second_tile.save()

        overlap_suffix = uuid.uuid4().hex[:8]
        self.overlap_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_overlap_{overlap_suffix}",
            isresource=True,
        )
        self.overlap_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.overlap_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{overlap_suffix}",
            alias=f"value_{overlap_suffix}",
            datatype="edtf",
            graph=self.overlap_graph,
            nodegroup=self.overlap_nodegroup,
            istopnode=True,
        )
        self.overlapping_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.overlap_graph,
        )
        self.overlapping_resource.save()
        self.non_overlapping_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.overlap_graph,
        )
        self.non_overlapping_resource.save()
        self.overlapping_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.overlap_nodegroup,
            resourceinstance=self.overlapping_resource,
            data={str(self.overlap_edtf_node.nodeid): "2020-01-15/2020-01-25"},
            provisionaledits=None,
        )
        self.overlapping_tile.save()
        self.non_overlapping_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.overlap_nodegroup,
            resourceinstance=self.non_overlapping_resource,
            data={str(self.overlap_edtf_node.nodeid): "2020-01-21/2020-01-31"},
            provisionaledits=None,
        )
        self.non_overlapping_tile.save()

        during_suffix = uuid.uuid4().hex[:8]
        self.during_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_during_{during_suffix}",
            isresource=True,
        )
        self.during_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.during_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{during_suffix}",
            alias=f"value_{during_suffix}",
            datatype="edtf",
            graph=self.during_graph,
            nodegroup=self.during_nodegroup,
            istopnode=True,
        )
        self.during_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.during_graph,
        )
        self.during_resource.save()
        self.not_during_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.during_graph,
        )
        self.not_during_resource.save()
        self.during_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.during_nodegroup,
            resourceinstance=self.during_resource,
            data={str(self.during_edtf_node.nodeid): "2020-01-12/2020-01-18"},
            provisionaledits=None,
        )
        self.during_tile.save()
        self.not_during_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.during_nodegroup,
            resourceinstance=self.not_during_resource,
            data={str(self.during_edtf_node.nodeid): "2020-01-10/2020-01-25"},
            provisionaledits=None,
        )
        self.not_during_tile.save()

        contains_suffix = uuid.uuid4().hex[:8]
        self.contains_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_contains_{contains_suffix}",
            isresource=True,
        )
        self.contains_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.contains_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{contains_suffix}",
            alias=f"value_{contains_suffix}",
            datatype="edtf",
            graph=self.contains_graph,
            nodegroup=self.contains_nodegroup,
            istopnode=True,
        )
        self.contains_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.contains_graph,
        )
        self.contains_resource.save()
        self.not_contains_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.contains_graph,
        )
        self.not_contains_resource.save()
        self.contains_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.contains_nodegroup,
            resourceinstance=self.contains_resource,
            data={str(self.contains_edtf_node.nodeid): "2020-01-10/2020-01-20"},
            provisionaledits=None,
        )
        self.contains_tile.save()
        self.not_contains_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.contains_nodegroup,
            resourceinstance=self.not_contains_resource,
            data={str(self.contains_edtf_node.nodeid): "2020-01-13/2020-01-14"},
            provisionaledits=None,
        )
        self.not_contains_tile.save()

        starts_suffix = uuid.uuid4().hex[:8]
        self.starts_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_starts_{starts_suffix}",
            isresource=True,
        )
        self.starts_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.starts_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{starts_suffix}",
            alias=f"value_{starts_suffix}",
            datatype="edtf",
            graph=self.starts_graph,
            nodegroup=self.starts_nodegroup,
            istopnode=True,
        )
        self.starts_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.starts_graph,
        )
        self.starts_match_resource.save()
        self.starts_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.starts_graph,
        )
        self.starts_other_resource.save()
        self.starts_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.starts_nodegroup,
            resourceinstance=self.starts_match_resource,
            data={str(self.starts_edtf_node.nodeid): "2020-01-10/2020-01-20"},
            provisionaledits=None,
        )
        self.starts_match_tile.save()
        self.starts_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.starts_nodegroup,
            resourceinstance=self.starts_other_resource,
            data={str(self.starts_edtf_node.nodeid): "2020-01-11/2020-01-20"},
            provisionaledits=None,
        )
        self.starts_other_tile.save()

        finishes_suffix = uuid.uuid4().hex[:8]
        self.finishes_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_finishes_{finishes_suffix}",
            isresource=True,
        )
        self.finishes_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.finishes_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{finishes_suffix}",
            alias=f"value_{finishes_suffix}",
            datatype="edtf",
            graph=self.finishes_graph,
            nodegroup=self.finishes_nodegroup,
            istopnode=True,
        )
        self.finishes_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.finishes_graph,
        )
        self.finishes_match_resource.save()
        self.finishes_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.finishes_graph,
        )
        self.finishes_other_resource.save()
        self.finishes_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.finishes_nodegroup,
            resourceinstance=self.finishes_match_resource,
            data={str(self.finishes_edtf_node.nodeid): "2020-01-10/2020-01-20"},
            provisionaledits=None,
        )
        self.finishes_match_tile.save()
        self.finishes_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.finishes_nodegroup,
            resourceinstance=self.finishes_other_resource,
            data={str(self.finishes_edtf_node.nodeid): "2020-01-10/2020-01-21"},
            provisionaledits=None,
        )
        self.finishes_other_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        self.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_edtf_presence_{presence_suffix}",
            isresource=True,
        )
        self.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.presence_edtf_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="edtf",
            graph=self.presence_graph,
            nodegroup=self.presence_nodegroup,
            istopnode=True,
        )
        self.resource_with_edtf = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.presence_graph,
        )
        self.resource_with_edtf.save()
        self.resource_without_edtf = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.presence_graph,
        )
        self.resource_without_edtf.save()
        self.tile_with_edtf = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.presence_nodegroup,
            resourceinstance=self.resource_with_edtf,
            data={str(self.presence_edtf_node.nodeid): "2020-01-20"},
            provisionaledits=None,
        )
        self.tile_with_edtf.save()
        self.tile_without_edtf = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.presence_nodegroup,
            resourceinstance=self.resource_without_edtf,
            data={},
            provisionaledits=None,
        )
        self.tile_without_edtf.save()

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
