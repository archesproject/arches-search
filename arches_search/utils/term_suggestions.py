import json

from django.db.models import Q

from arches_search.models.models import TermSearch
from arches_search.utils.term_matching import build_term_match_filter
from arches_controlled_lists.models import List
from arches_controlled_lists.views import ListView

from arches.app.models.models import TileModel, Node, GraphModel

# Substring matching means a short/common query can match huge numbers
# of rows, so _find_distinct_matches caps and adaptively widens the raw
# rows it examines (see its docstring) rather than scanning everything
# up front. .order_by("pk") keeps that scan deterministic — without it,
# Postgres's parallel workers can return a different row subset on every
# run of the identical query.
#
# Matches are bucketed by datatype (reference vs everything else) rather
# than pooled under one shared cap: incidental substring matches from
# the much larger term/string pool (e.g. "red" inside "prepared" or
# "credit") can otherwise fill MAX_RESULTS before the scan ever reaches
# the one reference-datatype row for the controlled term itself,
# silently dropping it from the Controlled Terms tab.
MAX_RESULTS = 100
INITIAL_RAW_MATCH_LIMIT = 1000
MAX_RAW_MATCH_LIMIT = 200000
RAW_MATCH_LIMIT_GROWTH_FACTOR = 10


def _get_item_path(list_data, value_id, language_code="en"):
    """Return a path of prefLabel values from the list name down to the item containing value_id."""
    items = list_data.get("items", [])
    items_by_id = {item["id"]: item for item in items}
    value_to_item = {v["id"]: item for item in items for v in item.get("values", [])}

    def pref_label(item):
        ret = item["id"]
        for v in item.get("values", []):
            if v["valuetype_id"] == "prefLabel":
                ret = v["value"]
                if v["language_id"] == language_code:
                    return v["value"]
        return ret

    item = value_to_item.get(value_id)

    if item is None:
        return None

    path = []
    while item is not None:
        path.append(pref_label(item))
        parent_id = item.get("parent_id")
        item = items_by_id.get(parent_id) if parent_id else None

    path.reverse()
    return [list_data["name"]] + path


def _find_distinct_matches(term_filter):
    """
    Up to MAX_RESULTS distinct (value, datatype) TermSearch rows matching
    term_filter. Widens the raw-row cap and retries when the first pass
    doesn't reach MAX_RESULTS distinct values — a fixed cap taken in
    arbitrary (pk) order can under-represent distinct values when many
    rows share the same handful of values (e.g. a controlled term
    applied to thousands of resources), since the first N raw rows can
    all be duplicates of one value. Stops once enough distinct values
    are found, every match has been examined, or MAX_RAW_MATCH_LIMIT is
    hit — that ceiling is a real trade-off, not just a safety net:
    clustering worse than it can still under-count. Raise it if that
    turns out to matter in practice.
    """
    raw_match_limit = INITIAL_RAW_MATCH_LIMIT

    while True:
        bounded_ids = list(
            TermSearch.objects.filter(term_filter)
            .order_by("pk")
            .values_list("pk", flat=True)[:raw_match_limit]
        )
        results = list(
            TermSearch.objects.filter(pk__in=bounded_ids)
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


def build_term_suggestions(query, request):
    term_filter = build_term_match_filter(query)
    results = _find_distinct_matches(
        term_filter & Q(datatype="reference")
    ) + _find_distinct_matches(term_filter & ~Q(datatype="reference"))

    graph_slugs = {result["graph_slug"] for result in results if result["graph_slug"]}
    graph_info_by_slug = {
        graph["slug"]: {"icon": graph["iconclass"], "name": str(graph["name"])}
        for graph in GraphModel.objects.filter(
            isresource=True, is_active=True, slug__in=graph_slugs
        )
        .exclude(slug="arches_system_settings")
        .values("slug", "iconclass", "name")
    }

    data = []

    for result in results:
        addtional_info = {}
        if result["datatype"] == "reference":
            try:
                tile = TileModel.objects.select_related("resourceinstance").get(
                    pk=result["tileid"]
                )
                node = Node.objects.get(
                    alias=result["node_alias"],
                    graph_id=tile.resourceinstance.graph_id,
                )

                selected_reference = None
                for reference in tile.data[str(node.pk)]:
                    for label in reference["labels"]:
                        if (
                            label["value"] == result["value"]
                            and label["valuetype_id"] == "prefLabel"
                        ):
                            selected_reference = (reference["list_id"], label["id"])
                            break

                view = ListView()
                if selected_reference:
                    list_id, label_id = selected_reference
                    serialized = view.get(request, list_id=list_id)
                    list_data = json.loads(serialized.content)
                    addtional_info["path"] = _get_item_path(
                        list_data, label_id, request.LANGUAGE_CODE
                    )

            except List.DoesNotExist:
                pass

        graph_info = graph_info_by_slug.get(result["graph_slug"], {})

        data.append(
            {
                "id": result["id"],
                "datatype": result["datatype"],
                "text": result["value"],
                "addtional_info": addtional_info,
                "resourceinstanceid": result["resourceinstanceid"],
                "graph_icon": graph_info.get("icon") or "",
                "graph_name": graph_info.get("name") or "",
            }
        )

    return data
