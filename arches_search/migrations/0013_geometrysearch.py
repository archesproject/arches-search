import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


NEW_GEOJSON_FACETS = [
    {
        "label": {"en": "intersects with"},
        "operator": "GEO_INTERSECTS",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "{col}__intersects",
        "is_orm_template_negated": False,
        "sortorder": 0,
    },
    {
        "label": {"en": "is within"},
        "operator": "GEO_WITHIN",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "{col}__within",
        "is_orm_template_negated": False,
        "sortorder": 1,
    },
    {
        "label": {"en": "contains"},
        "operator": "GEO_CONTAINS",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "{col}__contains",
        "is_orm_template_negated": False,
        "sortorder": 2,
    },
    {
        "label": {"en": "has no value"},
        "operator": "HAS_NO_VALUE",
        "arity": 0,
        "param_formats": [],
        "orm_template": "{col}__isnull",
        "is_orm_template_negated": False,
        "sortorder": 3,
    },
    {
        "label": {"en": "has any value"},
        "operator": "HAS_ANY_VALUE",
        "arity": 0,
        "param_formats": [],
        "orm_template": "{col}__isnull",
        "is_orm_template_negated": True,
        "sortorder": 4,
    },
]

OLD_GEOJSON_OPERATORS = {
    "GEO_CONTAINS_POINT",
    "GEO_CONTAINS_LINE",
    "GEO_CONTAINS_POLYGON",
}


def migrate_geojson_facets(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    DDataType = apps.get_model("models", "DDataType")

    geo_datatype = DDataType.objects.filter(
        datatype="geojson-feature-collection"
    ).first()
    if geo_datatype is None:
        return

    geo_ct, _ = ContentType.objects.get_or_create(
        app_label="arches_search",
        model="geometrysearch",
    )

    AdvancedSearchFacet.objects.filter(
        datatype=geo_datatype,
        operator__in=OLD_GEOJSON_OPERATORS,
    ).delete()

    AdvancedSearchFacet.objects.filter(
        datatype=geo_datatype,
        operator__in={"HAS_NO_VALUE", "HAS_ANY_VALUE"},
    ).delete()

    for spec in NEW_GEOJSON_FACETS:
        AdvancedSearchFacet.objects.create(
            arity=spec["arity"],
            datatype=geo_datatype,
            label=spec["label"],
            operator=spec["operator"],
            param_formats=spec["param_formats"],
            sortorder=spec["sortorder"],
            orm_template=spec["orm_template"],
            is_orm_template_negated=spec["is_orm_template_negated"],
            target_search_model=geo_ct,
        )


def reverse_migrate_geojson_facets(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    DDataType = apps.get_model("models", "DDataType")

    geo_datatype = DDataType.objects.filter(
        datatype="geojson-feature-collection"
    ).first()
    if geo_datatype is None:
        return

    AdvancedSearchFacet.objects.filter(
        datatype=geo_datatype,
        operator__in={spec["operator"] for spec in NEW_GEOJSON_FACETS},
    ).delete()

    term_ct, _ = ContentType.objects.get_or_create(
        app_label="arches_search",
        model="termsearch",
    )

    old_facets = [
        {
            "label": {"en": "contains a point"},
            "operator": "GEO_CONTAINS_POINT",
            "arity": 1,
            "param_formats": ["{value}"],
            "orm_template": "{col}__contains",
            "is_orm_template_negated": False,
            "sortorder": 0,
        },
        {
            "label": {"en": "contains a line"},
            "operator": "GEO_CONTAINS_LINE",
            "arity": 1,
            "param_formats": ["{value}"],
            "orm_template": "{col}__contains",
            "is_orm_template_negated": False,
            "sortorder": 1,
        },
        {
            "label": {"en": "contains a polygon"},
            "operator": "GEO_CONTAINS_POLYGON",
            "arity": 1,
            "param_formats": ["{value}"],
            "orm_template": "{col}__contains",
            "is_orm_template_negated": False,
            "sortorder": 2,
        },
        {
            "label": {"en": "has no value"},
            "operator": "HAS_NO_VALUE",
            "arity": 0,
            "param_formats": [],
            "orm_template": "{col}__isnull",
            "is_orm_template_negated": False,
            "sortorder": 3,
        },
        {
            "label": {"en": "has any value"},
            "operator": "HAS_ANY_VALUE",
            "arity": 0,
            "param_formats": [],
            "orm_template": "{col}__isnull",
            "is_orm_template_negated": True,
            "sortorder": 4,
        },
    ]
    for spec in old_facets:
        AdvancedSearchFacet.objects.create(
            arity=spec["arity"],
            datatype=geo_datatype,
            label=spec["label"],
            operator=spec["operator"],
            param_formats=spec["param_formats"],
            sortorder=spec["sortorder"],
            orm_template=spec["orm_template"],
            is_orm_template_negated=spec["is_orm_template_negated"],
            target_search_model=term_ct,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("arches_search", "0012_delete_ddatatypexadvancedsearchmodel"),
    ]

    operations = [
        migrations.CreateModel(
            name="GeometrySearch",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "tileid",
                    models.ForeignKey(
                        db_column="tileid",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="models.tile",
                    ),
                ),
                (
                    "resourceinstanceid",
                    models.ForeignKey(
                        db_column="resourceinstanceid",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="models.resourceinstance",
                    ),
                ),
                ("graph_slug", models.TextField()),
                ("node_alias", models.TextField()),
                ("datatype", models.TextField()),
                (
                    "geom",
                    django.contrib.gis.db.models.fields.GeometryField(srid=4326),
                ),
            ],
            options={
                "db_table": "arches_search_geometry",
                "managed": True,
            },
        ),
        migrations.AddIndex(
            model_name="geometrysearch",
            index=models.Index(
                fields=["resourceinstanceid"],
                name="arches_sear_resourc_geo_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="geometrysearch",
            index=models.Index(
                fields=["tileid"],
                name="arches_sear_tileid_geo_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="geometrysearch",
            index=models.Index(
                fields=["node_alias"],
                name="arches_sear_nodeal_geo_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="geometrysearch",
            index=models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"],
                name="arches_sear_subject_geo_idx",
            ),
        ),
        migrations.RunPython(migrate_geojson_facets, reverse_migrate_geojson_facets),
    ]
