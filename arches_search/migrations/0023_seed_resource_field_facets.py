from django.db import migrations

BOOLEAN = "django.db.models.BooleanField"
FOREIGN_KEY = "django.db.models.ForeignKey"
UUID = "django.db.models.UUIDField"
DATE_TIME = "django.db.models.DateTimeField"
DATE = "django.db.models.DateField"
TEXT = "django.db.models.TextField"
CHAR = "django.db.models.CharField"
I18N_TEXT = "arches.app.models.fields.i18n.I18n_TextField"

PRESENCE = [
    {
        "label": "has any value",
        "operator": "HAS_ANY_VALUE",
        "arity": 0,
        "orm_template": "{col}__isnull",
        "is_orm_template_negated": True,
    },
    {
        "label": "has no value",
        "operator": "HAS_NO_VALUE",
        "arity": 0,
        "orm_template": "{col}__isnull",
    },
]

EQUALITY = [
    {
        "label": "is",
        "operator": "EQUALS",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "{col}",
    },
    {
        "label": "is one of",
        "operator": "IN",
        "arity": 1,
        "param_formats": ["{values}"],
        "orm_template": "{col}__in",
    },
]

TEXT_MATCHING = EQUALITY + [
    {
        "label": "contains",
        "operator": "CONTAINS",
        "arity": 1,
        "param_formats": ["%{value}%"],
        "orm_template": "{col}__icontains",
    },
    {
        "label": "starts with",
        "operator": "STARTS_WITH",
        "arity": 1,
        "param_formats": ["{value}%"],
        "orm_template": "{col}__istartswith",
    },
]

DATE_COMPARISON = EQUALITY[:1] + [
    {
        "label": "is between",
        "operator": "RANGE",
        "arity": 2,
        "param_formats": ["from", "to"],
        "orm_template": "{col}__range",
    },
    {
        "label": "is before",
        "operator": "BEFORE",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "{col}__lt",
    },
    {
        "label": "is after",
        "operator": "AFTER",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "{col}__gt",
    },
]

# The operand comes from the request user, not the client payload.
CURRENT_USER = [
    {
        "label": "is me",
        "operator": "IS_CURRENT_USER",
        "arity": 1,
        "param_formats": ["current_user"],
        "orm_template": "{col}",
    },
    {
        "label": "is not me",
        "operator": "IS_NOT_CURRENT_USER",
        "arity": 1,
        "param_formats": ["current_user"],
        "orm_template": "{col}",
        "is_orm_template_negated": True,
    },
]

# Stored as {language: value}, so the lookup is keyed by the active language.
# {language} is substituted alongside {col} when the template is compiled.
I18N_TEXT_MATCHING = [
    {
        "label": "is",
        "operator": "EQUALS",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "{col}__{language}",
    },
    {
        "label": "contains",
        "operator": "CONTAINS",
        "arity": 1,
        "param_formats": ["%{value}%"],
        "orm_template": "{col}__{language}__icontains",
    },
    {
        "label": "starts with",
        "operator": "STARTS_WITH",
        "arity": 1,
        "param_formats": ["{value}%"],
        "orm_template": "{col}__{language}__istartswith",
    },
]

FACETS_BY_FIELD_CLASS = {
    BOOLEAN: [
        {
            "label": "is true",
            "operator": "IS_TRUE",
            "arity": 0,
            "orm_template": "{col}",
        },
        {
            "label": "is false",
            "operator": "IS_FALSE",
            "arity": 0,
            "orm_template": "{col}",
            "is_orm_template_negated": True,
        },
    ],
    FOREIGN_KEY: EQUALITY + PRESENCE + CURRENT_USER,
    UUID: EQUALITY + PRESENCE,
    DATE_TIME: DATE_COMPARISON + PRESENCE,
    DATE: DATE_COMPARISON + PRESENCE,
    TEXT: TEXT_MATCHING + PRESENCE,
    CHAR: TEXT_MATCHING + PRESENCE,
    I18N_TEXT: I18N_TEXT_MATCHING + PRESENCE,
}


def seed_resource_field_facets(apps, schema_editor):
    ResourceFieldFacet = apps.get_model("arches_search", "ResourceFieldFacet")

    for field_class, facets in FACETS_BY_FIELD_CLASS.items():
        for sortorder, facet in enumerate(facets):
            ResourceFieldFacet.objects.update_or_create(
                field_class=field_class,
                operator=facet["operator"],
                defaults={
                    "label": facet["label"],
                    "arity": facet["arity"],
                    "param_formats": facet.get("param_formats", []),
                    "orm_template": facet["orm_template"],
                    "is_orm_template_negated": facet.get(
                        "is_orm_template_negated", False
                    ),
                    "sortorder": sortorder,
                },
            )


def unseed_resource_field_facets(apps, schema_editor):
    ResourceFieldFacet = apps.get_model("arches_search", "ResourceFieldFacet")

    for field_class, facets in FACETS_BY_FIELD_CLASS.items():
        ResourceFieldFacet.objects.filter(
            field_class=field_class,
            operator__in=[facet["operator"] for facet in facets],
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("arches_search", "0022_resourcefieldfacet"),
    ]

    operations = [
        migrations.RunPython(seed_resource_field_facets, unseed_resource_field_facets),
    ]
