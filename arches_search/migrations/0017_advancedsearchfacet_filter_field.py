from django.db import migrations, models


def set_filter_field(apps, schema_editor):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    AdvancedSearchFacet.objects.filter(datatype__datatype="string").update(
        filter_field="language"
    )


def unset_filter_field(apps, schema_editor):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    AdvancedSearchFacet.objects.filter(filter_field="language").update(filter_field="")


class Migration(migrations.Migration):

    dependencies = [
        ("arches_search", "0016_filelistsearch"),
    ]

    operations = [
        migrations.AddField(
            model_name="advancedsearchfacet",
            name="filter_field",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Name of a field on the target search model used to further filter rows based on operand metadata (e.g. 'language' for locale-keyed string operands). Empty means no additional filtering.",
                max_length=100,
                verbose_name="Filter field",
            ),
        ),
        migrations.RunPython(set_filter_field, reverse_code=unset_filter_field),
    ]
