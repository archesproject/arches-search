"""Descriptor (display-name) term indexing.

Verifies the reference-number-in-display-name is made text-searchable by indexing
the resource descriptor into the term table, borrowing a real tile for the NOT
NULL tileid, filtering empty/"Undefined" names, and re-indexing idempotently.
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

from arches_search.indexing.index_descriptor import (
    DESCRIPTOR_NODE_ALIAS,
    index_resource_descriptors,
)
from arches_search.models.models import TermSearch

REFERENCE = "HER-12345 Round Barrow"


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
        index_resource_descriptors(self.resource)
        rows = self._rows()
        self.assertEqual(rows.count(), 1)
        row = rows.first()
        self.assertEqual(row.value, REFERENCE)
        self.assertEqual(str(row.tileid_id), str(self.tile.tileid))
        self.assertEqual(row.language, "en")

        index_resource_descriptors(self.resource)  # must not duplicate
        self.assertEqual(self._rows().count(), 1)

    def test_skips_undefined_and_empty_names(self):
        self.resource.descriptors = {"en": {"name": "Undefined"}, "fr": {"name": ""}}
        self.resource.save()
        index_resource_descriptors(self.resource)
        self.assertEqual(self._rows().count(), 0)
