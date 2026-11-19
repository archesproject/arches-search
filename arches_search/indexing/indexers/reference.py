from django.db import connection

from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches.extensions.controlled_lists.models import List, ListItem, ListItemValue
from arches_search.models.models import TermSearch, UUIDSearch

from arches_search.indexing.base import BaseIndexing

ANCESTRY_SQL = f"""
WITH RECURSIVE ancestry(item_id, ancestor_id, depth) AS (
    SELECT id, id, 0 FROM {ListItem._meta.db_table} WHERE id = ANY(%s::uuid[])
    UNION ALL
    SELECT ancestry.item_id, item.parent_id, ancestry.depth + 1
    FROM ancestry JOIN {ListItem._meta.db_table} item ON item.id = ancestry.ancestor_id
    WHERE item.parent_id IS NOT NULL
)
SELECT item_id, ancestor_id FROM ancestry ORDER BY item_id, depth DESC
"""


class ReferenceIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance("reference")

    def sort_row_filters(self) -> dict:
        """Sort by the preferred label, not by an alternate one."""
        return {"valuetype": "prefLabel"}

    def hierarchy_edges_sql(self):
        return f"SELECT parent_id AS parent, id AS child FROM {ListItem._meta.db_table}"

    def item_labels(self, item_ids, labels):
        return [
            (label.list_item_id, label.value)
            for label in ListItemValue.objects.labels().filter(
                list_item_id__in=item_ids, value__in=labels
            )
        ]

    def searchable_items(self, query, limit):
        searchable_list_ids = list(
            List.objects.filter(searchable=True).values_list("id", flat=True)
        )
        if not searchable_list_ids:
            return []
        return [
            (label.list_item_id, label.value)
            for label in ListItemValue.objects.labels().filter(
                list_item__list_id__in=searchable_list_ids, value__icontains=query
            )[:limit]
        ]

    def item_paths(self, item_ids, language_code):
        with connection.cursor() as cursor:
            cursor.execute(ANCESTRY_SQL, [[str(item_id) for item_id in item_ids]])
            ancestry = cursor.fetchall()

        labels_by_item_id = {}
        for label in ListItemValue.objects.labels().filter(
            list_item_id__in={ancestor_id for _item_id, ancestor_id in ancestry}
        ):
            labels_by_item_id.setdefault(label.list_item_id, []).append(label)

        paths = {
            list_item["id"]: [list_item["list__name"]]
            for list_item in ListItem.objects.filter(id__in=item_ids).values(
                "id", "list__name"
            )
        }
        for item_id, ancestor_id in ancestry:
            paths[item_id].append(
                ListItem.find_best_label_from_set(
                    labels_by_item_id.get(ancestor_id, []), language_code
                )
                or str(ancestor_id)
            )
        return paths

    def index(self, tile, node):
        """
        A row per label, carrying the language and valuetype it declares.

        Read from the tile rather than through append_to_document(), which
        flattens labels to bare strings and so loses both.
        """
        search_items = []
        list_item_ids = set()

        for reference in tile.data[str(node.nodeid)]:
            for label in reference["labels"]:
                if label["value"] is not None:
                    search_items.append(
                        TermSearch(
                            node_alias=node.alias,
                            tileid_id=tile.tileid,
                            resourceinstanceid_id=tile.resourceinstance_id,
                            datatype=self.datatype.datatype_name,
                            graph_slug=node.graph.slug,
                            language=label["language_id"],
                            valuetype=label["valuetype_id"],
                            value=label["value"],
                        )
                    )

                if label["list_item_id"] is not None:
                    list_item_ids.add(label["list_item_id"])

        for list_item_id in list_item_ids:
            search_items.append(
                UUIDSearch(
                    node_alias=node.alias,
                    tileid_id=tile.tileid,
                    resourceinstanceid_id=tile.resourceinstance_id,
                    datatype=self.datatype.datatype_name,
                    graph_slug=node.graph.slug,
                    value=list_item_id,
                )
            )

        return search_items
