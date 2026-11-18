from django.db import connection
from django.db.models import Q

from arches.app.models.models import GraphModel, Value
from arches.app.utils import permission_backend
from arches.extensions.controlled_lists.models import List, ListItem, ListItemValue
from arches_search.models.models import TermSearch, UUIDSearch
from arches_search.utils.advanced_search.constants import VOCABULARY_DATATYPES
from arches_search.utils.readable_nodes import ReadableNodes
from arches_search.utils.term_search.matching import build_term_match_filter

# Matches are bucketed (vocabulary values vs everything else) so a flood of
# incidental term matches can't crowd the one matching vocabulary row out of
# MAX_RESULTS before the scan reaches it.
MAX_RESULTS = 100
INITIAL_RAW_MATCH_LIMIT = 1000
MAX_RAW_MATCH_LIMIT = 200000
RAW_MATCH_LIMIT_GROWTH_FACTOR = 10
MIN_QUERY_LENGTH = 3

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


def _find_distinct_matches(term_filter, user, readable_nodes):
    """Up to MAX_RESULTS distinct (value, datatype) rows matching term_filter.
    Widens the raw-row cap and retries if a fixed cap under-represents
    distinct values (e.g. one term applied to thousands of resources) —
    capped at MAX_RAW_MATCH_LIMIT, a real trade-off, not just a safety net.

    Unreadable values are dropped before the cap, so they are never suggested
    and never crowd out readable ones.
    """
    raw_match_limit = INITIAL_RAW_MATCH_LIMIT

    while True:
        bounded_ids = list(
            readable_nodes.exclude_unreadable_rows(
                TermSearch.objects.filter(term_filter)
            )
            .order_by("pk")  # deterministic scan order across parallel workers
            .values_list("pk", flat=True)[:raw_match_limit]
        )
        results = list(
            permission_backend.filter_resource_queryset(
                user, TermSearch.objects.filter(pk__in=bounded_ids)
            )
            .values(
                "id",
                "datatype",
                "value",
                "node_alias",
                "tileid",
                "resourceinstanceid",
                "graph_slug",
            )
            .distinct("value", "datatype")
            .order_by("value", "datatype")[:MAX_RESULTS]
        )

        reached_all_matches = len(bounded_ids) < raw_match_limit
        reached_ceiling = raw_match_limit >= MAX_RAW_MATCH_LIMIT
        if len(results) >= MAX_RESULTS or reached_all_matches or reached_ceiling:
            return results

        raw_match_limit = min(
            raw_match_limit * RAW_MATCH_LIMIT_GROWTH_FACTOR,
            MAX_RAW_MATCH_LIMIT,
        )


def _list_item_paths(list_item_ids, language_code):
    with connection.cursor() as cursor:
        cursor.execute(ANCESTRY_SQL, [[str(item_id) for item_id in list_item_ids]])
        ancestry = cursor.fetchall()

    labels_by_item_id = {}
    for label in ListItemValue.objects.labels().filter(
        list_item_id__in={ancestor_id for _item_id, ancestor_id in ancestry}
    ):
        labels_by_item_id.setdefault(label.list_item_id, []).append(label)

    paths = {
        list_item["id"]: [list_item["list__name"]]
        for list_item in ListItem.objects.filter(id__in=list_item_ids).values(
            "id", "list__name"
        )
    }
    for item_id, ancestor_id in ancestry:
        paths[item_id].append(
            ListItem.find_best_label_from_set(
                labels_by_item_id.get(ancestor_id, []), language_code
            )
        )
    return paths


