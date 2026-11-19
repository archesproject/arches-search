from django.contrib.postgres.operations import (
    AddIndexConcurrently,
    RemoveIndexConcurrently,
)
from django.db import migrations, models

NEW_INDEX = "arches_sear_graph_s_386784_idx"


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("arches_search", "0026_advancedsearchoperandcomponent"),
    ]

    operations = [
        migrations.RunSQL(
            f"DROP INDEX CONCURRENTLY IF EXISTS {NEW_INDEX};",
            migrations.RunSQL.noop,
        ),
        AddIndexConcurrently(
            model_name="uuidsearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "value", "resourceinstanceid"],
                name=NEW_INDEX,
            ),
        ),
        RemoveIndexConcurrently(
            model_name="uuidsearch",
            name="arches_sear_graph_s_c0fa2b_idx",
        ),
    ]
