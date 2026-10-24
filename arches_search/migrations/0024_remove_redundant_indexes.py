import django.db.models.deletion
from django.db import migrations, models

SEARCH_MODELS = [
    "booleansearch",
    "daterangesearch",
    "datesearch",
    "filelistsearch",
    "geometrysearch",
    "numericsearch",
    "termsearch",
    "uuidsearch",
]

IMPLICIT_FK_INDEXES = [
    (
        "arches_search_boolean",
        "resourceinstanceid",
        "arches_search_boolean_resourceinstanceid_204b4796",
    ),
    ("arches_search_boolean", "tileid", "arches_search_boolean_tileid_02a092bf"),
    (
        "arches_search_date_range",
        "resourceinstanceid",
        "arches_search_date_range_resourceinstanceid_7224796d",
    ),
    ("arches_search_date_range", "tileid", "arches_search_date_range_tileid_0b0cddda"),
    (
        "arches_search_date",
        "resourceinstanceid",
        "arches_search_date_resourceinstanceid_29b61fa1",
    ),
    ("arches_search_date", "tileid", "arches_search_date_tileid_ca0b738c"),
    (
        "arches_search_file_list",
        "resourceinstanceid",
        "arches_search_file_list_resourceinstanceid_7e1c3961",
    ),
    ("arches_search_file_list", "tileid", "arches_search_file_list_tileid_2370fe77"),
    (
        "arches_search_geometry",
        "resourceinstanceid",
        "arches_search_geometry_resourceinstanceid_07d91eb8",
    ),
    ("arches_search_geometry", "tileid", "arches_search_geometry_tileid_526e6d51"),
    (
        "arches_search_numeric",
        "resourceinstanceid",
        "arches_search_numeric_resourceinstanceid_9c18de8c",
    ),
    ("arches_search_numeric", "tileid", "arches_search_numeric_tileid_a72d9c86"),
    (
        "arches_search_terms",
        "resourceinstanceid",
        "arches_search_terms_resourceinstanceid_738f1589",
    ),
    ("arches_search_terms", "tileid", "arches_search_terms_tileid_de816fc5"),
    (
        "arches_search_uuid",
        "resourceinstanceid",
        "arches_search_uuid_resourceinstanceid_e1b3487b",
    ),
    ("arches_search_uuid", "tileid", "arches_search_uuid_tileid_c8d13027"),
]


def _state_operations():
    operations = []
    for model_name in SEARCH_MODELS:
        operations += [
            migrations.AlterField(
                model_name=model_name,
                name="resourceinstanceid",
                field=models.ForeignKey(
                    db_column="resourceinstanceid",
                    db_index=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    to="models.resourceinstance",
                ),
            ),
            migrations.AlterField(
                model_name=model_name,
                name="tileid",
                field=models.ForeignKey(
                    db_column="tileid",
                    db_index=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    to="models.tile",
                ),
            ),
        ]
    return operations


class Migration(migrations.Migration):

    dependencies = [
        ("arches_search", "0023_seed_resource_field_facets"),
    ]

    # AlterField alone would drop and re-add (and re-validate) every FK
    # constraint, so only the index drop is sent to the database.
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=_state_operations(),
            database_operations=[
                migrations.RunSQL(
                    sql=f'DROP INDEX IF EXISTS "{index_name}";',
                    reverse_sql=f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table}" ("{column}");',
                )
                for table, column, index_name in IMPLICIT_FK_INDEXES
            ],
        ),
        migrations.RunSQL(
            """
            DROP INDEX IF EXISTS term_value_upper_trgm;
            """,
            """
            CREATE INDEX IF NOT EXISTS term_value_upper_trgm
            ON arches_search_terms
            USING gin (upper(value) gin_trgm_ops);
            """,
        ),
    ]