def _vocabulary_items(query, vocabulary_rows):
    rows_by_tile_id = {}
    for vocabulary_row in vocabulary_rows:
        rows_by_tile_id.setdefault(vocabulary_row["tileid"], []).append(vocabulary_row)

    item_ids_by_label = {}
    for id_row in UUIDSearch.objects.filter(
        tileid__in=rows_by_tile_id, datatype__in=VOCABULARY_DATATYPES
    ).values("tileid", "node_alias", "value"):
        for vocabulary_row in rows_by_tile_id[id_row["tileid"]]:
            if vocabulary_row["node_alias"] == id_row["node_alias"]:
                item_ids_by_label.setdefault(vocabulary_row["value"], set()).add(
                    id_row["value"]
                )

    candidate_ids = set().union(*item_ids_by_label.values())
    used_items = [
        (label.list_item_id, "reference", label.value)
        for label in ListItemValue.objects.labels().filter(
            list_item_id__in=candidate_ids, value__in=item_ids_by_label
        )
    ] + [
        (concept_value["concept_id"], "concept", concept_value["value"])
        for concept_value in Value.objects.filter(
            concept_id__in=candidate_ids,
            value__in=item_ids_by_label,
            valuetype__category="label",
        ).values("concept_id", "value")
    ]

    searchable_list_ids = list(
        List.objects.filter(searchable=True).values_list("id", flat=True)
    )
    searchable_items = []
    if searchable_list_ids:
        searchable_items = [
            (label.list_item_id, "reference", label.value)
            for label in ListItemValue.objects.labels().filter(
                list_item__list_id__in=searchable_list_ids, value__icontains=query
            )[:MAX_RESULTS]
        ]

    items_by_id = {}
    for item_id, datatype, label in used_items + searchable_items:
        items_by_id.setdefault(item_id, (item_id, datatype, label))
    return list(items_by_id.values())[:MAX_RESULTS]


def build_term_suggestions(query, request):
    query = query.strip()
    if len(query) < MIN_QUERY_LENGTH:
        return []

    term_filter = build_term_match_filter(query)
    readable_nodes = ReadableNodes(request.user)
    vocabulary_rows = _find_distinct_matches(
        term_filter & Q(datatype__in=VOCABULARY_DATATYPES),
        request.user,
        readable_nodes,
    )
    record_rows = _find_distinct_matches(
        term_filter & ~Q(datatype__in=VOCABULARY_DATATYPES),
        request.user,
        readable_nodes,
    )

    vocabulary_items = _vocabulary_items(query, vocabulary_rows)
    paths = _list_item_paths(
        [
            item_id
            for item_id, datatype, _label in vocabulary_items
            if datatype == "reference"
        ],
        request.LANGUAGE_CODE,
    )
    suggestions = [
        {
            "id": str(item_id),
            "item_id": str(item_id),
            "datatype": datatype,
            "text": label,
            "addtional_info": {"path": paths[item_id]} if item_id in paths else {},
            "resourceinstanceid": None,
            "graph_icon": "",
            "graph_name": "",
        }
        for item_id, datatype, label in vocabulary_items
    ]

    mapped_labels = {label for _item_id, _datatype, label in vocabulary_items}
    record_rows += [
        vocabulary_row
        for vocabulary_row in vocabulary_rows
        if vocabulary_row["value"] not in mapped_labels
    ]

    graph_slugs = {
        record_row["graph_slug"]
        for record_row in record_rows
        if record_row["graph_slug"]
    }
    graph_info_by_slug = {
        graph["slug"]: {"icon": graph["iconclass"], "name": str(graph["name"])}
        for graph in GraphModel.objects.filter(
            isresource=True, is_active=True, slug__in=graph_slugs
        )
        .exclude(slug="arches_system_settings")
        .values("slug", "iconclass", "name")
    }
    for record_row in record_rows:
        graph_info = graph_info_by_slug.get(record_row["graph_slug"], {})
        suggestions.append(
            {
                "id": record_row["id"],
                "datatype": record_row["datatype"],
                "text": record_row["value"],
                "addtional_info": {},
                "resourceinstanceid": record_row["resourceinstanceid"],
                "graph_icon": graph_info.get("icon") or "",
                "graph_name": graph_info.get("name") or "",
            }
        )

    return suggestions
