"""
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

"""This module contains commands for building Arches."""
import datetime
import math
import multiprocessing
import time

import django
from django.apps import apps

if not apps.ready:
    django.setup()

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, connections
from arches.app.models.models import TileModel, Node
from arches_search.indexing.index_from_tile import index_from_tile
from arches_search.indexing.indexing_factory import IndexingFactory
from arches_search.models.models import (
    BooleanSearch,
    DateRangeSearch,
    DateSearch,
    FileListSearch,
    GeometrySearch,
    NumericSearch,
    TermSearch,
    UUIDSearch,
)

SEARCH_MODELS = [
    TermSearch,
    NumericSearch,
    DateSearch,
    UUIDSearch,
    DateRangeSearch,
    BooleanSearch,
    GeometrySearch,
    FileListSearch,
]


def _build_nodegroup_cache():
    cache = {}
    for node in Node.objects.exclude(
        graph_id=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID
    ).select_related("graph"):
        cache.setdefault(node.nodegroup_id, []).append(node)
    return cache


# Worker-process state, populated once per worker by _init_worker.
_worker_factory = None
_worker_nodegroup_cache = None
_worker_progress = None


def _init_worker(progress_counter=None):
    django.setup()
    global _worker_factory, _worker_nodegroup_cache, _worker_progress
    _worker_factory = IndexingFactory()
    _worker_nodegroup_cache = _build_nodegroup_cache()
    _worker_progress = progress_counter


def _index_tile_shard(worker_id, num_workers):
    """Index the tiles whose tileid hashes into this worker's shard."""
    batch_size = settings.BULK_IMPORT_BATCH_SIZE
    values_to_index = {model: [] for model in SEARCH_MODELS}
    tile_count = 0
    since_last_report = 0

    qs = TileModel.objects.exclude(
        resourceinstance_id=settings.SYSTEM_SETTINGS_RESOURCE_ID
    ).extra(
        where=["abs(hashtext(tileid::text)::bigint) %% %s = %s"],
        params=[num_workers, worker_id],
    )

    def flush():
        for model, values in values_to_index.items():
            if values:
                model.objects.bulk_create(values, batch_size=batch_size)
                values.clear()

    def report_progress(n):
        if _worker_progress is not None and n:
            with _worker_progress.get_lock():
                _worker_progress.value += n

    for tile in qs.iterator(chunk_size=batch_size):
        for val in (
            index_from_tile(
                tile,
                delete_existing=False,
                indexing_factory=_worker_factory,
                nodegroup_cache=_worker_nodegroup_cache,
            )
            or []
        ):
            values_to_index[type(val)].append(val)
        tile_count += 1
        since_last_report += 1
        if tile_count % batch_size == 0:
            flush()
            report_progress(since_last_report)
            since_last_report = 0
    flush()
    report_progress(since_last_report)
    return (worker_id, tile_count)


