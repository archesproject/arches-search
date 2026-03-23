import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "arches_search",
            "0009_remove_termsearch_arches_sear_value_8a4617_idx_and_more",
        ),
        ("auth", "0012_alter_user_first_name_max_length"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SavedSearch",
            fields=[
                (
                    "savedsearchid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("query_definition", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saved_searches",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "arches_search_saved_searches",
                "managed": True,
            },
        ),
        migrations.CreateModel(
            name="SharedSearchXUser",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "saved_search",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shared_users",
                        to="arches_search.savedsearch",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "arches_search_shared_searches_x_users",
                "managed": True,
            },
        ),
        migrations.CreateModel(
            name="SharedSearchXGroup",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "saved_search",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shared_groups",
                        to="arches_search.savedsearch",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="auth.group",
                    ),
                ),
            ],
            options={
                "db_table": "arches_search_shared_searches_x_groups",
                "managed": True,
            },
        ),
        migrations.AddConstraint(
            model_name="sharedsearchxuser",
            constraint=models.UniqueConstraint(
                fields=["saved_search", "user"],
                name="unique_shared_search_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="sharedsearchxgroup",
            constraint=models.UniqueConstraint(
                fields=["saved_search", "group"],
                name="unique_shared_search_group",
            ),
        ),
    ]
