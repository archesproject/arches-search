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
    @classmethod
    def setUpTestData(cls):
        suffix = uuid.uuid4().hex[:8]
        cls.spatial_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_geojson_{suffix}",
            isresource=True,
        )
        cls.spatial_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.spatial_geojson_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{suffix}",
            alias=f"value_{suffix}",
            datatype="geojson-feature-collection",
            graph=cls.spatial_graph,
            nodegroup=cls.spatial_nodegroup,
            istopnode=True,
        )

        cls.matching_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.spatial_graph,
        )
        cls.matching_resource.save()
        cls.non_matching_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.spatial_graph,
        )
        cls.non_matching_resource.save()

        cls.matching_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.spatial_nodegroup,
            resourceinstance=cls.matching_resource,
            data={str(cls.spatial_geojson_node.nodeid): MATCHING_POLYGON_FC},
            provisionaledits=None,
        )
        cls.matching_tile.save()
        cls.non_matching_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.spatial_nodegroup,
            resourceinstance=cls.non_matching_resource,
            data={str(cls.spatial_geojson_node.nodeid): NON_MATCHING_POLYGON_FC},
            provisionaledits=None,
        )
        cls.non_matching_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        cls.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_geojson_presence_{presence_suffix}",
            isresource=True,
        )
        cls.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.presence_geojson_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="geojson-feature-collection",
            graph=cls.presence_graph,
            nodegroup=cls.presence_nodegroup,
            istopnode=True,
        )

        cls.resource_with_geojson = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_with_geojson.save()
        cls.resource_without_geojson = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_without_geojson.save()

        cls.tile_with_geojson = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_with_geojson,
            data={str(cls.presence_geojson_node.nodeid): MATCHING_POLYGON_FC},
            provisionaledits=None,
        )
        cls.tile_with_geojson.save()
        cls.tile_without_geojson = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_without_geojson,
            data={},
            provisionaledits=None,
        )
        cls.tile_without_geojson.save()

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
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.spatial_graph.slug,
                        "node_alias": self.spatial_geojson_node.alias,
                        "search_models": [],
                    },
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
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.spatial_graph.slug,
                        "node_alias": self.spatial_geojson_node.alias,
                        "search_models": [],
                    },
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
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.spatial_graph.slug,
                        "node_alias": self.spatial_geojson_node.alias,
                        "search_models": [],
                    },
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
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.spatial_graph.slug,
                        "node_alias": self.spatial_geojson_node.alias,
                        "search_models": [],
                    },
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
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.spatial_graph.slug,
                        "node_alias": self.spatial_geojson_node.alias,
                        "search_models": [],
                    },
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
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.presence_graph.slug,
                        "node_alias": self.presence_geojson_node.alias,
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
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.presence_graph.slug,
                        "node_alias": self.presence_geojson_node.alias,
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

        self.assertEqual(result, {self.resource_with_geojson.resourceinstanceid})
