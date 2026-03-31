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

# Resource polygon: 2×2 square from (0,0) to (2,2)
MATCHING_POLYGON_FC = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]]],
            },
            "properties": {},
        }
    ],
}

# Resource polygon far away from all search operands
NON_MATCHING_POLYGON_FC = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[10, 10], [10, 12], [12, 12], [12, 10], [10, 10]]],
            },
            "properties": {},
        }
    ],
}


class GeojsonFeatureCollectionAdvancedSearchFacetIntegrationTestCase(TestCase):
    def setUp(self):
        suffix = uuid.uuid4().hex[:8]
        self.spatial_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_geojson_{suffix}",
            isresource=True,
        )
        self.spatial_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.spatial_geojson_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{suffix}",
            alias=f"value_{suffix}",
            datatype="geojson-feature-collection",
            graph=self.spatial_graph,
            nodegroup=self.spatial_nodegroup,
            istopnode=True,
        )

        self.matching_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.spatial_graph,
        )
        self.matching_resource.save()
        self.non_matching_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.spatial_graph,
        )
        self.non_matching_resource.save()

        self.matching_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.spatial_nodegroup,
            resourceinstance=self.matching_resource,
            data={str(self.spatial_geojson_node.nodeid): MATCHING_POLYGON_FC},
            provisionaledits=None,
        )
        self.matching_tile.save()
        self.non_matching_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.spatial_nodegroup,
            resourceinstance=self.non_matching_resource,
            data={str(self.spatial_geojson_node.nodeid): NON_MATCHING_POLYGON_FC},
            provisionaledits=None,
        )
        self.non_matching_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        self.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_geojson_presence_{presence_suffix}",
            isresource=True,
        )
        self.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.presence_geojson_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="geojson-feature-collection",
            graph=self.presence_graph,
            nodegroup=self.presence_nodegroup,
            istopnode=True,
        )

        self.resource_with_geojson = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.presence_graph,
        )
        self.resource_with_geojson.save()
        self.resource_without_geojson = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.presence_graph,
        )
        self.resource_without_geojson.save()

        self.tile_with_geojson = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.presence_nodegroup,
            resourceinstance=self.resource_with_geojson,
            data={str(self.presence_geojson_node.nodeid): MATCHING_POLYGON_FC},
            provisionaledits=None,
        )
        self.tile_with_geojson.save()
        self.tile_without_geojson = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.presence_nodegroup,
            resourceinstance=self.resource_without_geojson,
            data={},
            provisionaledits=None,
        )
        self.tile_without_geojson.save()

        call_command("db_index", "reindex_database")

    def test_geo_contains_with_point_finds_the_polygon_that_contains_the_point(self):
        """GEO_CONTAINS returns only the resource whose stored polygon contains the search point."""
        payload = {
            "graph_slug": self.spatial_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.spatial_graph.slug, self.spatial_geojson_node.alias]
                    ],
                    "operator": "GEO_CONTAINS",
                    "operands": [
                        {
                            "type": "GEO_LITERAL",
                            "value": {"type": "Point", "coordinates": [1, 1]},
                        }
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

        self.assertEqual(result, {self.matching_resource.resourceinstanceid})

    def test_geo_contains_with_line_finds_the_polygon_that_contains_the_line(self):
        """GEO_CONTAINS returns only the resource whose stored polygon contains the search line."""
        payload = {
            "graph_slug": self.spatial_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.spatial_graph.slug, self.spatial_geojson_node.alias]
                    ],
                    "operator": "GEO_CONTAINS",
                    "operands": [
                        {
                            "type": "GEO_LITERAL",
                            "value": {
                                "type": "LineString",
                                "coordinates": [[0, 0], [1, 1]],
                            },
                        }
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

        self.assertEqual(result, {self.matching_resource.resourceinstanceid})

    def test_geo_contains_with_polygon_finds_the_polygon_that_contains_the_other_polygon(
        self,
    ):
        """GEO_CONTAINS returns only the resource whose stored polygon contains the smaller search polygon."""
        payload = {
            "graph_slug": self.spatial_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.spatial_graph.slug, self.spatial_geojson_node.alias]
                    ],
                    "operator": "GEO_CONTAINS",
                    "operands": [
                        {
                            "type": "GEO_LITERAL",
                            "value": {
                                "type": "Polygon",
                                "coordinates": [
                                    [[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]
                                ],
                            },
                        }
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

        self.assertEqual(result, {self.matching_resource.resourceinstanceid})

    def test_geo_intersects_finds_the_polygon_that_overlaps_the_search_area(self):
        """GEO_INTERSECTS returns only the resource whose stored polygon overlaps the search geometry."""
        payload = {
            "graph_slug": self.spatial_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.spatial_graph.slug, self.spatial_geojson_node.alias]
                    ],
                    "operator": "GEO_INTERSECTS",
                    "operands": [
                        {
                            "type": "GEO_LITERAL",
                            "value": {
                                "type": "Polygon",
                                "coordinates": [
                                    [[1, 1], [1, 3], [3, 3], [3, 1], [1, 1]]
                                ],
                            },
                        }
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

        self.assertEqual(result, {self.matching_resource.resourceinstanceid})

    def test_geo_within_finds_the_polygon_that_lies_inside_the_search_area(self):
        """GEO_WITHIN returns only the resource whose stored polygon is fully inside the large search polygon."""
        payload = {
            "graph_slug": self.spatial_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.spatial_graph.slug, self.spatial_geojson_node.alias]
                    ],
                    "operator": "GEO_WITHIN",
                    "operands": [
                        {
                            "type": "GEO_LITERAL",
                            "value": {
                                "type": "Polygon",
                                "coordinates": [
                                    [[-1, -1], [-1, 3], [3, 3], [3, -1], [-1, -1]]
                                ],
                            },
                        }
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

        self.assertEqual(result, {self.matching_resource.resourceinstanceid})

    def test_has_no_value_matches_the_resource_without_a_geojson_row(self):
        """HAS_NO_VALUE returns only the resource with no GeometrySearch row."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.presence_graph.slug, self.presence_geojson_node.alias]
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

        self.assertEqual(result, {self.resource_without_geojson.resourceinstanceid})

    def test_has_any_value_matches_the_resource_with_a_geojson_row(self):
        """HAS_ANY_VALUE returns only the resource that has a GeometrySearch row."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.presence_graph.slug, self.presence_geojson_node.alias]
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

        self.assertEqual(result, {self.resource_with_geojson.resourceinstanceid})
