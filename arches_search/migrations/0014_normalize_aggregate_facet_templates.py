from django.db import migrations


FORWARD_TEMPLATE_UPDATES = (
    ("reference", "REFERENCES_ALL", "AGG_SUPERSET:{col}:{p0}"),
    ("reference", "REFERENCES_ONLY", "AGG_SET_EQUAL:{col}:{p0}"),
    ("resource-instance-list", "COUNT_GREATER_THAN", "AGG_COUNT:{col}:gt:{p0}"),
    ("resource-instance-list", "COUNT_LESS_THAN", "AGG_COUNT:{col}:lt:{p0}"),
)

REVERSE_TEMPLATE_UPDATES = (
    ("reference", "REFERENCES_ALL", "HAVING_ALL:{col}:{values}"),
    ("reference", "REFERENCES_ONLY", "HAVING_ONLY:{col}:{values}"),
    ("resource-instance-list", "COUNT_GREATER_THAN", "{col_count}__gt"),
    ("resource-instance-list", "COUNT_LESS_THAN", "{col_count}__lt"),
)


def _apply_template_updates(apps, updates):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    DDataType = apps.get_model("models", "DDataType")

    datatype_by_name = {
        datatype.datatype: datatype
        for datatype in DDataType.objects.filter(
            datatype__in={datatype_name for datatype_name, _, _ in updates}
        )
    }

    for datatype_name, operator_token, orm_template in updates:
        datatype = datatype_by_name.get(datatype_name)
        if datatype is None:
            continue

        AdvancedSearchFacet.objects.filter(
            datatype=datatype,
            operator=operator_token,
        ).update(orm_template=orm_template)


def normalize_aggregate_templates(apps, schema_editor):
    _apply_template_updates(apps, FORWARD_TEMPLATE_UPDATES)


def reverse_normalize_aggregate_templates(apps, schema_editor):
    _apply_template_updates(apps, REVERSE_TEMPLATE_UPDATES)


class Migration(migrations.Migration):
    dependencies = [
        ("arches_search", "0013_geometrysearch"),
    ]

    operations = [
        migrations.RunPython(
            normalize_aggregate_templates,
            reverse_normalize_aggregate_templates,
        ),
    ]
