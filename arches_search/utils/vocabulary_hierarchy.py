from django.db import connection
from django.db.models import Expression, UUIDField

from arches.app.models.models import Relation
from arches.extensions.controlled_lists.models import ListItem

NARROWER_OR_SELF = "NARROWER_OR_SELF"
NARROWER = "NARROWER"
BROADER = "BROADER"
HIERARCHY_RELATIONS = {NARROWER_OR_SELF, NARROWER, BROADER}

LITERAL_BRANCH_LIMIT = 10_000

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

BRANCH_TEMPLATES = {
    NARROWER_OR_SELF: (
        "SELECT unnest(%s::uuid[]) "
        "UNION SELECT edge.child FROM ({edges}) edge JOIN branch ON edge.parent = branch.id"
    ),
    NARROWER: (
        "SELECT edge.child FROM ({edges}) edge WHERE edge.parent = ANY(%s::uuid[]) "
        "UNION SELECT edge.child FROM ({edges}) edge JOIN branch ON edge.parent = branch.id"
    ),
    BROADER: (
        "SELECT edge.parent FROM ({edges}) edge "
        "WHERE edge.child = ANY(%s::uuid[]) AND edge.parent IS NOT NULL "
        "UNION SELECT edge.parent FROM ({edges}) edge "
        "JOIN branch ON edge.child = branch.id WHERE edge.parent IS NOT NULL"
    ),
}


def _branch_sql(datatype_name, relation):
    body = BRANCH_TEMPLATES[relation].format(edges=EDGES_BY_DATATYPE[datatype_name])
    return f"WITH RECURSIVE branch(id) AS ({body}) SELECT id FROM branch"


class Branch(Expression):
    output_field = UUIDField()

    def __init__(self, datatype_name, relation, seed_ids):
        super().__init__()
        self.sql = _branch_sql(datatype_name, relation)
        self.seed_ids = seed_ids

    def as_sql(self, compiler, connection):
        return f"({self.sql})", [self.seed_ids]


def expand_branch(datatype_name, relation, seed_ids):
    seed_ids = [str(seed_id) for seed_id in seed_ids]
    with connection.cursor() as cursor:
        cursor.execute(
            f"{_branch_sql(datatype_name, relation)} LIMIT %s",
            [seed_ids, LITERAL_BRANCH_LIMIT + 1],
        )
        branch_ids = [branch_row[0] for branch_row in cursor.fetchall()]

    if len(branch_ids) <= LITERAL_BRANCH_LIMIT:
        return branch_ids
    return Branch(datatype_name, relation, seed_ids)