class Command(BaseCommand):
    """
    Commands for managing search index data

    """

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            nargs="?",
            choices=[
                "reindex_database",
            ],
            help="Operation Type; "
            + "'reindex_database'=Deletes and re-creates all arches search indices",
        )
        parser.add_argument(
            "--keep-indexes",
            action="store_true",
            help="Skip the drop/recreate of search-table indexes during reindex. "
            "Default is to drop all indexes before the bulk load and rebuild them "
            "after; use this flag on small datasets where the rebuild overhead "
            "exceeds the per-insert savings.",
        )
        parser.add_argument(
            "-mp",
            "--use_multiprocessing",
            action="store_true",
            dest="use_multiprocessing",
            default=False,
            help="indexes the tile shards in parallel processes",
        )
        parser.add_argument(
            "-mxp",
            "--max_subprocesses",
            action="store",
            type=int,
            dest="max_subprocesses",
            default=0,
            help="Changes the process pool size when using use_multiprocessing. "
            "Default is ceil(cpu_count()/2)",
        )

    def handle(self, *_, **options):
        if options["operation"] == "reindex_database":
            self.reindex_database(
                keep_indexes=options["keep_indexes"],
                use_multiprocessing=options["use_multiprocessing"],
                max_subprocesses=options["max_subprocesses"],
            )

    def _flush(self, values_to_index, batch_size):
        for index_type, values in values_to_index.items():
            if values:
                index_type.objects.bulk_create(values, batch_size=batch_size)
                values.clear()

    def reindex_database(
        self,
        keep_indexes=False,
        use_multiprocessing=False,
        max_subprocesses=0,
    ):
        self.delete_indexes()
        indexing_start = datetime.datetime.now()

        # do not remove this block or tests will fail.  open transactions
        # will interfere with dropping/recreating indexes, so skip that
        # if any are open
        if not keep_indexes and connection.in_atomic_block:
            self.stdout.write(
                "Detected open transaction; keeping indexes in place "
                "(drop/recreate would conflict with pending trigger events)."
            )
            keep_indexes = True

        dropped_indexes = [] if keep_indexes else self._drop_indexes()
        try:
            if use_multiprocessing:
                self._reindex_multiprocess(max_subprocesses)
            else:
                self._reindex_singleprocess()
        finally:
            if dropped_indexes:
                self.stdout.write(
                    f"Rebuilding {len(dropped_indexes)} index(es) "
                    "(this may take several minutes)..."
                )
                rebuild_start = datetime.datetime.now()
                self._recreate_indexes(dropped_indexes)
                self.stdout.write(
                    f"Rebuilt {len(dropped_indexes)} index(es) in "
                    f"{datetime.datetime.now() - rebuild_start}"
                )
        self.stdout.write(f"Indexing took {datetime.datetime.now() - indexing_start}")

    def _reindex_singleprocess(self):
        batch_size = settings.BULK_IMPORT_BATCH_SIZE
        nodegroup_cache = _build_nodegroup_cache()
        values_to_index = {model: [] for model in SEARCH_MODELS}
        indexing_factory = IndexingFactory()
        tile_count = 0

        for tile in TileModel.objects.exclude(
            resourceinstance_id=settings.SYSTEM_SETTINGS_RESOURCE_ID
        ).iterator(chunk_size=batch_size):
            for val in (
                index_from_tile(
                    tile,
                    delete_existing=False,
                    indexing_factory=indexing_factory,
                    nodegroup_cache=nodegroup_cache,
                )
                or []
            ):
                values_to_index[type(val)].append(val)

            tile_count += 1
            if tile_count % batch_size == 0:
                self._flush(values_to_index, batch_size)
                self.stdout.write(f"indexed {tile_count} tiles")

        self._flush(values_to_index, batch_size)

    def _reindex_multiprocess(self, max_subprocesses):
        try:
            multiprocessing.set_start_method("spawn")
        except RuntimeError:
            pass

        cpu_count = multiprocessing.cpu_count()
        if max_subprocesses == 0:
            process_count = math.ceil(cpu_count / 2)
        elif max_subprocesses > cpu_count:
            process_count = cpu_count
            self.stdout.write(
                f"--max_subprocesses exceeds CPU count; limiting to {process_count}"
            )
        else:
            process_count = max_subprocesses

        total_tiles = TileModel.objects.exclude(
            resourceinstance_id=settings.SYSTEM_SETTINGS_RESOURCE_ID
        ).count()
        self.stdout.write(
            f"Indexing {total_tiles} tiles across {process_count} worker(s)"
        )

        connections.close_all()

        progress = multiprocessing.Value("q", 0)
        errors = []

        def on_done(result):
            worker_id, tile_count = result
            self.stdout.write(f"Worker {worker_id} finished ({tile_count} tiles)")

        def on_err(err):
            import traceback

            try:
                raise err
            except Exception:
                tb = traceback.format_exc()
            errors.append((err, tb))
            self.stderr.write(f"Worker error: {err}\n{tb}")

        with multiprocessing.Pool(
            processes=process_count,
            initializer=_init_worker,
            initargs=(progress,),
        ) as pool:
            results = [
                pool.apply_async(
                    _index_tile_shard,
                    args=(worker_id, process_count),
                    callback=on_done,
                    error_callback=on_err,
                )
                for worker_id in range(process_count)
            ]
            pool.close()

            start = datetime.datetime.now()
            last_printed = -1
            while not all(r.ready() for r in results):
                time.sleep(2)
                current = progress.value
                if current == last_printed:
                    continue
                elapsed = (datetime.datetime.now() - start).total_seconds()
                rate = current / elapsed if elapsed > 0 else 0.0
                if total_tiles:
                    pct = 100.0 * current / total_tiles
                    self.stdout.write(
                        f"indexed {current}/{total_tiles} tiles "
                        f"({pct:.1f}%, {rate:.0f}/s)"
                    )
                else:
                    self.stdout.write(f"indexed {current} tiles ({rate:.0f}/s)")
                last_printed = current

            pool.join()

        if errors:
            raise RuntimeError(
                f"{len(errors)} indexing worker(s) failed; see logs above"
            )

    def delete_indexes(self):
        table_names = ", ".join(model._meta.db_table for model in SEARCH_MODELS)
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE {table_names}")

    def _drop_indexes(self):
        dropped = []
        with connection.schema_editor() as editor:
            for model in SEARCH_MODELS:
                for index in model._meta.indexes:
                    editor.remove_index(model, index)
                    dropped.append((model, index))
        if dropped:
            self.stdout.write(f"Dropped {len(dropped)} index(es) for bulk load")
        return dropped

    def _recreate_indexes(self, dropped):
        with connection.schema_editor() as editor:
            for model, index in dropped:
                editor.add_index(model, index)
