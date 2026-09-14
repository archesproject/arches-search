import logging

from django.utils.translation import gettext as _

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.search import (
    SearchCompiler,
    SearchPayload,
    validate_search_payload,
)

logger = logging.getLogger(__name__)


class SearchDefinitionCountsAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        items = body.get("items", [])

        counts = {}
        for item in items:
            item_id = item["id"]
            try:
                search_payload = SearchPayload.from_body(item["body"])
                validate_search_payload(search_payload)
                search_result = SearchCompiler(search_payload, request.user).compile()
                counts[item_id] = search_result.scoped_count
            except Exception:
                logger.exception(
                    _("Failed to compute search definition count for item %(item_id)s")
                    % {"item_id": item_id}
                )
                counts[item_id] = None

        return JSONResponse({"counts": counts})
