import logging

from django.utils.translation import gettext as _

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search.advanced_search import (
    SearchCompiler,
    validate_node_agnostic_filters,
)
from arches_search.views.api.search import build_search_payload

logger = logging.getLogger(__name__)


class SearchDefinitionCountsAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        items = body.get("items", [])

        counts = {}
        for item in items:
            item_id = item["id"]
            try:
                item_body = item["body"]
                validate_node_agnostic_filters(item_body.get("node_agnostic_filters"))
                search_result = SearchCompiler(
                    build_search_payload(item_body), request.user
                ).compile()
                counts[item_id] = search_result.scoped_count
            except Exception:
                logger.exception(
                    _("Failed to compute search definition count for item %(item_id)s")
                    % {"item_id": item_id}
                )
                counts[item_id] = None

        return JSONResponse({"counts": counts})
