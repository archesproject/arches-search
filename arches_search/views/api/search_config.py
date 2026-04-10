from arches.app.models import models as arches_models
from arches.app.utils.permission_backend import get_nodegroups_by_perm
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.models.models import NodeFilterConfig


class NodeFilterConfigAPI(APIBase):
    def get(self, request, graph_id):
        slug = request.GET.get("slug", "filtering")

        try:
            search_config = NodeFilterConfig.objects.get(graph_id=graph_id, slug=slug)
        except NodeFilterConfig.DoesNotExist:
            return JSONResponse({"nodes": []})

        config_nodes = search_config.config.get("nodes", [])
        if not config_nodes:
            return JSONResponse({"nodes": []})

        node_aliases = [entry["node_alias"] for entry in config_nodes]

        nodes_qs = arches_models.Node.objects.filter(
            graph_id=graph_id,
            alias__in=node_aliases,
        ).select_related("nodegroup")

        permitted_nodegroups = get_nodegroups_by_perm(
            request.user, "models.read_nodegroup"
        )
        nodes_qs = nodes_qs.filter(nodegroup__in=permitted_nodegroups)

        node_by_alias = {}
        for node in nodes_qs:
            node_by_alias[node.alias] = node

        result_nodes = []
        for entry in config_nodes:
            alias = entry["node_alias"]
            node = node_by_alias.get(alias)
            if node is None:
                continue
            result_nodes.append(
                {
                    "node_id": str(node.nodeid),
                    "node_alias": node.alias,
                    "nodegroup_id": str(node.nodegroup_id),
                    "label": entry.get("label") or str(node.name),
                    "datatype": node.datatype,
                    "config": node.config,
                    "sortorder": entry.get("sortorder", 0),
                }
            )

        return JSONResponse(
            {
                "graph_id": str(graph_id),
                "slug": slug,
                "nodes": result_nodes,
            }
        )
