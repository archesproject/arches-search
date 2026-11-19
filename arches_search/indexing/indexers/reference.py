from django.db.models import Q

from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches.extensions.controlled_lists.models import List, ListItem, ListItemValue
from arches_search.models.models import TermSearch, UUIDSearch

from arches_search.indexing.base import BaseIndexing
from arches_search.utils.vocabulary_hierarchy import BROADER, expand_hierarchy


class ReferenceIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance("reference")

    def sort_row_filters(self) -> dict:
        """Sort by the preferred label, not by an alternate one."""
        return {"valuetype": "prefLabel"}

    def hierarchy_edges(self):
        return ListItem.objects.values_list("parent_id", "id")

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
        ancestor_ids = expand_hierarchy(self.datatype.datatype_name, BROADER, item_ids)
        items = ListItem.objects.filter(
            Q(id__in=item_ids) | Q(id__in=ancestor_ids)
        ).values_list("id", "parent_id", "list__name")
        parent_ids_by_item_id = {}
        list_names_by_item_id = {}
        for item_id, parent_id, list_name in items:
            parent_ids_by_item_id[item_id] = parent_id
            list_names_by_item_id[item_id] = list_name

        labels_by_item_id = {}
        for label in ListItemValue.objects.labels().filter(
            list_item_id__in=parent_ids_by_item_id
        ):
            labels_by_item_id.setdefault(label.list_item_id, []).append(label)

        paths = {}
        for item_id in item_ids:
            labels = []
            path_item_id = item_id
            while path_item_id is not None:
                labels.append(
                    ListItem.find_best_label_from_set(
                        labels_by_item_id.get(path_item_id, []), language_code
                    )
                    or str(path_item_id)
                )
                path_item_id = parent_ids_by_item_id[path_item_id]
            paths[item_id] = [list_names_by_item_id[item_id], *reversed(labels)]
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
