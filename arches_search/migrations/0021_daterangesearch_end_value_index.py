from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("arches_search", "0020_search_results_map_layer"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="daterangesearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "end_value"],
                name="arches_sear_graph_s_end_val_idx",
            ),
        ),
    ]
