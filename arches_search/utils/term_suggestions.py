import json

from django.db.models import Q

from arches.app.utils import permission_backend
from arches_search.models.models import TermSearch
from arches_search.utils.term_matching import build_term_match_filter
from arches_controlled_lists.models import List
from arches_controlled_lists.views import ListView

from arches.app.models.models import TileModel, Node, GraphModel

# Matches are bucketed by datatype (reference vs everything else) so a
# flood of incidental term matches can't crowd the one matching
# reference-datatype row out of MAX_RESULTS before the scan reaches it.
MAX_RESULTS = 100
INITIAL_RAW_MATCH_LIMIT = 1000
MAX_RAW_MATCH_LIMIT = 200000
RAW_MATCH_LIMIT_GROWTH_FACTOR = 10


def _get_item_path(list_data, value_id, language_code="en"):
    """Return the prefLabel path from the list name to value_id's item."""
    items = list_data.get("items", [])
    items_by_id = {item["id"]: item for item in items}
    value_to_item = {
        item_value["id"]: item
        for item in items
        for item_value in item.get("values", [])
    }

    def pref_label(item):
        fallback_label = item["id"]
        for item_value in item.get("values", []):
            if item_value["valuetype_id"] == "prefLabel":
                fallback_label = item_value["value"]
                if item_value["language_id"] == language_code:
                    return item_value["value"]
        return fallback_label

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


def _find_distinct_matches(term_filter, user):
    """Up to MAX_RESULTS distinct (value, datatype) rows matching term_filter.
    Widens the raw-row cap and retries if a fixed cap under-represents
    distinct values (e.g. one term applied to thousands of resources) —
    capped at MAX_RAW_MATCH_LIMIT, a real trade-off, not just a safety net.
    """
    raw_match_limit = INITIAL_RAW_MATCH_LIMIT

    while True:
        bounded_ids = list(
            TermSearch.objects.filter(term_filter)
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


def build_term_suggestions(query, request):
    term_filter = build_term_match_filter(query)
    results = _find_distinct_matches(
        term_filter & Q(datatype="reference"), request.user
    ) + _find_distinct_matches(term_filter & ~Q(datatype="reference"), request.user)

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
