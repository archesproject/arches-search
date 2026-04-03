from django.db import migrations


FORWARD_TEMPLATE_UPDATES = (
    ("reference", "REFERENCES_ALL", "AGG_SUPERSET:{col}:{p0}"),
    ("reference", "REFERENCES_ONLY", "AGG_SET_EQUAL:{col}:{p0}"),
)

REVERSE_TEMPLATE_UPDATES = (
    ("reference", "REFERENCES_ALL", "HAVING_ALL:{col}:{values}"),
    ("reference", "REFERENCES_ONLY", "HAVING_ONLY:{col}:{values}"),
)

REMOVED_RESOURCE_INSTANCE_LIST_COUNT_FACETS = (
    {
        "label": {"en": "count is greater than"},
        "operator": "COUNT_GREATER_THAN",
        "arity": 1,
        "param_formats": ["{value}"],
        "sortorder": 4,
        "orm_template": "{col_count}__gt",
        "is_orm_template_negated": False,
    },
    {
        "label": {"en": "count is less than"},
        "operator": "COUNT_LESS_THAN",
        "arity": 1,
        "param_formats": ["{value}"],
        "sortorder": 5,
        "orm_template": "{col_count}__lt",
        "is_orm_template_negated": False,
    },
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


def _remove_resource_instance_list_count_facets(apps):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    DDataType = apps.get_model("models", "DDataType")

    datatype = DDataType.objects.filter(datatype="resource-instance-list").first()
    if datatype is None:
        return

    AdvancedSearchFacet.objects.filter(
        datatype=datatype,
        operator__in={
            facet_spec["operator"]
            for facet_spec in REMOVED_RESOURCE_INSTANCE_LIST_COUNT_FACETS
        },
    ).delete()


def _restore_resource_instance_list_count_facets(apps):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    ContentType = apps.get_model("contenttypes", "ContentType")
    DDataType = apps.get_model("models", "DDataType")

    datatype = DDataType.objects.filter(datatype="resource-instance-list").first()
    if datatype is None:
        return

    target_search_model, _created = ContentType.objects.get_or_create(
        app_label="arches_search",
        model="uuidsearch",
    )

    for facet_spec in REMOVED_RESOURCE_INSTANCE_LIST_COUNT_FACETS:
        AdvancedSearchFacet.objects.update_or_create(
            datatype=datatype,
            operator=facet_spec["operator"],
            defaults={
                "arity": facet_spec["arity"],
                "label": facet_spec["label"],
                "param_formats": facet_spec["param_formats"],
                "sortorder": facet_spec["sortorder"],
                "orm_template": facet_spec["orm_template"],
                "is_orm_template_negated": facet_spec["is_orm_template_negated"],
                "target_search_model": target_search_model,
            },
        )


def normalize_aggregate_templates(apps, schema_editor):
    _apply_template_updates(apps, FORWARD_TEMPLATE_UPDATES)
    _remove_resource_instance_list_count_facets(apps)


def reverse_normalize_aggregate_templates(apps, schema_editor):
    _apply_template_updates(apps, REVERSE_TEMPLATE_UPDATES)
    _restore_resource_instance_list_count_facets(apps)


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
