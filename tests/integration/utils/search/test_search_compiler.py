"""End-to-end tests for SearchCompiler: term_search (including hop expansion),
advanced_search_queries scope across graphs, and resource_type_counts /
all_resource_count behavior.

Geometry and date filtering are advanced search clauses rather than a separate
mechanism -- see test_geo_and_date_search_model_clauses.py."""

import json
import uuid
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import (
    GraphModel,
    ResourceInstance,
    ResourceXResource,
    TileModel,
)

from arches_search.models.models import DateSearch, GeometrySearch, TermSearch
from arches_search.utils.search import (
    SearchCompiler,
    SearchPayload,
    SearchRequest,
    execute_search,
    validate_advanced_search_queries,
)
from arches_search.utils.search.validation import (
    FALLBACK_PAGE_SIZE,
    MAX_PAGE_SIZE,
    default_page_size,
)
from tests.integration.utils.advanced_search.test_advanced_search import (
    AdvancedSearchSetupMixin,
    DOG_A_ID,
    DOG_B_ID,
    DOG_C_ID,
    DOG_D_ID,
    PERSON_A_ID,
    PERSON_B_ID,
    PERSON_C_ID,
    PERSON_D_ID,
)

# python manage.py test tests.integration.utils.search.test_search_compiler --settings="tests.test_settings"


_UNSET = object()

