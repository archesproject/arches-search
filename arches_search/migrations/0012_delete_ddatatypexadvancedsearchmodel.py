from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("arches_search", "0011_advancedsearchfacet_target_search_model"),
    ]

    operations = [
        migrations.DeleteModel(
            name="DDatatypeXAdvancedSearchModel",
        ),
    ]
