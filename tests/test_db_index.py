"""Tests for the db_index management command."""

import io
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
from arches.app.models.system_settings import settings

from arches_search.management.commands.db_index import (
    SEARCH_MODELS,
    _build_nodegroup_cache,
)
from arches_search.models.models import TermSearch


class DbIndexTestCaseBase(TestCase):
    """Minimal graph → nodegroup → node → resource → tile fixture."""

    @classmethod
    def setUpTestData(cls):
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="test-db-index",
            isresource=True,
        )
        cls.nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
        )
        cls.string_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="db_index_test_node",
            alias="db_index_test_node",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
        )
        cls.resource_instance = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
        )
        cls.tile = TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.nodegroup,
            resourceinstance=cls.resource_instance,
            data={
                str(cls.string_node.nodeid): {
                    "en": {"value": "hello world", "direction": "ltr"},
                },
            },
            provisionaledits=None,
        )


class ReindexHappyPathTests(DbIndexTestCaseBase):
    """End-to-end behavior of `db_index reindex_database`.
    """

    def test_reindex_populates_term_search_for_string_tile(self):
        call_command("db_index", "reindex_database", stdout=io.StringIO())

        rows = TermSearch.objects.filter(tileid=self.tile.tileid)
        self.assertTrue(rows.exists())
        values = list(rows.values_list("value", flat=True))
        self.assertIn("hello world", values)


class TransactionDetectionTests(DbIndexTestCaseBase):
    """The command must detect an open transaction (TestCase wrap) and
    fall back to keep-indexes, otherwise CREATE INDEX collides with
    pgtrigger's deferred trigger events."""

    def test_open_transaction_triggers_keep_indexes_fallback(self):
        out = io.StringIO()
        call_command("db_index", "reindex_database", stdout=out)
        output = out.getvalue()

        self.assertIn("Detected open transaction", output)
        # Drop/rebuild lines must NOT appear in the fallback path
        self.assertNotIn("Dropped", output)
        self.assertNotIn("Rebuilding", output)
        self.assertNotIn("Rebuilt", output)

    def test_keep_indexes_flag_suppresses_detection_notice(self):
        """If keep-indexes is set explicitly, no transaction-detection notice
        should fire (the check short-circuits)."""
        out = io.StringIO()
        call_command("db_index", "reindex_database", "--keep-indexes", stdout=out)
        output = out.getvalue()

        self.assertNotIn("Detected open transaction", output)
        self.assertNotIn("Dropped", output)
        self.assertNotIn("Rebuilding", output)


class BuildNodegroupCacheTests(DbIndexTestCaseBase):
    """Module-level helper used by both single and multiprocess paths."""

    def test_groups_nodes_by_nodegroup_id(self):
        cache = _build_nodegroup_cache()

        self.assertIn(self.nodegroup.nodegroupid, cache)
        cached_node_ids = {node.nodeid for node in cache[self.nodegroup.nodegroupid]}
        self.assertIn(self.string_node.nodeid, cached_node_ids)

    def test_excludes_system_settings_graph(self):
        cache = _build_nodegroup_cache()

        for nodes in cache.values():
            for node in nodes:
                self.assertNotEqual(
                    str(node.graph_id),
                    str(settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID),
                )


class HashShardingPartitionTests(DbIndexTestCaseBase):
    """The SQL hash filter used by multiprocess workers must partition tiles
    cleanly: every tile lands in exactly one worker's shard."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Add a few more tiles so the partition test isn't trivially passing
        # with a single row. Each tile needs its own ResourceInstance because
        # the base nodegroup is cardinality-1 (one tile per resource instance).
        for _ in range(10):
            extra_resource = ResourceInstance.objects.create(
                resourceinstanceid=uuid.uuid4(),
                graph=cls.graph,
            )
            TileModel.objects.create(
                tileid=uuid.uuid4(),
                nodegroup=cls.nodegroup,
                resourceinstance=extra_resource,
                data={str(cls.string_node.nodeid): None},
                provisionaledits=None,
            )

    def _shard_count(self, worker_id, num_workers):
        return (
            TileModel.objects.exclude(
                resourceinstance_id=settings.SYSTEM_SETTINGS_RESOURCE_ID
            )
            .extra(
                where=["abs(hashtext(tileid::text)::bigint) %% %s = %s"],
                params=[num_workers, worker_id],
            )
            .count()
        )

    def test_shards_sum_to_total_tile_count(self):
        total = TileModel.objects.exclude(
            resourceinstance_id=settings.SYSTEM_SETTINGS_RESOURCE_ID
        ).count()

        for num_workers in (1, 2, 4, 8):
            with self.subTest(num_workers=num_workers):
                summed = sum(
                    self._shard_count(worker_id, num_workers)
                    for worker_id in range(num_workers)
                )
                self.assertEqual(
                    summed,
                    total,
                    msg=(
                        f"Hash sharding across {num_workers} workers did not "
                        f"cover every tile (sum={summed}, total={total})."
                    ),
                )


class DeleteIndexesTests(DbIndexTestCaseBase):
    """`delete_indexes` (TRUNCATE) issues TRUNCATE on every search table."""

    def test_delete_indexes_runs_against_every_search_table(self):
        """All search tables start empty and stay empty after a no-op TRUNCATE.

        We can't validate the populate-then-truncate flow inside a TestCase
        transaction (pgtrigger events from the populate would block the
        subsequent TRUNCATE), but we can at least verify the call doesn't
        error against each table name in SEARCH_MODELS.
        """
        from arches_search.management.commands.db_index import Command

        Command().delete_indexes()

        for model in SEARCH_MODELS:
            with self.subTest(model=model.__name__):
                self.assertEqual(model.objects.count(), 0)
