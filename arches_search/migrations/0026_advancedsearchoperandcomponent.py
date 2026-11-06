import arches.app.models.fields.i18n
import arches.app.utils.betterJSONSerializer
import django.db.models.deletion
from django.db import migrations, models

TIME_FILTER = {
    "slug": "time",
    "label": {"en": "Time filter"},
    "icon": "pi pi-calendar",
    "component": "arches_search/AdvancedSearch/components/OperandPanel/components/TimeOperandEditor.vue",
    "sets_operator": True,
}

MAP_FILTER = {
    "slug": "map",
    "label": {"en": "Map filter"},
    "icon": "pi pi-map-marker",
    "component": "arches_search/AdvancedSearch/components/OperandPanel/components/MapOperandEditor.vue",
    "sets_operator": False,
}

OPERAND_COMPONENTS_BY_DATATYPE = {
    "date": TIME_FILTER,
    "edtf": TIME_FILTER,
    "geojson-feature-collection": MAP_FILTER,
}


def seed_operand_components(apps, schema_editor):
    AdvancedSearchOperandComponent = apps.get_model(
        "arches_search", "AdvancedSearchOperandComponent"
    )
    DDataType = apps.get_model("models", "DDataType")

    for datatype in DDataType.objects.filter(
        datatype__in=OPERAND_COMPONENTS_BY_DATATYPE.keys()
    ):
        AdvancedSearchOperandComponent.objects.create(
            datatype=datatype,
            **OPERAND_COMPONENTS_BY_DATATYPE[datatype.datatype],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("arches_search", "0025_remove_redundant_indexes"),
        ("models", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdvancedSearchOperandComponent",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "slug",
                    models.CharField(
                        help_text="Shared by data types whose values are edited the same way, e.g. date and edtf.",
                        max_length=50,
                        verbose_name="Slug",
                    ),
                ),
                (
                    "label",
                    arches.app.models.fields.i18n.I18n_TextField(
                        default="",
                        encoder=arches.app.utils.betterJSONSerializer.JSONSerializer,
                        verbose_name="Label",
                    ),
                ),
                ("icon", models.CharField(max_length=100, verbose_name="Icon")),
                (
                    "component",
                    models.CharField(
                        help_text="Path of the Vue component that edits the value in the side panel, relative to the frontend source root.",
                        max_length=255,
                        verbose_name="Component",
                    ),
                ),
                (
                    "sets_operator",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the component chooses the operator itself, so the builder does not show its own operator select.",
                        verbose_name="Sets operator",
                    ),
                ),
                (
                    "datatype",
                    models.OneToOneField(
                        db_column="datatypeid",
                        help_text="The data type whose values this component edits in the advanced search builder. Data types without one are edited inline with their node's widget.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="models.ddatatype",
                        verbose_name="Data Type",
                    ),
                ),
            ],
        ),
        migrations.RunPython(seed_operand_components, migrations.RunPython.noop),
    ]
