import json
from django.http import JsonResponse
from django.views import View

from arches_search.models.models import TermSearch
from django.contrib.postgres.search import SearchQuery
from arches_controlled_lists.models import List
from arches_controlled_lists.views import ListView

from arches.app.models.models import TileModel, Node, ResourceInstance


def get_item_path(list_data, value_id, language_code="en"):
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


class TermSuggestionView(View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        if not query:
            return JsonResponse({"results": []})

        search_query = SearchQuery(query)
        results = (
            TermSearch.objects.values(
                "id", "datatype", "value", "node_alias", "tileid", "resourceinstanceid"
            )
            .distinct("value", "datatype")
            .filter(search_vector=search_query)
            .order_by("value", "datatype")[:100]
        )

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
                        addtional_info["path"] = get_item_path(
                            list_data, label_id, request.LANGUAGE_CODE
                        )

                except List.DoesNotExist:
                    pass

            data.append(
                {
                    "id": result["id"],
                    "datatype": result["datatype"],
                    "text": result["value"],
                    "addtional_info": addtional_info,
                }
            )

        return JsonResponse({"results": data})
