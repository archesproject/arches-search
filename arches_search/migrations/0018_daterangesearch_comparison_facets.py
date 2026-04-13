from django.db import migrations, models


DATE_RANGE_COMPARISON_FACETS = [
    {
        "operator": "EQUALS",
        "arity": 1,
        "orm_template": "AND:start_value__lte:{value};end_value__gte:{value}",
        "is_orm_template_negated": False,
        "label": "=",
        "sortorder_offset": 100,
    },
    {
        "operator": "NOT_EQUALS",
        "arity": 1,
        "orm_template": "AND:start_value__lte:{value};end_value__gte:{value}",
        "is_orm_template_negated": True,
        "label": "!=",
        "sortorder_offset": 101,
    },
    {
        "operator": "LESS_THAN",
        "arity": 1,
        "orm_template": "end_value__lt",
        "is_orm_template_negated": False,
        "label": "<",
        "sortorder_offset": 102,
    },
    {
        "operator": "LESS_THAN_OR_EQUALS",
        "arity": 1,
        "orm_template": "end_value__lte",
        "is_orm_template_negated": False,
        "label": "<=",
        "sortorder_offset": 103,
    },
    {
        "operator": "GREATER_THAN",
        "arity": 1,
        "orm_template": "start_value__gt",
        "is_orm_template_negated": False,
        "label": ">",
        "sortorder_offset": 104,
    },
    {
        "operator": "GREATER_THAN_OR_EQUALS",
        "arity": 1,
        "orm_template": "start_value__gte",
        "is_orm_template_negated": False,
        "label": ">=",
        "sortorder_offset": 105,
    },
    {
        "operator": "BETWEEN",
        "arity": 2,
        "orm_template": "AND:start_value__lte:{value1};end_value__gte:{value0}",
        "is_orm_template_negated": False,
        "label": "is between",
        "sortorder_offset": 106,
    },
    {
        "operator": "NOT_BETWEEN",
        "arity": 2,
        "orm_template": "AND:start_value__lte:{value1};end_value__gte:{value0}",
        "is_orm_template_negated": True,
        "label": "is not between",
        "sortorder_offset": 107,
    },
]


def seed_daterangesearch_comparison_facets(apps, schema_editor):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    DDataType = apps.get_model("models", "DDataType")
    ContentType = apps.get_model("contenttypes", "ContentType")

    edtf_datatype = DDataType.objects.get(datatype="edtf")
    date_range_content_type, _ = ContentType.objects.get_or_create(
        app_label="arches_search",
        model="daterangesearch",
    )

    for facet_spec in DATE_RANGE_COMPARISON_FACETS:
        AdvancedSearchFacet.objects.create(
            arity=facet_spec["arity"],
            datatype=edtf_datatype,
            label={"en": facet_spec["label"]},
            operator=facet_spec["operator"],
            param_formats=[],
            sortorder=facet_spec["sortorder_offset"],
            orm_template=facet_spec["orm_template"],
            is_orm_template_negated=facet_spec["is_orm_template_negated"],
            target_search_model=date_range_content_type,
        )


def remove_daterangesearch_comparison_facets(apps, schema_editor):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    ContentType = apps.get_model("contenttypes", "ContentType")

    try:
        date_range_content_type = ContentType.objects.get(
            app_label="arches_search",
            model="daterangesearch",
        )
    except ContentType.DoesNotExist:
        return

    operators_to_remove = {spec["operator"] for spec in DATE_RANGE_COMPARISON_FACETS}
    AdvancedSearchFacet.objects.filter(
        target_search_model=date_range_content_type,
        operator__in=operators_to_remove,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("arches_search", "0017_advancedsearchfacet_filter_field"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="advancedsearchfacet",
            name="unique_operator_per_datatype",
        ),
        migrations.RemoveConstraint(
            model_name="advancedsearchfacet",
            name="unique_sortorder_per_datatype",
        ),
        migrations.AddConstraint(
            model_name="advancedsearchfacet",
            constraint=models.UniqueConstraint(
                fields=["datatype", "operator", "target_search_model"],
                name="unique_operator_per_datatype_and_model",
            ),
        ),
        migrations.AddConstraint(
            model_name="advancedsearchfacet",
            constraint=models.UniqueConstraint(
                fields=["datatype", "sortorder", "target_search_model"],
                name="unique_sortorder_per_datatype_and_model",
            ),
        ),
        migrations.RunPython(
            seed_daterangesearch_comparison_facets,
            remove_daterangesearch_comparison_facets,
        ),
    ]
