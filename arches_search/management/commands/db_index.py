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
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
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

    def handle(self, *args, **options):
        if options["operation"] == "reindex_database":
            self.reindex_database()

    def _flush(self, values_to_index, batch_size):
        for index_type, values in values_to_index.items():
            if values:
                index_type.objects.bulk_create(values, batch_size=batch_size)
                values.clear()

    def reindex_database(self):
        self.delete_indexes()
        SYSTEM_SETTINGS_GRAPH = "ff623370-fa12-11e6-b98b-6c4008b05c4c"
        BATCH_SIZE = 1000
        nodegroup_cache = {}
        for node in Node.objects.exclude(graph_id=SYSTEM_SETTINGS_GRAPH).select_related(
            "graph"
        ):
            nodegroup_cache.setdefault(node.nodegroup_id, []).append(node)

        values_to_index = {model: [] for model in SEARCH_MODELS}
        indexing_factory = IndexingFactory()
        indexing_start = datetime.datetime.now()
        tile_count = 0

        for tile in TileModel.objects.exclude(
            resourceinstance_id=settings.SYSTEM_SETTINGS_RESOURCE_ID
        ).iterator(chunk_size=BATCH_SIZE):
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
            if tile_count % BATCH_SIZE == 0:
                self._flush(values_to_index, BATCH_SIZE)
                self.stdout.write(f"indexed {tile_count} tiles")

        self._flush(values_to_index, BATCH_SIZE)
        self.stdout.write(f"Indexing took {datetime.datetime.now() - indexing_start}")

    def delete_indexes(self):
        table_names = ", ".join(model._meta.db_table for model in SEARCH_MODELS)
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE {table_names}")
