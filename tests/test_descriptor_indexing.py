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
    build_descriptor_terms,
    write_descriptor_search_terms,
)
from arches_search.management.commands.arches_search import (
    _index_descriptor_shard,
)
from arches_search.models.models import TermSearch
from arches_search.utils.advanced_search.registries.node_alias_datatype_registry import (
    NodeAliasDatatypeRegistry,
)
from arches_search.utils.readable_nodes import ReadableNodes
from arches_search.utils.term_search.matching import get_related_resources_by_text

REFERENCE = "HER-12345 Round Barrow"
PRIMARY_DESCRIPTORS_FUNCTION_ID = "60000000-0000-0000-0000-000000000001"


class DescriptorIndexingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug="test-descriptor", isresource=True
        )
        cls.nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(), cardinality="n"
        )
        cls.node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="ref",
            alias="ref",
            datatype="number",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
        )
        FunctionXGraph.objects.create(
            function_id=PRIMARY_DESCRIPTORS_FUNCTION_ID,
            graph=cls.graph,
            config={
                "descriptor_types": {
                    "name": {
                        "nodegroup_id": str(cls.nodegroup.nodegroupid),
                        "string_template": "HER-<ref>",
                    }
                }
            },
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

    def test_function_delete_rebuilds_row_on_remaining_tile(self):
        other_tile = TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=self.nodegroup,
            resourceinstance=self.resource,
            data={str(self.node.nodeid): 12345},
            provisionaledits=None,
            sortorder=1,
        )
        write_descriptor_search_terms(self.resource)
        self.assertEqual(self._rows().get().tileid_id, self.tile.tileid)

        with self.captureOnCommitCallbacks(execute=True):
            SearchIndexingFunction().delete(self.tile)
            self.tile.delete()

        self.assertEqual(self._rows().get().tileid_id, other_tile.tileid)

    def test_skips_name_from_provisional_only_tile(self):
        TileModel.objects.filter(pk=self.tile.tileid).update(
            data={str(self.node.nodeid): None},
            provisionaledits={
                str(uuid.uuid4()): {"value": {str(self.node.nodeid): 12345}}
            },
        )
        self.assertEqual(build_descriptor_terms(self.resource), [])

    def test_ignores_provisional_tile_the_name_is_not_built_from(self):
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=self.nodegroup,
            resourceinstance=self.resource,
            data={str(self.node.nodeid): None},
            provisionaledits={
                str(uuid.uuid4()): {"value": {str(self.node.nodeid): 99999}}
            },
            sortorder=1,
        )
        self.assertEqual(len(build_descriptor_terms(self.resource)), 1)

    def test_multicard_borrows_a_source_tile(self):
        FunctionXGraph.objects.filter(graph=self.graph).update(
            config={
                "descriptor_types": {
                    "name": {"nodegroup_id": "", "string_template": "HER-<ref>"}
                }
            }
        )
        TileModel.objects.create(
            tileid=uuid.UUID(int=0),
            nodegroup=NodeGroup.objects.create(nodegroupid=uuid.uuid4()),
            resourceinstance=self.resource,
            data={},
            provisionaledits=None,
        )
        [row] = build_descriptor_terms(self.resource)
        self.assertEqual(row.tileid_id, self.tile.tileid)

    def test_skips_languages_where_the_template_rendered_empty(self):
        self.resource.descriptors = {
            "en": {"name": REFERENCE},
            "fr": {"name": "HER- "},
        }
        [row] = build_descriptor_terms(self.resource)
        self.assertEqual((row.value, row.language), (REFERENCE, "en"))

    def test_text_only_term_search_skips_the_descriptor(self):
        write_descriptor_search_terms(self.resource)

        def matches(datatype):
            return set(
                get_related_resources_by_text(
                    [REFERENCE],
                    self.graph.graphid,
                    ReadableNodes(user=None),
                    max_hops=0,
                    datatype=datatype,
                ).values_list("resourceinstanceid", flat=True)
            )

        self.assertIn(self.resource.resourceinstanceid, matches(None))
        self.assertNotIn(self.resource.resourceinstanceid, matches("string"))

    def test_any_text_clause_rows_skip_the_descriptor(self):
        write_descriptor_search_terms(self.resource)
        rows = NodeAliasDatatypeRegistry().graph_rows(TermSearch, self.graph.slug)
        self.assertFalse(rows.filter(node_alias=DESCRIPTOR_NODE_ALIAS).exists())

    def test_reuses_the_graph_lookup_for_later_resources(self):
        descriptor_cache = {}
        build_descriptor_terms(self.resource, descriptor_cache)
        with self.assertNumQueries(1):
            build_descriptor_terms(self.resource, descriptor_cache)

    def test_shards_index_each_resource_once(self):
        _index_descriptor_shard(0, 2)
        _index_descriptor_shard(1, 2)
        self.assertEqual(self._rows().count(), 1)

    def test_skips_undefined_and_empty_names(self):
        self.resource.descriptors = {"en": {"name": "Undefined"}, "fr": {"name": ""}}
        self.resource.save()
        write_descriptor_search_terms(self.resource)
        self.assertEqual(self._rows().count(), 0)
