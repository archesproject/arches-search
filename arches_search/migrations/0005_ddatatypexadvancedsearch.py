import django.db.models.deletion
from django.db import migrations, models


def forwards_func(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    DDatatype = apps.get_model("models", "DDataType")
    DDatatypeXAdvancedSearchModel = apps.get_model(
        "arches_search", "DDatatypeXAdvancedSearchModel"
    )

    search_model_ct = {
        "termsearch": ContentType.objects.get(
            app_label="arches_search", model="termsearch"
        ),
        "numericsearch": ContentType.objects.get(
            app_label="arches_search", model="numericsearch"
        ),
        "uuidsearch": ContentType.objects.get(
            app_label="arches_search", model="uuidsearch"
        ),
        "datesearch": ContentType.objects.get(
            app_label="arches_search", model="datesearch"
        ),
        "daterangesearch": ContentType.objects.get(
            app_label="arches_search", model="daterangesearch"
        ),
        "booleansearch": ContentType.objects.get(
            app_label="arches_search", model="booleansearch"
        ),
    }

    datatype_to_model = {
        "annotation": "termsearch",
        "boolean": "booleansearch",
        "concept": "termsearch",
        "concept-list": "termsearch",
        "date": "datesearch",
        "domain-value": "termsearch",
        "domain-value-list": "termsearch",
        "edtf": "daterangesearch",
        "file-list": "termsearch",
        "geojson-feature-collection": "termsearch",
        "node-value": "termsearch",
        "non-localized-string": "termsearch",
        "number": "numericsearch",
        "reference": "termsearch",
        "resource-instance": "uuidsearch",
        "resource-instance-list": "uuidsearch",
        "semantic": "termsearch",
        "string": "termsearch",
        "url": "termsearch",
    }

    field_names = {f.name for f in DDatatype._meta.get_fields()}
    datatype_lookup_field = "datatype" if "datatype" in field_names else "name"

    for datatype_code, model_key in datatype_to_model.items():
        try:
            datatype_obj = DDatatype.objects.get(
                **{datatype_lookup_field: datatype_code}
            )
        except DDatatype.DoesNotExist:
            continue
        DDatatypeXAdvancedSearchModel.objects.update_or_create(
            datatype=datatype_obj,
            defaults={"content_type": search_model_ct[model_key]},
        )


def reverse_func(apps, schema_editor):
    DDatatype = apps.get_model("models", "DDataType")
    DDatatypeXAdvancedSearchModel = apps.get_model(
        "arches_search", "DDatatypeXAdvancedSearchModel"
    )

    datatype_codes = [
        "annotation",
        "boolean",
        "concept",
        "concept-list",
        "date",
        "domain-value",
        "domain-value-list",
        "edtf",
        "file-list",
        "geojson-feature-collection",
        "node-value",
        "non-localized-string",
        "number",
        "reference",
        "resource-instance",
        "resource-instance-list",
        "semantic",
        "string",
        "url",
    ]

    field_names = {f.name for f in DDatatype._meta.get_fields()}
    datatype_lookup_field = "datatype" if "datatype" in field_names else "name"

    DDatatypeXAdvancedSearchModel.objects.filter(
        datatype__in=DDatatype.objects.filter(
            **{f"{datatype_lookup_field}__in": datatype_codes}
        )
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("arches_search", "0004_rename_updated_indicies"),
    ]

    operations = [
        migrations.CreateModel(
            name="DDatatypeXAdvancedSearchModel",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "content_type",
                    models.ForeignKey(
                        help_text="The concrete search-table model for this data type.",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="contenttypes.contenttype",
                        verbose_name="Search Model",
                    ),
                ),
                (
                    "datatype",
                    models.OneToOneField(
                        db_column="datatypeid",
                        help_text="The data type this mapping applies to.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="models.ddatatype",
                        verbose_name="Data Type",
                    ),
                ),
            ],
            options={
                "managed": True,
                "indexes": [
                    models.Index(
                        fields=["datatype"], name="arches_sear_datatyp_bb6e0a_idx"
                    ),
                    models.Index(
                        fields=["content_type"], name="arches_sear_content_71d4aa_idx"
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("datatype",), name="unique_search_model_per_datatype"
                    )
                ],
            },
        ),
        migrations.RunPython(forwards_func, reverse_func),
    ]
