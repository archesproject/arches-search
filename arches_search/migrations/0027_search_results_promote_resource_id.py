from django.db import migrations

SOURCE_NAME = "arches-search-results"
PROMOTED_FEATURE_ID = "resourceinstanceid"


def promote_resource_id(apps, schema_editor):
    MapSource = apps.get_model("models", "MapSource")
    for map_source in MapSource.objects.filter(name=SOURCE_NAME):
        map_source.source = {**map_source.source, "promoteId": PROMOTED_FEATURE_ID}
        map_source.save()


def demote_resource_id(apps, schema_editor):
    MapSource = apps.get_model("models", "MapSource")
    for map_source in MapSource.objects.filter(name=SOURCE_NAME):
        map_source.source = {
            key: value for key, value in map_source.source.items() if key != "promoteId"
        }
        map_source.save()


class Migration(migrations.Migration):

    dependencies = [
        ("arches_search", "0026_advancedsearchoperandcomponent"),
    ]

    operations = [
        migrations.RunPython(promote_resource_id, demote_resource_id),
    ]
