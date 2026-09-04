"""
Geometry and date filtering as SEARCH_MODELS clauses.

These replaced node_agnostic_filters' GEO_INTERSECTS and DATE_RANGE entries.
Both were only ever sent with max_hops=0, which reduced the old relationship
expansion to "resources of this graph that matched" -- a plain graph-scoped
clause -- so the move cost nothing.

Every expected set below was established by asserting equality with the filter
it replaced, on this fixture, before that filter was deleted. They are the
record of that parity.

Term search is not here: it is sent with max_hops=2 and its cross-resource
expansion is not clause-shaped, so it remains its own payload key.

python manage.py test tests.integration.utils.advanced_search.test_geo_and_date_search_model_clauses --settings="tests.test_settings"
"""

import uuid

from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase

from arches.app.models.models import GraphModel, ResourceInstance, TileModel

from arches_search.models.models import DateRangeSearch, DateSearch, GeometrySearch
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)

GRAPH_SLUG = "parity-test-graph"

# The window both forms are asked about.
WINDOW_FROM = "1900-01-01"
WINDOW_TO = "2000-01-01"

# A box around (10, 10), well clear of (50, 50).
SEARCH_FEATURE_COLLECTION = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[9.0, 9.0], [11.0, 9.0], [11.0, 11.0], [9.0, 11.0], [9.0, 9.0]]
                ],
            },
        }
    ],
}


def encode_date(date_string):
    normalized, _ = DateSearch.normalize_operands(
        [{"type": "LITERAL", "value": date_string}], datatype_name="date"
    )
    return normalized[0]["value"]


class GeoAndDateSearchModelClauseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="Parity",
            slug=GRAPH_SLUG,
            isresource=True,
            is_active=True,
            iconclass="fa fa-check",
        )

        cls.inside_box = cls._resource()
        cls.outside_box = cls._resource()
        cls._add_point(cls.inside_box, 10.0, 10.0)
        cls._add_point(cls.outside_box, 50.0, 50.0)

        # ~35km east of the box edge: outside it, inside a 50km buffer.
        cls.just_outside_box = cls._resource()
        cls._add_point(cls.just_outside_box, 11.3, 10.0)

        # Far from the box, but inside a second drawn feature.
        cls.inside_second_feature = cls._resource()
        cls._add_point(cls.inside_second_feature, 30.0, 30.0)

        cls.date_in_window = cls._resource()
        cls.date_outside_window = cls._resource()
        cls._add_date(cls.date_in_window, "1950-01-01")
        cls._add_date(cls.date_outside_window, "1800-01-01")

        # A range straddling the window's start, and one entirely before it.
        cls.range_overlapping = cls._resource()
        cls.range_disjoint = cls._resource()
        cls._add_date_range(cls.range_overlapping, "1890-01-01", "1910-01-01")
        cls._add_date_range(cls.range_disjoint, "1700-01-01", "1750-01-01")

    @classmethod
    def _resource(cls):
        return ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph
        )

    @classmethod
    def _add_point(cls, resource, lon, lat):
        GeometrySearch.objects.create(
            tileid=TileModel.objects.create(resourceinstance=resource),
            resourceinstanceid=resource,
            graph_slug=GRAPH_SLUG,
            node_alias="location",
            datatype="geojson-feature-collection",
            geom=GEOSGeometry(f"POINT({lon} {lat})", srid=4326),
        )

    @classmethod
    def _add_date(cls, resource, date_string):
        DateSearch.objects.create(
            tileid=TileModel.objects.create(resourceinstance=resource),
            resourceinstanceid=resource,
            graph_slug=GRAPH_SLUG,
            node_alias="found_date",
            datatype="date",
            value=encode_date(date_string),
        )

    @classmethod
    def _add_date_range(cls, resource, start_string, end_string):
        DateRangeSearch.objects.create(
            tileid=TileModel.objects.create(resourceinstance=resource),
            resourceinstanceid=resource,
            graph_slug=GRAPH_SLUG,
            node_alias="occupation",
            datatype="edtf",
            start_value=encode_date(start_string),
            end_value=encode_date(end_string),
        )

    def _via_clause(self, search_models, operator, operands):
        payload = {
            "graph_slug": GRAPH_SLUG,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "SEARCH_MODELS",
                        "graph_slug": GRAPH_SLUG,
                        "node_alias": "",
                        "search_models": search_models,
                    },
                    "operator": operator,
                    "operands": operands,
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }
        return set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

    # --- geometry ---

    def test_geo_clause_matches_only_the_resource_in_the_box(self):
        matched = self._via_clause(
            ["GeometrySearch"],
            "GEO_INTERSECTS",
            [{"type": "GEO_LITERAL", "value": SEARCH_FEATURE_COLLECTION}],
        )
        self.assertEqual(matched, {self.inside_box.pk})

    def test_a_buffered_feature_reaches_further(self):
        """
        Per-feature buffering only happens on the FeatureCollection path, so it
        is the piece most easily lost. The wider result is the proof it ran.
        """
        buffered = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "buffer_distance": 50,
                        "buffer_units": "kilometers",
                    },
                    "geometry": SEARCH_FEATURE_COLLECTION["features"][0]["geometry"],
                }
            ],
        }
        matched = self._via_clause(
            ["GeometrySearch"],
            "GEO_INTERSECTS",
            [{"type": "GEO_LITERAL", "value": buffered}],
        )
        self.assertEqual(matched, {self.inside_box.pk, self.just_outside_box.pk})

    def test_several_features_union(self):
        """
        Two disjoint features union to a MultiPolygon -- the shape the
        antimeridian splitter cannot walk, which is why the FeatureCollection
        path deliberately skips it.
        """
        two_features = {
            "type": "FeatureCollection",
            "features": [
                SEARCH_FEATURE_COLLECTION["features"][0],
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [29.0, 29.0],
                                [31.0, 29.0],
                                [31.0, 31.0],
                                [29.0, 31.0],
                                [29.0, 29.0],
                            ]
                        ],
                    },
                },
            ],
        }
        matched = self._via_clause(
            ["GeometrySearch"],
            "GEO_INTERSECTS",
            [{"type": "GEO_LITERAL", "value": two_features}],
        )
        self.assertEqual(matched, {self.inside_box.pk, self.inside_second_feature.pk})

    # --- dates ---

    def test_date_clause_matches_a_date_and_an_overlapping_range(self):
        """
        One clause spanning both models: DateSearch resolves BETWEEN through the
        date datatype (value__range) and DateRangeSearch through edtf (an
        overlap), and the two OR together -- which is what the replaced filter
        did by hand.
        """
        matched = self._via_clause(
            ["DateSearch", "DateRangeSearch"],
            "BETWEEN",
            [
                {"type": "LITERAL", "value": WINDOW_FROM},
                {"type": "LITERAL", "value": WINDOW_TO},
            ],
        )
        self.assertEqual(matched, {self.date_in_window.pk, self.range_overlapping.pk})

    def test_date_clause_excludes_rows_outside_the_window(self):
        matched = self._via_clause(
            ["DateSearch", "DateRangeSearch"],
            "BETWEEN",
            [
                {"type": "LITERAL", "value": WINDOW_FROM},
                {"type": "LITERAL", "value": WINDOW_TO},
            ],
        )
        self.assertNotIn(self.date_outside_window.pk, matched)
        self.assertNotIn(self.range_disjoint.pk, matched)
