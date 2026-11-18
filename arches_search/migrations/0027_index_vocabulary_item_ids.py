from django.db import migrations, transaction

REFERENCE_NODES_SQL = """
SELECT graph.slug, node.alias, node.nodeid::text, node.nodegroupid
FROM nodes node
JOIN graphs graph ON graph.graphid = node.graphid
WHERE node.datatype = 'reference' AND graph.slug <> 'arches_system_settings'
"""

DELETE_NODE_ROWS_SQL = """
DELETE FROM arches_search_uuid
WHERE datatype = 'reference' AND graph_slug = %(graph_slug)s AND node_alias = %(node_alias)s
"""

INSERT_NODE_ITEM_IDS_SQL = """
INSERT INTO arches_search_uuid (tileid, resourceinstanceid, graph_slug, node_alias, datatype, value)
SELECT item_ids.tileid, item_ids.resourceinstanceid, %(graph_slug)s, %(node_alias)s,
       'reference', item_ids.list_item_id
FROM (
    SELECT DISTINCT tile.tileid, tile.resourceinstanceid,
           (label ->> 'list_item_id')::uuid AS list_item_id
    FROM tiles tile
    CROSS JOIN LATERAL jsonb_array_elements(
        CASE WHEN jsonb_typeof(tile.tiledata -> %(node_id)s) = 'array'
             THEN tile.tiledata -> %(node_id)s END
    ) reference
    CROSS JOIN LATERAL jsonb_array_elements(
        CASE WHEN jsonb_typeof(reference -> 'labels') = 'array' THEN reference -> 'labels' END
    ) label
    WHERE tile.nodegroupid = %(nodegroup_id)s AND label ->> 'list_item_id' IS NOT NULL
) item_ids
"""

REMOVE_CONCEPT_VALUE_IDS = """
DELETE FROM arches_search_uuid indexed
WHERE indexed.datatype IN ('concept', 'concept-list')
  AND EXISTS (SELECT 1 FROM "values" concept_value WHERE concept_value.valueid = indexed.value);
"""


def reindex_reference_item_ids(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(REFERENCE_NODES_SQL)
        reference_nodes = cursor.fetchall()

    nodes_by_alias = {}
    for graph_slug, node_alias, node_id, nodegroup_id in reference_nodes:
        nodes_by_alias.setdefault((graph_slug, node_alias), []).append(
            (node_id, nodegroup_id)
        )

    for (graph_slug, node_alias), nodes in nodes_by_alias.items():
        with transaction.atomic(using=connection.alias), connection.cursor() as cursor:
            cursor.execute(
                DELETE_NODE_ROWS_SQL,
                {"graph_slug": graph_slug, "node_alias": node_alias},
            )
            for node_id, nodegroup_id in nodes:
                cursor.execute(
                    INSERT_NODE_ITEM_IDS_SQL,
                    {
                        "graph_slug": graph_slug,
                        "node_alias": node_alias,
                        "node_id": node_id,
                        "nodegroup_id": nodegroup_id,
                    },
                )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("arches_search", "0026_advancedsearchoperandcomponent"),
    ]

    operations = [
        migrations.RunPython(reindex_reference_item_ids, migrations.RunPython.noop),
        migrations.RunSQL(REMOVE_CONCEPT_VALUE_IDS, migrations.RunSQL.noop),
    ]
