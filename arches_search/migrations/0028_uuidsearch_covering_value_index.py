from django.db import migrations, models

NEW_INDEX = "arches_sear_graph_s_386784_idx"
OLD_INDEX = "arches_sear_graph_s_c0fa2b_idx"


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("arches_search", "0027_index_vocabulary_item_ids"),
    ]

    operations = [
        migrations.RunSQL(
            f"DROP INDEX CONCURRENTLY IF EXISTS {NEW_INDEX};",
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            f"CREATE INDEX CONCURRENTLY {NEW_INDEX} ON arches_search_uuid "
            "(graph_slug, node_alias, value, resourceinstanceid);",
            f"DROP INDEX CONCURRENTLY IF EXISTS {NEW_INDEX};",
            state_operations=[
                migrations.AddIndex(
                    model_name="uuidsearch",
                    index=models.Index(
                        fields=[
                            "graph_slug",
                            "node_alias",
                            "value",
                            "resourceinstanceid",
                        ],
                        name=NEW_INDEX,
                    ),
                ),
            ],
        ),
        migrations.RunSQL(
            f"DROP INDEX CONCURRENTLY IF EXISTS {OLD_INDEX};",
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {OLD_INDEX} ON arches_search_uuid "
            "(graph_slug, node_alias, value);",
            state_operations=[
                migrations.RemoveIndex(model_name="uuidsearch", name=OLD_INDEX),
            ],
        ),
    ]
