import django.contrib.postgres.indexes
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("arches_search", "0006_add_more_specific_indices_to_search_tables"),
    ]

    operations = [
        TrigramExtension(),
        migrations.RemoveIndex(
            model_name="booleansearch",
            name="arches_sear_tileid_0b23d0_idx",
        ),
        migrations.RemoveIndex(
            model_name="booleansearch",
            name="arches_sear_graph_s_cdea05_idx",
        ),
        migrations.RemoveIndex(
            model_name="booleansearch",
            name="arches_sear_graph_s_f9da56_idx",
        ),
        migrations.RemoveIndex(
            model_name="daterangesearch",
            name="arches_sear_tileid_ad3a82_idx",
        ),
        migrations.RemoveIndex(
            model_name="daterangesearch",
            name="arches_sear_graph_s_bfe863_idx",
        ),
        migrations.RemoveIndex(
            model_name="daterangesearch",
            name="arches_sear_start_v_686a18_idx",
        ),
        migrations.RemoveIndex(
            model_name="daterangesearch",
            name="arches_sear_graph_s_ffe7f6_idx",
        ),
        migrations.RemoveIndex(
            model_name="datesearch",
            name="arches_sear_tileid_8c1e1c_idx",
        ),
        migrations.RemoveIndex(
            model_name="datesearch",
            name="arches_sear_graph_s_253090_idx",
        ),
        migrations.RemoveIndex(
            model_name="datesearch",
            name="arches_sear_graph_s_7d5e61_idx",
        ),
        migrations.RemoveIndex(
            model_name="numericsearch",
            name="arches_sear_tileid_c5a973_idx",
        ),
        migrations.RemoveIndex(
            model_name="numericsearch",
            name="arches_sear_graph_s_6907be_idx",
        ),
        migrations.RemoveIndex(
            model_name="numericsearch",
            name="arches_sear_graph_s_108656_idx",
        ),
        migrations.RemoveIndex(
            model_name="termsearch",
            name="arches_sear_tileid_95c051_idx",
        ),
        migrations.RemoveIndex(
            model_name="termsearch",
            name="arches_sear_graph_s_a10c9b_idx",
        ),
        migrations.RemoveIndex(
            model_name="termsearch",
            name="arches_sear_graph_s_29d42b_idx",
        ),
        migrations.RemoveIndex(
            model_name="uuidsearch",
            name="arches_sear_tileid_8ca2c3_idx",
        ),
        migrations.RemoveIndex(
            model_name="uuidsearch",
            name="arches_sear_graph_s_ed63db_idx",
        ),
        migrations.RemoveIndex(
            model_name="uuidsearch",
            name="arches_sear_graph_s_bf96ee_idx",
        ),
        migrations.AddIndex(
            model_name="booleansearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"],
                name="arches_sear_graph_s_0d1840_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="booleansearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "tileid", "value"],
                name="arches_sear_graph_s_06e27b_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="daterangesearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"],
                name="arches_sear_graph_s_000a17_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="daterangesearch",
            index=models.Index(
                fields=[
                    "graph_slug",
                    "node_alias",
                    "tileid",
                    "start_value",
                    "end_value",
                ],
                name="arches_sear_graph_s_b00d8a_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="datesearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"],
                name="arches_sear_graph_s_be0429_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="datesearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "tileid", "value"],
                name="arches_sear_graph_s_c85445_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="numericsearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"],
                name="arches_sear_graph_s_97d9d8_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="numericsearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "tileid", "value"],
                name="arches_sear_graph_s_57080f_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="termsearch",
            index=models.Index(
                fields=["language"], name="arches_sear_languag_ecd225_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="termsearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "language", "value"],
                name="arches_sear_graph_s_2ae457_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="termsearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"],
                name="arches_sear_graph_s_3e2efc_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="termsearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "tileid", "value"],
                name="arches_sear_graph_s_a81e44_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="termsearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "tileid", "language", "value"],
                name="arches_sear_graph_s_1350d9_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="termsearch",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["value"], name="term_value_trgm", opclasses=["gin_trgm_ops"]
            ),
        ),
        migrations.RunSQL(
            """
            CREATE INDEX IF NOT EXISTS term_value_upper_trgm
            ON arches_search_terms
            USING gin (upper(value) gin_trgm_ops);
            """,
            """
            DROP INDEX IF EXISTS term_value_upper_trgm;
            """,
        ),
        migrations.AddIndex(
            model_name="uuidsearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"],
                name="arches_sear_graph_s_169917_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="uuidsearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "tileid", "value"],
                name="arches_sear_graph_s_aaf504_idx",
            ),
        ),
    ]
