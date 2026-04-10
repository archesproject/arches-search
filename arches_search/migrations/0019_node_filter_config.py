import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("models", "0001_initial"),
        ("arches_search", "0018_daterangesearch_comparison_facets"),
    ]

    operations = [
        migrations.CreateModel(
            name="NodeFilterConfig",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("config", models.JSONField(default=dict)),
                (
                    "slug",
                    models.TextField(default="filtering"),
                ),
                (
                    "graph",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="node_filter_configs",
                        to="models.graphmodel",
                    ),
                ),
            ],
            options={
                "db_table": "arches_search_node_filter_config",
                "managed": True,
            },
        ),
        migrations.AddConstraint(
            model_name="nodefilterconfig",
            constraint=models.UniqueConstraint(
                fields=["graph", "slug"],
                name="unique_node_filter_config_slug_per_graph",
            ),
        ),
    ]
