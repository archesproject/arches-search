from django.db import connection
from django.db.models import UUIDField
from django.db.models.expressions import RawSQL

from arches_search.indexing.indexing_factory import IndexingFactory

NARROWER_OR_SELF = "NARROWER_OR_SELF"
NARROWER = "NARROWER"
BROADER = "BROADER"
HIERARCHY_RELATIONS = {NARROWER_OR_SELF, NARROWER, BROADER}

MAX_INLINE_HIERARCHY_IDS = 10_000

HIERARCHY_TEMPLATES = {
    NARROWER_OR_SELF: (
        "SELECT unnest(%s::uuid[]) "
        "UNION SELECT edge.child FROM edge JOIN related ON edge.parent = related.id"
    ),
    NARROWER: (
        "SELECT edge.child FROM edge WHERE edge.parent = ANY(%s::uuid[]) "
        "UNION SELECT edge.child FROM edge JOIN related ON edge.parent = related.id"
    ),
    BROADER: (
        "SELECT edge.parent FROM edge "
        "WHERE edge.child = ANY(%s::uuid[]) AND edge.parent IS NOT NULL "
        "UNION SELECT edge.parent FROM edge "
        "JOIN related ON edge.child = related.id WHERE edge.parent IS NOT NULL"
    ),
}


def _hierarchy_sql(datatype_name, relation):
    edges = IndexingFactory().get_indexing_class(datatype_name).hierarchy_edges()
    if edges is None:
        raise ValueError(f"Datatype '{datatype_name}' has no vocabulary hierarchy.")
    edges_sql, edges_params = (
        edges.order_by().query.get_compiler(connection=connection).as_sql()
    )
    return (
        f"WITH RECURSIVE edge(parent, child) AS NOT MATERIALIZED ({edges_sql}), "
        f"related(id) AS ({HIERARCHY_TEMPLATES[relation]}) SELECT id FROM related"
    ), list(edges_params)


def expand_hierarchy(datatype_name, relation, seed_ids):
    hierarchy_sql, edges_params = _hierarchy_sql(datatype_name, relation)
    params = [*edges_params, [str(seed_id) for seed_id in seed_ids]]
    with connection.cursor() as cursor:
        cursor.execute(
            f"{hierarchy_sql} LIMIT %s", [*params, MAX_INLINE_HIERARCHY_IDS + 1]
        )
        related_ids = [related_row[0] for related_row in cursor.fetchall()]

    if len(related_ids) <= MAX_INLINE_HIERARCHY_IDS:
        return related_ids
    return RawSQL(hierarchy_sql, params, output_field=UUIDField())
