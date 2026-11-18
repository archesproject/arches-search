from django.db import connection
from django.db.models import UUIDField
from django.db.models.expressions import RawSQL

from arches.app.models.models import Relation
from arches.extensions.controlled_lists.models import ListItem

NARROWER_OR_SELF = "NARROWER_OR_SELF"
NARROWER = "NARROWER"
BROADER = "BROADER"
HIERARCHY_RELATIONS = {NARROWER_OR_SELF, NARROWER, BROADER}

MAX_INLINE_HIERARCHY_IDS = 10_000

EDGES_BY_DATATYPE = {
    "reference": (
        f"SELECT parent_id AS parent, id AS child FROM {ListItem._meta.db_table}"
    ),
    "concept": (
        "SELECT conceptidfrom AS parent, conceptidto AS child "
        f"FROM {Relation._meta.db_table} "
        "WHERE relationtype IN ('narrower', 'hasTopConcept')"
    ),
}
EDGES_BY_DATATYPE["concept-list"] = EDGES_BY_DATATYPE["concept"]
VOCABULARY_DATATYPES = set(EDGES_BY_DATATYPE)

HIERARCHY_TEMPLATES = {
    NARROWER_OR_SELF: (
        "SELECT unnest(%s::uuid[]) "
        "UNION SELECT edge.child FROM ({edges}) edge JOIN related ON edge.parent = related.id"
    ),
    NARROWER: (
        "SELECT edge.child FROM ({edges}) edge WHERE edge.parent = ANY(%s::uuid[]) "
        "UNION SELECT edge.child FROM ({edges}) edge JOIN related ON edge.parent = related.id"
    ),
    BROADER: (
        "SELECT edge.parent FROM ({edges}) edge "
        "WHERE edge.child = ANY(%s::uuid[]) AND edge.parent IS NOT NULL "
        "UNION SELECT edge.parent FROM ({edges}) edge "
        "JOIN related ON edge.child = related.id WHERE edge.parent IS NOT NULL"
    ),
}


def _hierarchy_sql(datatype_name, relation):
    body = HIERARCHY_TEMPLATES[relation].format(edges=EDGES_BY_DATATYPE[datatype_name])
    return f"WITH RECURSIVE related(id) AS ({body}) SELECT id FROM related"


def expand_hierarchy(datatype_name, relation, seed_ids):
    seed_ids = [str(seed_id) for seed_id in seed_ids]
    hierarchy_sql = _hierarchy_sql(datatype_name, relation)
    with connection.cursor() as cursor:
        cursor.execute(
            f"{hierarchy_sql} LIMIT %s", [seed_ids, MAX_INLINE_HIERARCHY_IDS + 1]
        )
        related_ids = [related_row[0] for related_row in cursor.fetchall()]

    if len(related_ids) <= MAX_INLINE_HIERARCHY_IDS:
        return related_ids
    return RawSQL(hierarchy_sql, [seed_ids], output_field=UUIDField())