# Where validation reads SEARCH_ITEMS_PER_PAGE. override_settings cannot reach
# it: system settings are a LazySettings of their own.
SYSTEM_SETTINGS = "arches_search.utils.search.validation.settings"


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

    def _search(
        self,
        *,
        graph_slugs=_UNSET,
        term_search=None,
        advanced_search_queries=None,
        pre_filter=None,
    ):
        # Explicit rather than **kwargs, so a renamed payload key is a
        # TypeError instead of a quietly unfiltered search.
        payload = SearchPayload(
            graph_slugs=(
                [self.graph_a.slug, self.graph_b.slug]
                if graph_slugs is _UNSET
                else graph_slugs
            ),
            term_search=term_search,
            advanced_search_queries=advanced_search_queries,
        )
        return SearchCompiler(payload, self.user, pre_filter=pre_filter).compile()

    def _result_ids(self, result):
        return set(result.results.values_list("resourceinstanceid", flat=True))

    def _search_models_payloads(self, search_models, operator, operands):
        """
        The same clause for every graph in the fixture.

        A clause only filters the graph its payload names, so covering the whole
        universe means one entry per graph -- which is what the term search does
        implicitly for all of them at once.
        """
        return [
            {
                "graph_slug": graph.slug,
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": {
                            "type": "SEARCH_MODELS",
                            "graph_slug": graph.slug,
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
            for graph in (self.graph_a, self.graph_b)
        ]

    def test_text_match_direct_only_max_hops_zero(self):
        result = self._search(term_search={"terms": ["amber"], "max_hops": 0})
        self.assertEqual(
            self._result_ids(result),
            {self.amber_mineral.resourceinstanceid, self.amber_site.resourceinstanceid},
        )

    def test_text_match_excludes_non_matching_resource(self):
        result = self._search(term_search={"terms": ["amber"], "max_hops": 0})
        self.assertNotIn(
            self.quartz_mineral.resourceinstanceid, self._result_ids(result)
        )

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
            advanced_search_queries=self._search_models_payloads(
                ["GeometrySearch"],
                "GEO_INTERSECTS",
                [{"type": "GEO_LITERAL", "value": feature_collection}],
            )
        )
        self.assertEqual(
            self._result_ids(result), {self.amber_mineral.resourceinstanceid}
        )

    def test_date_range_matches_only_resource_in_range(self):
        result = self._search(
            advanced_search_queries=self._search_models_payloads(
                ["DateSearch", "DateRangeSearch"],
                "BETWEEN",
                [
                    {"type": "LITERAL", "value": "1890-01-01"},
                    {"type": "LITERAL", "value": "1910-01-01"},
                ],
            )
        )
        self.assertEqual(
            self._result_ids(result), {self.amber_mineral.resourceinstanceid}
        )

    def test_term_search_and_a_date_clause_and_together(self):
        """
        The term search pre-filters each graph and the payload narrows what is
        left, so the two compose without either knowing about the other.
        """
        result = self._search(
            term_search={"terms": ["amber"], "max_hops": 0},
            advanced_search_queries=self._search_models_payloads(
                ["DateSearch", "DateRangeSearch"],
                "BETWEEN",
                [
                    {"type": "LITERAL", "value": "1890-01-01"},
                    {"type": "LITERAL", "value": "1910-01-01"},
                ],
            ),
        )
        # amber_site matches the term search but has no date fixture at all, so
        # AND composition must exclude it.
        self.assertEqual(
            self._result_ids(result), {self.amber_mineral.resourceinstanceid}
        )

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

    def test_empty_advanced_search_queries_does_not_exclude_other_graphs(self):
        result = self._search(
            advanced_search_queries=[self._advanced_search_body(self.graph_a)]
        )
        ids = self._result_ids(result)
        # An empty clause list narrows nothing.
        self.assertIn(self.amber_mineral.resourceinstanceid, ids)
        self.assertIn(self.quartz_mineral.resourceinstanceid, ids)
        self.assertIn(self.amber_site.resourceinstanceid, ids)

    def test_term_search_over_http(self):
        """
        The shape the simple search bar sends. Covered here because term_search
        is the one filter with no clause equivalent, so nothing else asserts it
        end to end.
        """
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("search"),
            json.dumps(
                {
                    "graph_slugs": [self.graph_a.slug, self.graph_b.slug],
                    "term_search": {"terms": ["amber"], "max_hops": 0},
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        returned_ids = {
            resource["resourceinstanceid"] for resource in response.json()["resources"]
        }
        self.assertEqual(
            returned_ids,
            {
                str(self.amber_mineral.resourceinstanceid),
                str(self.amber_site.resourceinstanceid),
            },
        )

    def test_malformed_term_search_is_a_bad_request(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("search"),
            json.dumps(
                {
                    "graph_slugs": [self.graph_a.slug],
                    # The list-of-typed-entries shape this key used to take.
                    "term_search": [{"type": "TEXT_MATCH", "value": ["amber"]}],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_a_payload_naming_an_unsearched_graph_is_a_400(self):
        """
        A typo in graph_slug used to drop the whole payload without a word, and
        the graph it was meant to filter came back whole -- a search that looks
        like it worked and returns too much.
        """
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("search"),
            json.dumps(
                {
                    "graph_slugs": [self.graph_a.slug],
                    "advanced_search_queries": [
                        {
                            "graph_slug": self.graph_a.slug + "-typo",
                            "scope": "RESOURCE",
                            "logic": "AND",
                            "clauses": [],
                            "groups": [],
                            "aggregations": [],
                            "relationship": None,
                        }
                    ],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_bad_paging_is_a_400_not_a_500(self):
        self.client.force_login(self.user)
        for paging in (
            {"page_size": 0},
            {"page": "abc"},
            {"page": 0},
            {"page_size": 10**6},
        ):
            with self.subTest(paging=paging):
                response = self.client.post(
                    reverse("search"),
                    json.dumps({"graph_slugs": [self.graph_a.slug], **paging}),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400)

    def test_a_page_past_the_end_is_empty_rather_than_an_error(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("search"),
            json.dumps({"graph_slugs": [self.graph_a.slug], "page": 9999}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["resources"], [])
        self.assertFalse(body["pagination"]["has_next"])

    def test_resource_type_counts_come_back_in_a_stable_order(self):
        """Built from a set, this reshuffled between processes."""
        first = [row["graph_id"] for row in self._search().resource_type_counts]
        second = [row["graph_id"] for row in self._search().resource_type_counts]

        self.assertEqual(first, second)
        # Ordered by slug, so "…-mineral" precedes "…-site" every time.
        self.assertEqual(
            first[:2],
            [str(self.graph_a.graphid), str(self.graph_b.graphid)],
        )

    def test_selecting_no_graphs_returns_nothing_but_still_counts(self):
        result = self._search(graph_slugs=None)

        self.assertEqual(self._result_ids(result), set())
        self.assertEqual(result.scoped_count, 0)

        # Nothing returned, but the counts still say what is out there.
        counts_by_graph_id = {
            row["graph_id"]: row["count"] for row in result.resource_type_counts
        }
        self.assertEqual(counts_by_graph_id[str(self.graph_a.graphid)], 2)
        self.assertEqual(counts_by_graph_id[str(self.graph_b.graphid)], 1)

    def test_resource_type_counts_cover_every_active_graph_regardless_of_graph_slugs(
        self,
    ):
        result = self._search(
            graph_slugs=[self.graph_a.slug],
            term_search={"terms": ["amber"], "max_hops": 0},
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

    def _post_search(self, body):
        self.client.force_login(self.user)
        return self.client.post(
            reverse("search"), json.dumps(body), content_type="application/json"
        )

    def test_page_size_defaults_to_search_items_per_page(self):
        with mock.patch(SYSTEM_SETTINGS, SimpleNamespace(SEARCH_ITEMS_PER_PAGE=1)):
            response = self._post_search({"graph_slugs": [self.graph_a.slug]})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["pagination"]["page_size"], 1)
        self.assertEqual(len(body["resources"]), 1)
        # graph_a holds two resources, so one per page leaves another page.
        self.assertTrue(body["pagination"]["has_next"])

    def test_a_configured_page_size_above_the_cap_raises_the_cap(self):
        configured = MAX_PAGE_SIZE + 50
        with mock.patch(
            SYSTEM_SETTINGS, SimpleNamespace(SEARCH_ITEMS_PER_PAGE=configured)
        ):
            default_request = self._post_search({"graph_slugs": [self.graph_a.slug]})
            oversized_request = self._post_search(
                {"graph_slugs": [self.graph_a.slug], "page_size": configured + 1}
            )

        with self.subTest("the default is never rejected"):
            self.assertEqual(default_request.status_code, 200)
            self.assertEqual(
                default_request.json()["pagination"]["page_size"], configured
            )
        with self.subTest("but a request past it still is"):
            self.assertEqual(oversized_request.status_code, 400)

    def test_an_unusable_configured_page_size_falls_back(self):
        for configured, expected in (
            (25.0, 25),
            (None, FALLBACK_PAGE_SIZE),
            (0, FALLBACK_PAGE_SIZE),
            (True, FALLBACK_PAGE_SIZE),
        ):
            with self.subTest(configured=configured):
                with mock.patch(
                    SYSTEM_SETTINGS, SimpleNamespace(SEARCH_ITEMS_PER_PAGE=configured)
                ):
                    self.assertEqual(default_page_size(), expected)

    def test_pre_filter_narrows_the_results_and_the_counts(self):
        result = self._search(
            pre_filter=ResourceInstance.objects.filter(
                resourceinstanceid__in=[
                    self.quartz_mineral.resourceinstanceid,
                    self.amber_site.resourceinstanceid,
                ]
            )
        )
        counts_by_graph_id = {
            row["graph_id"]: row["count"] for row in result.resource_type_counts
        }

        self.assertEqual(
            self._result_ids(result),
            {
                self.quartz_mineral.resourceinstanceid,
                self.amber_site.resourceinstanceid,
            },
        )
        self.assertEqual(counts_by_graph_id[str(self.graph_a.graphid)], 1)
        self.assertEqual(counts_by_graph_id[str(self.graph_b.graphid)], 1)
        self.assertEqual(result.all_resource_count, 2)
        self.assertEqual(result.scoped_count, 2)

    def test_pre_filter_and_the_term_search_intersect(self):
        # "amber" matches amber_mineral and amber_site; the pre_filter holds
        # both minerals. Only amber_mineral is in both.
        result = self._search(
            term_search={"terms": ["amber"], "max_hops": 0},
            pre_filter=ResourceInstance.objects.filter(graph=self.graph_a),
        )

        self.assertEqual(
            self._result_ids(result), {self.amber_mineral.resourceinstanceid}
        )

    def test_an_ordered_pre_filter_does_not_split_the_counts(self):
        pre_filter = ResourceInstance.objects.filter(graph=self.graph_a)
        unordered = self._search(pre_filter=pre_filter)
        ordered = self._search(pre_filter=pre_filter.order_by("resourceinstanceid"))

        self.assertEqual(ordered.resource_type_counts, unordered.resource_type_counts)
        self.assertEqual(ordered.scoped_count, 2)

    def test_execute_search_searches_within_pre_filter(self):
        response = execute_search(
            SearchRequest.from_body({"graph_slugs": [self.graph_a.slug]}),
            self.user,
            pre_filter=ResourceInstance.objects.filter(pk=self.quartz_mineral.pk),
        )

        self.assertEqual(
            [str(resource["resourceinstanceid"]) for resource in response.resources],
            [str(self.quartz_mineral.resourceinstanceid)],
        )
        self.assertEqual(response.pagination["total_results"], 1)


class PerGraphAdvancedSearchQueryTests(AdvancedSearchSetupMixin, TestCase):
    """
    advanced_search_queries carries one payload per graph being filtered.

    A graph a payload addresses is filtered by it; a graph no payload addresses
    is returned whole. That is what lets a caller ask for two resource models and
    refine only one of them -- the other still earns its place in the results.

    The Person/Dog fixture is used because it is the only one with real nodes,
    which a filtering clause needs.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # The fixture never sets is_active; SearchCompiler only searches
        # active graphs.
        GraphModel.objects.filter(
            graphid__in=[cls.person_graph.graphid, cls.dog_graph.graphid]
        ).update(is_active=True)
        cls.user = get_user_model().objects.create_superuser(
            username="per-graph-admin",
            email="per-graph@example.com",
            password="unused",
        )

    PERSON_IDS = {PERSON_A_ID, PERSON_B_ID, PERSON_C_ID, PERSON_D_ID}
    DOG_IDS = {DOG_A_ID, DOG_B_ID, DOG_C_ID, DOG_D_ID}

    @staticmethod
    def _person_payload(value):
        return {
            "graph_slug": "person",
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": "person",
                        "node_alias": "first_name",
                        "search_models": [],
                    },
                    "operator": "EQUALS",
                    "operands": [{"type": "LITERAL", "value": value}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

    @staticmethod
    def _dog_payload(minimum_tail_length):
        return {
            "graph_slug": "dog",
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": "dog",
                        "node_alias": "tail_length",
                        "search_models": [],
                    },
                    "operator": "GREATER_THAN",
                    "operands": [{"type": "LITERAL", "value": minimum_tail_length}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

    def _search(self, advanced_search_queries=None, graph_slugs=None, pre_filter=None):
        return SearchCompiler(
            SearchPayload(
                graph_slugs=graph_slugs,
                term_search=None,
                advanced_search_queries=advanced_search_queries,
            ),
            self.user,
            pre_filter=pre_filter,
        ).compile()

    @staticmethod
    def _ids(result):
        return set(result.results.values_list("resourceinstanceid", flat=True))

    def _count_for(self, result, graph_id):
        return next(
            entry["count"]
            for entry in result.resource_type_counts
            if entry["graph_id"] == str(graph_id)
        )

    def test_a_graph_no_payload_addresses_is_returned_whole(self):
        both = ["person", "dog"]
        result = self._search([self._person_payload("FOO")], graph_slugs=both)
        ids = self._ids(result)

        with self.subTest("the addressed graph is filtered"):
            self.assertEqual(ids & self.PERSON_IDS, {PERSON_A_ID})
        with self.subTest("the unaddressed graph comes through whole"):
            self.assertEqual(ids & self.DOG_IDS, self.DOG_IDS)
        with self.subTest("and the counts agree"):
            self.assertEqual(self._count_for(result, self.person_graph.graphid), 1)
            self.assertEqual(
                self._count_for(result, self.dog_graph.graphid), len(self.DOG_IDS)
            )

    def test_a_payload_matching_nothing_does_not_take_other_graphs_with_it(self):
        result = self._search(
            [self._person_payload("no-such-name")], graph_slugs=["person", "dog"]
        )
        ids = self._ids(result)

        self.assertEqual(ids & self.PERSON_IDS, set())
        self.assertEqual(ids & self.DOG_IDS, self.DOG_IDS)

    def test_each_payload_filters_its_own_graph(self):
        # Two payloads, two graphs, each narrowed by its own clauses. Tails are
        # 25, 999, 10 and 200, so the threshold keeps dog_b and dog_d.
        result = self._search(
            [self._person_payload("FOO"), self._dog_payload(100)],
            graph_slugs=["person", "dog"],
        )
        ids = self._ids(result)

        self.assertEqual(ids & self.PERSON_IDS, {PERSON_A_ID})
        self.assertEqual(ids & self.DOG_IDS, {DOG_B_ID, DOG_D_ID})

    def test_graph_slugs_still_scopes_the_returned_rows(self):
        # The dog graph is filtered out by scoping, not by the person payload.
        result = self._search([self._person_payload("FOO")], graph_slugs=["person"])

        self.assertEqual(self._ids(result), {PERSON_A_ID})

    def test_two_payloads_for_one_graph_are_rejected(self):
        with self.assertRaises(ValidationError):
            validate_advanced_search_queries(
                [self._person_payload("FOO"), self._person_payload("BAR")]
            )

    def test_pre_filter_narrows_addressed_and_unaddressed_graphs_alike(self):
        # Tails over 100 keep dog_b and dog_d; the pre_filter holds dog_a and
        # dog_b, so only dog_b survives both. Person has no payload, so it is
        # narrowed by the pre_filter alone.
        result = self._search(
            [self._dog_payload(100)],
            graph_slugs=["person", "dog"],
            pre_filter=ResourceInstance.objects.filter(
                resourceinstanceid__in=[PERSON_A_ID, PERSON_B_ID, DOG_A_ID, DOG_B_ID]
            ),
        )
        ids = self._ids(result)

        with self.subTest("the addressed graph is filtered within it"):
            self.assertEqual(ids & self.DOG_IDS, {DOG_B_ID})
        with self.subTest("the unaddressed graph is narrowed to it"):
            self.assertEqual(ids & self.PERSON_IDS, {PERSON_A_ID, PERSON_B_ID})
