from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.node_alias_metadata import (
    build_node_alias_metadata_for_payload_query,
)


class NodeMetadataForPayloadAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        node_metadata = build_node_alias_metadata_for_payload_query(body)

        return JSONResponse(node_metadata)
