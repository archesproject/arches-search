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
import logging
from django.db import transaction
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from arches.app.models.models import TileModel

from arches_search.indexing.index_from_tile import index_from_tile
from arches_search.indexing.indexing_factory import IndexingFactory
from arches_search.models.models import (
    BooleanSearch,
    NumericSearch,
    TermSearch,
    DateRangeSearch,
    DateSearch,
    UUIDSearch,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Commands for running common elasticsearch commands

    """

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            nargs="?",
            choices=[
                "reindex_database",
            ],
            help="Operation Type; "
            + "'reindex_database'=Deletes and re-creates all indices in ElasticSearch, then indexes all data found in the database",
        )

    def handle(self, *args, **options):
        if options["operation"] == "reindex_database":
            self.reindex_database()

    def reindex_database(self):
        self.delete_indexes()
        nodegroup_cache = {}
        indexing_factory = IndexingFactory()
        paginator = Paginator(TileModel.objects.order_by("tileid").all(), 1000)
        for page in range(1, paginator.num_pages + 1):
            with transaction.atomic():
                for tile in paginator.page(page).object_list:
                    index_from_tile(
                        tile,
                        delete_existing=False,
                        indexing_factory=indexing_factory,
                        nodegroup_cache=nodegroup_cache,
                    )

    def delete_indexes(self, name=None):
        TermSearch.objects.all().delete()
        NumericSearch.objects.all().delete()
        DateSearch.objects.all().delete()
        DateRangeSearch.objects.all().delete()
        BooleanSearch.objects.all().delete()
        UUIDSearch.objects.all().delete()
