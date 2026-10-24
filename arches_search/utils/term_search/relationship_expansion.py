from django.conf import settings
from django.db.models import Expression, UUIDField
from django.db.models.expressions import RawSQL

from arches.app.models.models import ResourceInstance, ResourceXResource

SEED_CTE_NAME = "term_direct_matches"
FRONTIER_CTE_PREFIX = "term_frontier_"


class MaterializedUnion(Expression):
    """
    A parenthesized `WITH name AS MATERIALIZED (a UNION b ...) ... UNION ...`
    subquery, for use as the right-hand side of an `__in` lookup.

    Each named set is computed once however many times later sets reference
    it (see set_reference), and sets are combined with UNION rather than OR'd
    `IN` lists, so Postgres can plan the semi-joins instead of falling back to
    per-row SubPlans.
    """

    output_field = UUIDField()

    def __init__(self, named_sets, final_set):
        super().__init__()
        self.named_sets = named_sets
        self.final_set = final_set

    # Wraps unhashable querysets; identity semantics are enough.
    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    @staticmethod
    def _compile_union(querysets, connection):
        sql_parts = []
        params = []
        for queryset in querysets:
            sql, query_params = queryset.query.get_compiler(
                connection=connection
            ).as_sql()
            sql_parts.append(sql)
            params.extend(query_params)
        return " UNION ".join(sql_parts), params

    def as_sql(self, compiler, connection):
        cte_parts = []
        params = []
        for name, querysets in self.named_sets:
            sql, set_params = self._compile_union(querysets, connection)
            cte_parts.append(f"{name}(resourceinstanceid) AS MATERIALIZED ({sql})")
            params.extend(set_params)
        final_sql, final_params = self._compile_union(self.final_set, connection)
        params.extend(final_params)
        return f"(WITH {', '.join(cte_parts)} {final_sql})", params


def set_reference(name):
    """Right-hand side of an `__in` lookup selecting from a named set."""
    return RawSQL(f"SELECT resourceinstanceid FROM {name}", [])


def expand_matches_via_relationships(
    direct_match_resource_ids, target_graphid, max_hops, readable_nodes
):
    """
    Returns target_graphid resources that are themselves in direct_match_resource_ids
    (any graph), or reachable from one within max_hops via resource_x_resource.

    Links made through a node the user cannot read are not followed.
    """
    if not 0 <= max_hops <= settings.TERM_SEARCH_MAX_HOPS:
        raise ValueError(
            f"max_hops must be between 0 and {settings.TERM_SEARCH_MAX_HOPS}"
        )

    relations = readable_nodes.exclude_unreadable_relations(
        ResourceXResource.objects.all()
    )
    seed_reference = set_reference(SEED_CTE_NAME)
    named_sets = [
        (
            SEED_CTE_NAME,
            [direct_match_resource_ids.values("resourceinstanceid")],
        )
    ]
    target_graph_match_sets = [
        ResourceInstance.objects.filter(
            resourceinstanceid__in=seed_reference, graph_id=target_graphid
        ).values("resourceinstanceid")
    ]

    frontier_name = f"{FRONTIER_CTE_PREFIX}0"
    named_sets.append(
        (
            frontier_name,
            [
                ResourceInstance.objects.filter(resourceinstanceid__in=seed_reference)
                .exclude(graph_id=target_graphid)
                .values("resourceinstanceid")
            ],
        )
    )

    for hop_number in range(max_hops):
        frontier_reference = set_reference(frontier_name)
        target_graph_match_sets.append(
            relations.filter(
                to_resource_id__in=frontier_reference,
                from_resource_graph_id=target_graphid,
            ).values("from_resource_id")
        )
        target_graph_match_sets.append(
            relations.filter(
                from_resource_id__in=frontier_reference,
                to_resource_graph_id=target_graphid,
            ).values("to_resource_id")
        )
        if hop_number < max_hops - 1:
            frontier_name = f"{FRONTIER_CTE_PREFIX}{hop_number + 1}"
            named_sets.append(
                (
                    frontier_name,
                    [
                        relations.filter(to_resource_id__in=frontier_reference)
                        .exclude(from_resource_graph_id=target_graphid)
                        .values("from_resource_id"),
                        relations.filter(from_resource_id__in=frontier_reference)
                        .exclude(to_resource_graph_id=target_graphid)
                        .values("to_resource_id"),
                    ],
                )
            )

    return ResourceInstance.objects.filter(
        resourceinstanceid__in=MaterializedUnion(named_sets, target_graph_match_sets)
    )
