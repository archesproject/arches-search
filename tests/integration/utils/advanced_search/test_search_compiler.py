"""End-to-end tests for SearchCompiler: node_agnostic_filters (all three
entry types, individually and combined), advanced_search_query graph
scoping, and resource_type_counts/all_resource_count behavior."""

import uuid

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase

from arches.app.models.models import (
    GraphModel,
    ResourceInstance,
    ResourceXResource,
    TileModel,
)

from arches_search.models.models import DateSearch, GeometrySearch, TermSearch
from arches_search.utils.advanced_search.advanced_search import (
    SearchCompiler,
    SearchPayload,
)

# python manage.py test tests.integration.utils.advanced_search.test_search_compiler --settings="tests.test_settings"


def _encode_date(date_string):
    normalized_operands, _ = DateSearch.normalize_operands(
        [{"type": "LITERAL", "value": date_string}], datatype_name="date"
    )
    return normalized_operands[0]["value"]


class SearchCompilerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username="search-compiler-admin",
            email="admin@example.com",
            password="unused",
        )

        cls.graph_a = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="Mineral",
            slug="search-compiler-test-mineral",
            isresource=True,
            is_active=True,
            iconclass="fa fa-gem",
        )
        cls.graph_b = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="Site",
            slug="search-compiler-test-site",
            isresource=True,
            is_active=True,
            iconclass="fa fa-map",
        )

        cls.amber_mineral = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph_a
        )
        cls.quartz_mineral = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph_a
        )
        cls.amber_site = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=cls.graph_b
        )

        cls._add_term(cls.amber_mineral, cls.graph_a, "amber specimen")
        cls._add_term(cls.quartz_mineral, cls.graph_a, "quartz specimen")
        cls._add_term(cls.amber_site, cls.graph_b, "amber excavation site")

        # amber_mineral -> amber_site: a 1-hop relationship so amber_site is only
        # reachable into graph_a's results via hop traversal, not a direct match.
        ResourceXResource.objects.create(
            resourcexid=uuid.uuid4(),
            from_resource=cls.amber_mineral,
            to_resource=cls.amber_site,
            from_resource_graph_id=cls.graph_a.graphid,
            to_resource_graph_id=cls.graph_b.graphid,
        )

        cls._add_point(cls.amber_mineral, cls.graph_a, 10.0, 10.0)
        cls._add_point(cls.quartz_mineral, cls.graph_a, 50.0, 50.0)

        cls._add_date(cls.amber_mineral, cls.graph_a, "1900-01-01")
        cls._add_date(cls.quartz_mineral, cls.graph_a, "2000-01-01")

    @classmethod
    def _add_term(cls, resource, graph, text):
        tile = TileModel.objects.create(resourceinstance=resource)
        TermSearch.objects.create(
            tileid=tile,
            resourceinstanceid=resource,
            graph_slug=graph.slug,
            node_alias="name",
            language="en",
            datatype="string",
            value=text,
        )

    @classmethod
    def _add_point(cls, resource, graph, lon, lat):
        tile = TileModel.objects.create(resourceinstance=resource)
        GeometrySearch.objects.create(
            tileid=tile,
            resourceinstanceid=resource,
            graph_slug=graph.slug,
            node_alias="location",
            datatype="geojson-feature-collection",
            geom=GEOSGeometry(f"POINT({lon} {lat})", srid=4326),
        )

    @classmethod
    def _add_date(cls, resource, graph, date_string):
        tile = TileModel.objects.create(resourceinstance=resource)
        DateSearch.objects.create(
            tileid=tile,
            resourceinstanceid=resource,
            graph_slug=graph.slug,
            node_alias="found_date",
            datatype="date",
            value=_encode_date(date_string),
        )

    def _search(self, **payload_kwargs):
        payload = SearchPayload(
            graph_ids=payload_kwargs.get("graph_ids"),
            node_agnostic_filters=payload_kwargs.get("node_agnostic_filters"),
            advanced_search_query=payload_kwargs.get("advanced_search_query"),
        )
        return SearchCompiler(payload, self.user).compile()

    def _result_ids(self, result):
        return set(result.results.values_list("resourceinstanceid", flat=True))

    # --- TEXT_MATCH, with hop traversal ---

    def test_text_match_direct_only_max_hops_zero(self):
        result = self._search(
            node_agnostic_filters=[
                {"type": "TEXT_MATCH", "value": ["amber"], "max_hops": 0}
            ]
        )
        self.assertEqual(
            self._result_ids(result),
            {self.amber_mineral.resourceinstanceid, self.amber_site.resourceinstanceid},
        )

    def test_text_match_excludes_non_matching_resource(self):
        result = self._search(
            node_agnostic_filters=[
                {"type": "TEXT_MATCH", "value": ["amber"], "max_hops": 0}
            ]
        )
        self.assertNotIn(
            self.quartz_mineral.resourceinstanceid, self._result_ids(result)
        )

    # --- GEO_INTERSECTS ---

    def test_geo_intersects_matches_only_resource_inside_drawn_shape(self):
        feature_collection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[5, 5], [15, 5], [15, 15], [5, 15], [5, 5]]],
                    },
                }
            ],
        }
        result = self._search(
            node_agnostic_filters=[
                {"type": "GEO_INTERSECTS", "value": feature_collection, "max_hops": 0}
            ]
        )
        self.assertEqual(
            self._result_ids(result), {self.amber_mineral.resourceinstanceid}
        )

    # --- DATE_RANGE ---

    def test_date_range_matches_only_resource_in_range(self):
        result = self._search(
            node_agnostic_filters=[
                {
                    "type": "DATE_RANGE",
                    "value": {"from": "1890-01-01", "to": "1910-01-01"},
                    "max_hops": 0,
                }
            ]
        )
        self.assertEqual(
            self._result_ids(result), {self.amber_mineral.resourceinstanceid}
        )

    # --- combined filters AND together ---

    def test_combined_text_and_date_filters_and_together(self):
        result = self._search(
            node_agnostic_filters=[
                {"type": "TEXT_MATCH", "value": ["amber"], "max_hops": 0},
                {
                    "type": "DATE_RANGE",
                    "value": {"from": "1890-01-01", "to": "1910-01-01"},
                    "max_hops": 0,
                },
            ]
        )
        # amber_site matches TEXT_MATCH but has no date fixture at all, so AND
        # composition must exclude it.
        self.assertEqual(
            self._result_ids(result), {self.amber_mineral.resourceinstanceid}
        )

    # --- advanced_search_query scoping (decision #3) ---

    def _advanced_search_body(self, graph):
        return {
            "graph_slug": graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

    def test_advanced_search_query_is_noop_for_other_graphs(self):
        result = self._search(
            advanced_search_query=self._advanced_search_body(self.graph_a)
        )
        ids = self._result_ids(result)
        # An empty-clauses query on graph_a matches every graph_a resource; graph_b
        # is untouched by the query (a no-op there) but graph_b resources are still
        # searched (this is a "search everywhere" request, no graph_ids given), so
        # amber_site is present too — via the "no filters at all -> whole graph"
        # fallback, not via the query.
        self.assertIn(self.amber_mineral.resourceinstanceid, ids)
        self.assertIn(self.quartz_mineral.resourceinstanceid, ids)
        self.assertIn(self.amber_site.resourceinstanceid, ids)

    # --- resource_type_counts always covers every active graph ---

    def test_resource_type_counts_cover_every_active_graph_regardless_of_graph_ids(
        self,
    ):
        result = self._search(
            graph_ids=[str(self.graph_a.graphid)],
            node_agnostic_filters=[
                {"type": "TEXT_MATCH", "value": ["amber"], "max_hops": 0}
            ],
        )
        counts_by_graph_id = {
            row["graph_id"]: row["count"] for row in result.resource_type_counts
        }
        self.assertEqual(counts_by_graph_id[str(self.graph_a.graphid)], 1)
        self.assertEqual(counts_by_graph_id[str(self.graph_b.graphid)], 1)
        self.assertEqual(result.all_resource_count, 2)
        # scoped to graph_a only:
        self.assertEqual(
            self._result_ids(result), {self.amber_mineral.resourceinstanceid}
        )
        self.assertEqual(result.scoped_count, 1)
