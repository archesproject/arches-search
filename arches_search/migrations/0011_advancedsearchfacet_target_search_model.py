import django.db.models.deletion
from django.db import migrations, models


EDTF_DATE_OPERATORS = {
    "EQUALS",
    "NOT_EQUALS",
    "LESS_THAN",
    "GREATER_THAN",
    "LESS_THAN_OR_EQUALS",
    "GREATER_THAN_OR_EQUALS",
    "HAS_NO_VALUE",
    "HAS_ANY_VALUE",
}

EDTF_RANGE_OPERATORS = {
    "OVERLAPS",
    "DURING",
    "CONTAINS",
    "STARTS_AT",
    "FINISHES_AT",
}


def populate_target_search_models(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")

    def get_content_type(model_name: str):
        content_type, _created = ContentType.objects.get_or_create(
            app_label="arches_search",
            model=model_name,
        )
        return content_type

    search_model_ct = {
        "termsearch": get_content_type("termsearch"),
        "numericsearch": get_content_type("numericsearch"),
        "uuidsearch": get_content_type("uuidsearch"),
        "datesearch": get_content_type("datesearch"),
        "daterangesearch": get_content_type("daterangesearch"),
        "booleansearch": get_content_type("booleansearch"),
    }

    datatype_to_model = {
        "boolean": "booleansearch",
        "date": "datesearch",
        "file-list": "termsearch",
        "geojson-feature-collection": "termsearch",
        "non-localized-string": "termsearch",
        "number": "numericsearch",
        "reference": "termsearch",
        "resource-instance": "uuidsearch",
        "resource-instance-list": "uuidsearch",
        "string": "termsearch",
        "url": "termsearch",
    }

    for facet in AdvancedSearchFacet.objects.select_related("datatype"):
        datatype_name = getattr(facet.datatype, "datatype", None) or getattr(
            facet.datatype, "name", None
        )
        if datatype_name == "edtf":
            if facet.operator in EDTF_DATE_OPERATORS:
                model_key = "datesearch"
            elif facet.operator in EDTF_RANGE_OPERATORS:
                model_key = "daterangesearch"
            else:
                continue
        else:
            model_key = datatype_to_model.get(datatype_name)

        if model_key is None:
            continue

        facet.target_search_model = search_model_ct[model_key]
        facet.save(update_fields=["target_search_model"])


class Migration(migrations.Migration):
    dependencies = [
        ("arches_search", "0010_saved_searches"),
    ]

    operations = [
        migrations.AddField(
            model_name="advancedsearchfacet",
            name="target_search_model",
            field=models.ForeignKey(
                blank=True,
                help_text="The concrete search-table model this facet should query against.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="contenttypes.contenttype",
                verbose_name="Target Search Model",
            ),
        ),
        migrations.RunPython(populate_target_search_models, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="advancedsearchfacet",
            name="target_search_model",
            field=models.ForeignKey(
                help_text="The concrete search-table model this facet should query against.",
                on_delete=django.db.models.deletion.PROTECT,
                to="contenttypes.contenttype",
                verbose_name="Target Search Model",
            ),
        ),
    ]
