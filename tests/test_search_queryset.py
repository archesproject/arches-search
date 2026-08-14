"""Tests for the graphId -> graphIds (multi-select) change in search_queryset.py."""

import io
import uuid

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth import get_user_model

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    TileModel,
)

from arches_search.utils.search_queryset import (
    SimpleSearchQuerysetBuilder,
    build_resource_type_counts,
    build_search_queryset,
)

# python manage.py test tests.test_search_queryset --settings="tests.test_settings"


class SearchQuerysetTestCaseBase(TestCase):
    """Two graphs, each with one string node and a couple of resources, so
    tests can exercise cross-graph term matching (and therefore the
    per-graph UNION ALL combine path) without needing resource_x_resource
    hop fixtures."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="search-queryset-tester", password="unused"
        )
        cls.superuser = get_user_model().objects.create_superuser(
            username="search-queryset-admin",
            email="admin@example.com",
            password="unused",
        )

        cls.graph_a = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="Mineral",
            slug="search-queryset-test-mineral",
            isresource=True,
            is_active=True,
            iconclass="fa fa-gem",
        )
        cls.graph_b = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="Site",
            slug="search-queryset-test-site",
            isresource=True,
            is_active=True,
            iconclass="fa fa-map",
        )
        cls.nodegroup_a = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.nodegroup_b = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.node_a = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="mineral_name",
            alias="mineral_name",
            datatype="string",
            graph=cls.graph_a,
            nodegroup=cls.nodegroup_a,
            istopnode=True,
        )
        cls.node_b = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="site_name",
            alias="site_name",
            datatype="string",
            graph=cls.graph_b,
            nodegroup=cls.nodegroup_b,
            istopnode=True,
        )

        cls.amber_mineral = cls._create_resource(
            cls.graph_a, cls.nodegroup_a, cls.node_a, "amber specimen"
        )
        cls.quartz_mineral = cls._create_resource(
            cls.graph_a, cls.nodegroup_a, cls.node_a, "quartz specimen"
        )
        cls.amber_site = cls._create_resource(
            cls.graph_b, cls.nodegroup_b, cls.node_b, "amber excavation site"
        )

        call_command("arches_search", "reindex_database", stdout=io.StringIO())

    @classmethod
    def _create_resource(cls, graph, nodegroup, node, text):
        resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(), graph=graph
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=nodegroup,
            resourceinstance=resource,
            data={str(node.nodeid): {"en": {"value": text, "direction": "ltr"}}},
            provisionaledits=None,
        )
        return resource


class BuildSearchQuerysetGraphIdsTests(SearchQuerysetTestCaseBase):
    def test_term_search_across_multiple_graphs_unions_matches(self):
        result = build_search_queryset(
            {
                "terms": [{"text": "amber"}],
                "graphIds": [str(self.graph_a.graphid), str(self.graph_b.graphid)],
            },
            self.superuser,
        )

        ids = set(result.values_list("resourceinstanceid", flat=True))
        self.assertEqual(
            ids,
            {
                self.amber_mineral.resourceinstanceid,
                self.amber_site.resourceinstanceid,
            },
        )

    def test_term_search_single_graph_id_still_scopes_correctly(self):
        result = build_search_queryset(
            {
                "terms": [{"text": "amber"}],
                "graphIds": [str(self.graph_a.graphid)],
            },
            self.superuser,
        )

        ids = set(result.values_list("resourceinstanceid", flat=True))
        self.assertEqual(ids, {self.amber_mineral.resourceinstanceid})

    def test_term_search_excludes_non_matching_resources(self):
        result = build_search_queryset(
            {
                "terms": [{"text": "amber"}],
                "graphIds": [str(self.graph_a.graphid), str(self.graph_b.graphid)],
            },
            self.superuser,
        )

        ids = set(result.values_list("resourceinstanceid", flat=True))
        self.assertNotIn(self.quartz_mineral.resourceinstanceid, ids)

    def test_term_search_without_graph_ids_uses_and_semantics_across_terms(self):
        result = build_search_queryset(
            {"terms": [{"text": "amber"}, {"text": "specimen"}], "graphIds": []},
            self.superuser,
        )

        ids = set(result.values_list("resourceinstanceid", flat=True))
        self.assertEqual(ids, {self.amber_mineral.resourceinstanceid})

    def test_query_only_search_scopes_to_multiple_graph_ids(self):
        result = build_search_queryset(
            {
                "graphIds": [str(self.graph_a.graphid), str(self.graph_b.graphid)],
            },
            self.superuser,
        )

        ids = set(result.values_list("resourceinstanceid", flat=True))
        self.assertEqual(
            ids,
            {
                self.amber_mineral.resourceinstanceid,
                self.quartz_mineral.resourceinstanceid,
                self.amber_site.resourceinstanceid,
            },
        )

    def test_no_terms_or_query_scopes_to_multiple_graph_ids(self):
        result = build_search_queryset(
            {"graphIds": [str(self.graph_a.graphid), str(self.graph_b.graphid)]},
            self.superuser,
        )

        ids = set(result.values_list("resourceinstanceid", flat=True))
        self.assertEqual(
            ids,
            {
                self.amber_mineral.resourceinstanceid,
                self.quartz_mineral.resourceinstanceid,
                self.amber_site.resourceinstanceid,
            },
        )

    def test_missing_graph_ids_defaults_to_no_scoping(self):
        result = build_search_queryset({}, self.superuser)

        ids = set(result.values_list("resourceinstanceid", flat=True))
        self.assertIn(self.amber_mineral.resourceinstanceid, ids)
        self.assertIn(self.amber_site.resourceinstanceid, ids)

    def test_non_list_graph_ids_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            build_search_queryset(
                {"terms": [{"text": "amber"}], "graphIds": str(self.graph_a.graphid)},
                self.superuser,
            )

    def test_non_string_graph_id_entry_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            build_search_queryset(
                {"terms": [{"text": "amber"}], "graphIds": [123]}, self.superuser
            )


class BuildResourceTypeCountsGraphIdsTests(SearchQuerysetTestCaseBase):
    def test_counts_terms_across_multiple_graphs(self):
        type_agnostic_queryset = build_search_queryset(
            {"terms": [{"text": "amber"}], "graphIds": []},
            self.superuser,
        )

        results, all_resource_count = build_resource_type_counts(
            [{"text": "amber"}], type_agnostic_queryset
        )

        counts_by_graph_id = {row["graph_id"]: row["count"] for row in results}
        self.assertEqual(counts_by_graph_id[str(self.graph_a.graphid)], 1)
        self.assertEqual(counts_by_graph_id[str(self.graph_b.graphid)], 1)
        self.assertEqual(all_resource_count, 2)


class SimpleSearchQuerysetBuilderGraphIdsTests(SearchQuerysetTestCaseBase):
    def test_type_agnostic_queryset_reuses_scoped_queryset_when_no_graph_ids(self):
        builder = SimpleSearchQuerysetBuilder(
            {"terms": [{"text": "amber"}]}, self.superuser
        )

        self.assertIs(builder.type_agnostic_queryset, builder.scoped_queryset)

    def test_type_agnostic_queryset_clears_graph_ids_when_present(self):
        builder = SimpleSearchQuerysetBuilder(
            {
                "terms": [{"text": "amber"}],
                "graphIds": [str(self.graph_a.graphid)],
            },
            self.superuser,
        )

        scoped_ids = set(
            builder.scoped_queryset.values_list("resourceinstanceid", flat=True)
        )
        type_agnostic_ids = set(
            builder.type_agnostic_queryset.values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(scoped_ids, {self.amber_mineral.resourceinstanceid})
        self.assertEqual(
            type_agnostic_ids,
            {
                self.amber_mineral.resourceinstanceid,
                self.amber_site.resourceinstanceid,
            },
        )
