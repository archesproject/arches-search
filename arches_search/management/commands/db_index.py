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
from django.core.management.base import BaseCommand
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
            + "'reindex_database'=Deletes and re-creates all indices in ElasticSearch, then indexes all data found in the database",
        )

    def handle(self, *args, **options):
        if options["operation"] == "reindex_database":
            self.reindex_database()

    def reindex_database(self):
        self.delete_indexes()
        nodegroup_cache = {}
        indexing_factory = IndexingFactory()

        terms = []
        numbers = []
        dates = []
        date_ranges = []
        booleans = []
        uuids = []
        print("Calculating index values")
        value_calculation_start = datetime.datetime.now()

        for tile in (
            TileModel.objects.order_by("tileid").all().iterator(chunk_size=1000)
        ):
            index_values = index_from_tile(
                tile,
                delete_existing=False,
                indexing_factory=indexing_factory,
                nodegroup_cache=nodegroup_cache,
            )
            if index_values:
                for val in index_values:
                    if isinstance(val, TermSearch):
                        terms.append(val)
                    elif isinstance(val, DateSearch):
                        dates.append(val)
                    elif isinstance(val, NumericSearch):
                        numbers.append(val)
                    elif isinstance(val, UUIDSearch):
                        uuids.append(val)
                    elif isinstance(val, BooleanSearch):
                        booleans.append(val)
                    elif isinstance(val, DateRangeSearch):
                        date_ranges.append(val)

        print(
            f"Value calculation took {datetime.datetime.now() - value_calculation_start} seconds"
        )

        print("Saving index records")
        value_saving_start = datetime.datetime.now()
        TermSearch.objects.bulk_create(terms, batch_size=1000)
        NumericSearch.objects.bulk_create(numbers, batch_size=1000)
        DateSearch.objects.bulk_create(dates, batch_size=1000)
        UUIDSearch.objects.bulk_create(uuids, batch_size=1000)
        DateRangeSearch.objects.bulk_create(date_ranges, batch_size=1000)
        BooleanSearch.objects.bulk_create(booleans, batch_size=1000)

        print(
            f"Value saving took {datetime.datetime.now() - value_saving_start} seconds"
        )

    def delete_indexes(self, name=None):
        TermSearch.objects.all().delete()
        NumericSearch.objects.all().delete()
        DateSearch.objects.all().delete()
        DateRangeSearch.objects.all().delete()
        BooleanSearch.objects.all().delete()
        UUIDSearch.objects.all().delete()
