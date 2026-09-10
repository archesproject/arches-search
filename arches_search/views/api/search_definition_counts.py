import logging

from django.utils.translation import gettext as _

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.simple_search.search_queryset import build_search_queryset

logger = logging.getLogger(__name__)


class SearchDefinitionCountsAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        items = body.get("items", [])

        counts = {}
        for item in items:
            item_id = item["id"]
            try:
                counts[item_id] = build_search_queryset(
                    item["body"], request.user
                ).count()
            except Exception:
                logger.exception(
                    _("Failed to compute search definition count for item %(item_id)s")
                    % {"item_id": item_id}
                )
                counts[item_id] = None

        return JSONResponse({"counts": counts})
