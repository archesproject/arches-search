"""Descriptor (display-name) term indexing.

Verifies the reference-number-in-display-name is made text-searchable by indexing
the resource descriptor into the term table, borrowing a real tile for the NOT
NULL tileid, filtering empty/"Undefined" names, and re-indexing idempotently.
"""
import uuid

from django.test import TestCase

from arches.app.models.models import (
    FunctionXGraph,
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    TileModel,
)

from arches_search.functions.search_indexing import SearchIndexingFunction
from arches_search.indexing.index_descriptor import (
    DESCRIPTOR_NODE_ALIAS,
    write_descriptor_search_terms,
)
from arches_search.models.models import TermSearch

REFERENCE = "HER-12345 Round Barrow"
PRIMARY_DESCRIPTORS_FUNCTION_ID = "60000000-0000-0000-0000-000000000001"


class DescriptorIndexingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug="test-descriptor", isresource=True
        )
        cls.nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="ref",
            alias="ref",
            datatype="number",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
        )
        cls.resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
            descriptors={"en": {"name": REFERENCE, "description": "", "map_popup": ""}},
        )
        cls.tile = TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.nodegroup,
            resourceinstance=cls.resource,
            data={str(cls.node.nodeid): 12345},
            provisionaledits=None,
        )

    def _rows(self):
        return TermSearch.objects.filter(
            resourceinstanceid_id=self.resource.resourceinstanceid,
            node_alias=DESCRIPTOR_NODE_ALIAS,
        )

    def test_indexes_descriptor_with_borrowed_tile_and_is_idempotent(self):
        write_descriptor_search_terms(self.resource)
        rows = self._rows()
        self.assertEqual(rows.count(), 1)
        row = rows.first()
        self.assertEqual(row.value, REFERENCE)
        self.assertEqual(str(row.tileid_id), str(self.tile.tileid))
        self.assertEqual(row.language, "en")

        write_descriptor_search_terms(self.resource)  # must not duplicate
        self.assertEqual(self._rows().count(), 1)

    def test_function_indexes_descriptor_computed_from_tiles(self):
        FunctionXGraph.objects.create(
            function_id=PRIMARY_DESCRIPTORS_FUNCTION_ID,
            graph=self.graph,
            config={
                "descriptor_types": {
                    "name": {
                        "nodegroup_id": str(self.nodegroup.nodegroupid),
                        "string_template": "HER-<ref>",
                    }
                }
            },
        )
        with self.captureOnCommitCallbacks(execute=True):
            SearchIndexingFunction().post_save(self.tile)
            TileModel.objects.filter(pk=self.tile.tileid).update(
                data={str(self.node.nodeid): 99999}
            )

        self.assertEqual([row.value for row in self._rows()], ["HER-99999"])

    def test_function_queues_one_callback_per_resource(self):
        other_tile = TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=self.nodegroup,
            resourceinstance=self.resource,
            data={},
            provisionaledits=None,
        )
        with self.captureOnCommitCallbacks() as callbacks:
            SearchIndexingFunction().post_save(self.tile)
            SearchIndexingFunction().post_save(other_tile)

        self.assertEqual(len(callbacks), 1)

    def test_skips_undefined_and_empty_names(self):
        self.resource.descriptors = {"en": {"name": "Undefined"}, "fr": {"name": ""}}
        self.resource.save()
        write_descriptor_search_terms(self.resource)
        self.assertEqual(self._rows().count(), 0)
