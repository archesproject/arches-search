"""
Which nodes a user may read.

Everything a search does with node data goes through this: clauses, term search
and suggestions, aggregations, and the values projected onto results. A node in
a nodegroup the user cannot read then behaves as if it does not exist, and all
of those agree on which nodes that is.

Arches treats a nodegroup with no explicit permissions as readable, so for most
users nothing is unreadable and these filters add no SQL.
"""

from functools import cached_property
from typing import Any, Dict, FrozenSet, List
from uuid import UUID

from django.db.models import Q, QuerySet

from arches.app.models.models import Node, NodeGroup
from arches.app.utils.permission_backend import get_nodegroups_by_perm

READ_NODEGROUP_PERMISSION = "models.read_nodegroup"


class ReadableNodes:
    """
    Worked out on first use. That walks every nodegroup, so build one per
    request and share it. user=None is a trusted in-process caller, for whom
    every node is readable.
    """

    def __init__(self, user) -> None:
        self._user = user

    def filter_nodes(self, nodes: QuerySet) -> QuerySet:
        """Narrow a Node queryset to the nodes the user may read."""
        if not self._unreadable_nodegroup_ids:
            return nodes
        return nodes.exclude(nodegroup_id__in=self._unreadable_nodegroup_ids)

    def exclude_unreadable_rows(self, rows: QuerySet) -> QuerySet:
        """
        Narrow a search index queryset, whose rows name their node by
        graph_slug and node_alias.
        """
        if not self._unreadable_aliases_by_graph_slug:
            return rows

        unreadable_rows = Q()
        for graph_slug, node_aliases in self._unreadable_aliases_by_graph_slug.items():
            unreadable_rows |= Q(graph_slug=graph_slug, node_alias__in=node_aliases)
        return rows.exclude(unreadable_rows)

    def exclude_unreadable_relations(self, relations: QuerySet) -> QuerySet:
        """Narrow a ResourceXResource queryset to links made through readable nodes."""
        if not self._unreadable_node_ids:
            return relations
        return relations.exclude(node_id__in=self._unreadable_node_ids)

    @cached_property
    def _unreadable_nodegroup_ids(self) -> FrozenSet[UUID]:
        if self._user is None:
            return frozenset()

        readable_nodegroup_ids = set(
            get_nodegroups_by_perm(self._user, READ_NODEGROUP_PERMISSION)
        )
        return frozenset(
            nodegroup_id
            for nodegroup_id in NodeGroup.objects.values_list("pk", flat=True)
            if nodegroup_id not in readable_nodegroup_ids
        )

    @cached_property
    def _unreadable_nodes(self) -> List[Dict[str, Any]]:
        if not self._unreadable_nodegroup_ids:
            return []
        return list(
            Node.objects.filter(nodegroup_id__in=self._unreadable_nodegroup_ids).values(
                "nodeid", "graph__slug", "alias"
            )
        )

    @cached_property
    def _unreadable_node_ids(self) -> FrozenSet[UUID]:
        return frozenset(node["nodeid"] for node in self._unreadable_nodes)

    @cached_property
    def _unreadable_aliases_by_graph_slug(self) -> Dict[str, List[str]]:
        aliases_by_graph_slug: Dict[str, List[str]] = {}
        for node in self._unreadable_nodes:
            aliases_by_graph_slug.setdefault(node["graph__slug"], []).append(
                node["alias"]
            )
        return aliases_by_graph_slug
