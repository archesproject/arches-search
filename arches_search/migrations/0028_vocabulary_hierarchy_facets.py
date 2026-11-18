from django.db import migrations

VALUES_PARAM = ["{values}"]


def _facet(operator, label, orm_template, model, negated=False, arity=1):
    return {
        "operator": operator,
        "label": label,
        "orm_template": orm_template,
        "is_orm_template_negated": negated,
        "arity": arity,
        "param_formats": VALUES_PARAM if arity else [],
        "model": model,
    }


VOCABULARY_FACETS = [
    _facet(
        "REFERENCES_ANY", "references any", "NARROWER_OR_SELF:value__in", "uuidsearch"
    ),
    _facet("REFERENCES_EXACTLY", "references exactly", "value__in", "uuidsearch"),
    _facet("DESCENDANT_OF", "is narrower than", "NARROWER:value__in", "uuidsearch"),
    _facet("ANCESTOR_OF", "is broader than", "BROADER:value__in", "uuidsearch"),
    _facet(
        "REFERENCES_NONE_OF",
        "references none of",
        "NARROWER_OR_SELF:value__in",
        "uuidsearch",
        negated=True,
    ),
    _facet(
        "REFERENCES_ALL", "references all", "HAVING_ALL:value:{value0}", "uuidsearch"
    ),
    _facet(
        "REFERENCES_ONLY", "references only", "HAVING_ONLY:value:{value0}", "uuidsearch"
    ),
    _facet("HAS_NO_VALUE", "has no value", "value__isnull", "termsearch", arity=0),
    _facet(
        "HAS_ANY_VALUE",
        "has any value",
        "value__isnull",
        "termsearch",
        negated=True,
        arity=0,
    ),
]

LEGACY_REFERENCE_FACETS = [
    _facet("REFERENCES_ANY", "references any", "value__in", "termsearch"),
    _facet(
        "REFERENCES_ALL", "references all", "HAVING_ALL:value:{value0}", "termsearch"
    ),
    _facet(
        "REFERENCES_ONLY", "references only", "HAVING_ONLY:value:{value0}", "termsearch"
    ),
    _facet(
        "REFERENCES_NONE_OF",
        "references none of",
        "value__in",
        "termsearch",
        negated=True,
    ),
    _facet("DESCENDANT_OF", "descendant of", "value__in", "termsearch"),
    _facet("ANCESTOR_OF", "ancestor of", "value__in", "termsearch"),
    _facet("HAS_NO_VALUE", "has no value", "value__isnull", "termsearch", arity=0),
    _facet(
        "HAS_ANY_VALUE",
        "has any value",
        "value__isnull",
        "termsearch",
        negated=True,
        arity=0,
    ),
]

FACETS_BY_DATATYPE = {
    "reference": VOCABULARY_FACETS,
    "concept": VOCABULARY_FACETS,
    "concept-list": VOCABULARY_FACETS,
}
OPERATORS_TO_REPLACE = {
    spec["operator"] for spec in VOCABULARY_FACETS + LEGACY_REFERENCE_FACETS
}
LEGACY_FACETS_BY_DATATYPE = {"reference": LEGACY_REFERENCE_FACETS}


def _sync_facets(apps, facets_by_datatype):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    ContentType = apps.get_model("contenttypes", "ContentType")
    DDataType = apps.get_model("models", "DDataType")

    AdvancedSearchFacet.objects.filter(
        datatype__datatype__in=FACETS_BY_DATATYPE, operator__in=OPERATORS_TO_REPLACE
    ).delete()

    for datatype in DDataType.objects.filter(datatype__in=facets_by_datatype):
        for sortorder, spec in enumerate(facets_by_datatype[datatype.datatype]):
            target_search_model, _created = ContentType.objects.get_or_create(
                app_label="arches_search", model=spec["model"]
            )
            AdvancedSearchFacet.objects.create(
                datatype=datatype,
                arity=spec["arity"],
                label={"en": spec["label"]},
                operator=spec["operator"],
                param_formats=spec["param_formats"],
                sortorder=sortorder,
                orm_template=spec["orm_template"],
                is_orm_template_negated=spec["is_orm_template_negated"],
                target_search_model=target_search_model,
            )


def forwards(apps, schema_editor):
    _sync_facets(apps, FACETS_BY_DATATYPE)


def backwards(apps, schema_editor):
    _sync_facets(apps, LEGACY_FACETS_BY_DATATYPE)


class Migration(migrations.Migration):

    dependencies = [
        ("arches_search", "0027_uuidsearch_covering_value_index"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
