import uuid

from django.utils.translation import gettext as _

from arches.app.utils.response import JSONResponse, JSONErrorResponse
from arches.app.views.api import APIBase

from arches_search.utils.relatable_node_tree_for_graph import (
    build_relatable_nodes_tree_response,
)


class RelatableNodesTreeForGraphAPI(APIBase):
    def get(self, request, graph_id):
        try:
            target_graph_uuid = uuid.UUID(str(graph_id))
        except (TypeError, ValueError):
            return JSONErrorResponse(_("Invalid graph ID"), status=400)

        return JSONResponse(build_relatable_nodes_tree_response(target_graph_uuid))
