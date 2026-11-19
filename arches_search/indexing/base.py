from django.db.models import QuerySet

from arches.app.datatypes.datatypes import BaseDataType


class BaseIndexing:
    def __init__(self):
        self.datatype: BaseDataType = None

    def index(self, tile, node):
        pass

    def sort_row_filters(self) -> dict:
        """
        Field lookups that pick out the single row to sort by, for an indexer
        that potentially writes several rows per value.

        A reference writes a row per label, so it returns
        {"valuetype": "prefLabel"}. An indexer writing one row per value has
        nothing to narrow, and returns nothing.
        """
        return {}

    def hierarchy_edges(self) -> QuerySet | None:
        return None

    def item_labels(self, item_ids, labels) -> list:
        return []

    def searchable_items(self, query, limit) -> list:
        return []

    def item_paths(self, item_ids, language_code) -> dict:
        return {}
