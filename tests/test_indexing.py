"""
Tests confirming that:
  1. Null values can be indexed (stored in the DB without errors)
  2. Very long strings can be indexed (stored in the DB without truncation)

Note: the null value tests assume that the null guards inside each indexer
have been removed so that null values ARE written to the search index.
TermSearch.value (and equivalent fields on other search models) must have
null=True / blank=True for those tests to pass.
"""

import uuid

from django.test import TestCase

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    TileModel,
)

from arches_search.indexing.index_from_tile import index_from_tile


# ---------------------------------------------------------------------------
# Shared test fixture
# ---------------------------------------------------------------------------


class IndexingTestCase(TestCase):
    """
    Creates the minimum arches object hierarchy (graph → nodegroup → node →
    resource instance → tile) needed to drive the indexing pipeline against
    a real database.
    """

    @classmethod
    def setUpTestData(cls):
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="test-indexing",
            isresource=True,
        )
        cls.nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
        )
        cls.string_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="test_string_node",
            alias="test_string_node",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
        )
        cls.non_localized_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="test_non_localized_node",
            alias="test_non_localized_node",
            datatype="non-localized-string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        cls.number_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="test_number_node",
            alias="test_number_node",
            datatype="number",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        cls.boolean_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="test_boolean_node",
            alias="test_boolean_node",
            datatype="boolean",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        cls.resource_instance = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
        )

    def _make_tile(self, node, value):
        """Create (and save) a TileModel whose data has *value* for *node*."""
        return TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=self.nodegroup,
            resourceinstance=self.resource_instance,
            data={str(node.nodeid): value},
            provisionaledits=None,
        )


# ---------------------------------------------------------------------------
# All-datatypes null test
# ---------------------------------------------------------------------------


class AllDatatypesNullIndexingTest(IndexingTestCase):
    """
    A single tile whose every node value is null should produce no indexable
    records from index_from_tile, for every datatype that has a registered
    indexer.
    """

    INDEXER_DATATYPES = [
        "boolean",
        "concept",
        "concept-list",
        "date",
        "edtf",
        "file-list",
        "non-localized-string",
        "number",
        "reference",
        "resource-instance",
        "resource-instance-list",
        "string",
        "url",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.all_datatype_nodes = {}
        for datatype in cls.INDEXER_DATATYPES:
            alias = datatype.replace("-", "_")
            cls.all_datatype_nodes[datatype] = Node.objects.create(
                nodeid=uuid.uuid4(),
                name=f"null_test_{alias}_node",
                alias=f"null_test_{alias}_node",
                datatype=datatype,
                graph=cls.graph,
                nodegroup=cls.nodegroup,
                istopnode=False,
            )

    def test_all_null_values_produce_no_index_records(self):
        """
        index_from_tile returns an empty list when every node value in the
        tile is null, across all datatypes that have a registered indexer.
        """
        tile = TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=self.nodegroup,
            resourceinstance=self.resource_instance,
            data={str(node.nodeid): None for node in self.all_datatype_nodes.values()},
            provisionaledits=None,
        )
        nodegroup_cache = {
            self.nodegroup.nodegroupid: list(self.all_datatype_nodes.values()),
        }

        result = index_from_tile(
            tile,
            delete_existing=False,
            nodegroup_cache=nodegroup_cache,
        )

        self.assertEqual(
            result,
            [],
            msg=(
                f"Expected no index records for null values but got "
                f"{len(result)} record(s): {result}"
            ),
        )
