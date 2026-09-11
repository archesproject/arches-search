from django.http import JsonResponse
from django.views import View

from arches_search.utils.node_agnostic_search.term_suggestions import (
    build_term_suggestions,
)


class TermSuggestionView(View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        if not query:
            return JsonResponse({"results": []})

        return JsonResponse({"results": build_term_suggestions(query, request)})
