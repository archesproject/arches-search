import uuid

from django.utils.translation import gettext as _

from arches.app.utils.response import JSONResponse, JSONErrorResponse
from arches.app.views.api import APIBase

from arches_search.utils.relatable_node_tree_for_graph import (
    build_relatable_nodes_tree_response,
    build_relatable_nodes_tree_for_graph_pair,
)


class RelatableNodesTreeForGraphAPI(APIBase):
    def get(self, request, graph_id):
        try:
            target_graph_uuid = uuid.UUID(str(graph_id))
        except (TypeError, ValueError):
            return JSONErrorResponse(_("Invalid graph ID"), status=400)

        return JSONResponse(build_relatable_nodes_tree_response(target_graph_uuid))


class RelatableNodesTreeForGraphPairAPI(APIBase):
    def get(self, request, graph_id, other_graph_id):
        try:
            graph_a_uuid = uuid.UUID(str(graph_id))
            graph_b_uuid = uuid.UUID(str(other_graph_id))
        except (TypeError, ValueError):
            return JSONErrorResponse(_("Invalid graph ID"), status=400)

        return JSONResponse(
            build_relatable_nodes_tree_for_graph_pair(graph_a_uuid, graph_b_uuid)
        )
