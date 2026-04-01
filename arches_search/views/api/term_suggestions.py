from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from arches_search.models.models import TermSearch
from django.contrib.postgres.search import SearchQuery, SearchRank


class TermSuggestionView(View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        if not query:
            return JsonResponse({"results": []})

        search_query = SearchQuery(query)
        results = (
            TermSearch.objects.values("id", "datatype", "value")
            .distinct("value", "datatype")
            .filter(search_vector=search_query)
            .order_by("value", "datatype")[:100]
        )

        data = [
            {
                "id": term["id"],
                "datatype": term["datatype"],
                "value": term["value"],
            }
            for term in results
        ]
        return JsonResponse({"results": data})
