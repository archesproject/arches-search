from django.db import migrations


# Maps each (model_name, old_template) pair to the replacement template.
# model_name is the lowercase label of the target ContentType.
# These take priority over the universal replacements below.
TEMPLATE_REPLACEMENTS_BY_MODEL = {
    # GeometrySearch uses `geom` as its value column.
    ("geometrysearch", "{col}"): "geom",
    ("geometrysearch", "{col}__contains"): "geom__contains",
    ("geometrysearch", "{col}__intersects"): "geom__intersects",
    ("geometrysearch", "{col}__within"): "geom__within",
    ("geometrysearch", "{col}__isnull"): "geom__isnull",
    # DateRangeSearch uses start_value / end_value.
    ("daterangesearch", "{col_start}"): "start_value",
    ("daterangesearch", "{col_end}"): "end_value",
    (
        "daterangesearch",
        "AND:{col_start}__lte:{p1};{col_end}__gte:{p0}",
    ): "AND:start_value__lte:{value1};end_value__gte:{value0}",
    (
        "daterangesearch",
        "AND:{col_start}__lte:{p0};{col_end}__gte:{p1}",
    ): "AND:start_value__lte:{value0};end_value__gte:{value1}",
    (
        "daterangesearch",
        "AND:{col_start}__gte:{p0};{col_end}__lte:{p1}",
    ): "AND:start_value__gte:{value0};end_value__lte:{value1}",
    # DateSearch uses `value`.
    ("datesearch", "{col_start}"): "value",
    ("datesearch", "{col_end}"): "value",
}

# Templates that are identical across all remaining models
# (all use a `value` column or are aggregate/structural templates).
#
# Note: migration 0014 converted {col_count}__gt → AGG_COUNT:{col}:gt:{p0}
# and HAVING_ALL:{col}:{values} → AGG_SUPERSET:{col}:{p0}, so the inputs
# here are the post-0014 forms.
TEMPLATE_REPLACEMENTS_UNIVERSAL = {
    "{col}": "value",
    "{col}__gt": "value__gt",
    "{col}__gte": "value__gte",
    "{col}__lt": "value__lt",
    "{col}__lte": "value__lte",
    "{col}__isnull": "value__isnull",
    "{col}__exact": "value__exact",
    "{col}__iexact": "value__iexact",
    "{col}__icontains": "value__icontains",
    "{col}__istartswith": "value__istartswith",
    "{col}__iendswith": "value__iendswith",
    "{col}__in": "value__in",
    "{col}__contains": "value__contains",
    "{col}__range": "value__range",
    # Aggregate: consolidate AGG_SUPERSET/SET_EQUAL → HAVING_ALL/ONLY with {value0}
    "AGG_SUPERSET:{col}:{p0}": "HAVING_ALL:value:{value0}",
    "AGG_SET_EQUAL:{col}:{p0}": "HAVING_ONLY:value:{value0}",
    # Count aggregate: normalise to canonical AGG_COUNT:: form with {value}
    "AGG_COUNT:{col}:gt:{p0}": "AGG_COUNT::gt:{value}",
    "AGG_COUNT:{col}:lt:{p0}": "AGG_COUNT::lt:{value}",
}


def normalise_orm_templates(apps, schema_editor):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")

    for facet in AdvancedSearchFacet.objects.select_related("target_search_model"):
        model_name = (
            facet.target_search_model.model if facet.target_search_model_id else None
        )
        old_template = facet.orm_template

        # Check model-specific replacements first.
        new_template = TEMPLATE_REPLACEMENTS_BY_MODEL.get((model_name, old_template))

        # Fall back to universal replacements.
        if new_template is None:
            new_template = TEMPLATE_REPLACEMENTS_UNIVERSAL.get(old_template)

        if new_template is not None and new_template != old_template:
            facet.orm_template = new_template
            facet.save(update_fields=["orm_template"])


def reverse_normalise_orm_templates(apps, schema_editor):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")

    reverse_by_model = {
        (model_name, new_template): old_template
        for (
            model_name,
            old_template,
        ), new_template in TEMPLATE_REPLACEMENTS_BY_MODEL.items()
    }
    reverse_universal = {
        new_template: old_template
        for old_template, new_template in TEMPLATE_REPLACEMENTS_UNIVERSAL.items()
    }

    for facet in AdvancedSearchFacet.objects.select_related("target_search_model"):
        model_name = (
            facet.target_search_model.model if facet.target_search_model_id else None
        )
        current_template = facet.orm_template

        old_template = reverse_by_model.get((model_name, current_template))
        if old_template is None:
            old_template = reverse_universal.get(current_template)

        if old_template is not None and old_template != current_template:
            facet.orm_template = old_template
            facet.save(update_fields=["orm_template"])


class Migration(migrations.Migration):
    dependencies = [
        ("arches_search", "0014_normalize_aggregate_facet_templates"),
    ]

    operations = [
        migrations.RunPython(
            normalise_orm_templates,
            reverse_normalise_orm_templates,
        ),
    ]
