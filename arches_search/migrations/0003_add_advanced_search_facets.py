import uuid
import django.db.models.deletion

from django.db import migrations, models

from arches.app.models.system_settings import settings


# I'm unable to access `generate_uri` from ListItem here, so I'm duplicating its logic.
def generate_uri(id):
    if not id:
        raise RuntimeError("URI generation attempted without a primary key.")

    parts = [settings.PUBLIC_SERVER_ADDRESS.rstrip("/")]
    if settings.FORCE_SCRIPT_NAME:
        parts.append(settings.FORCE_SCRIPT_NAME)
    parts += ["plugins", "controlled-list-manager", "item", str(id)]

    return "/".join(parts)


def populate_datatype_advanced_search_facets(apps, schema_editor):
    List = apps.get_model("arches_controlled_lists", "List")
    ListItem = apps.get_model("arches_controlled_lists", "ListItem")
    ListItemValue = apps.get_model("arches_controlled_lists", "ListItemValue")
    DatatypeXAdvancedSearchFacets = apps.get_model(
        "arches_search", "DatatypeXAdvancedSearchFacets"
    )
    DDataType = apps.get_model("models", "DDataType")

    datatype_to_facet_map = {
        "annotation": [],
        "boolean": ["is true", "is false", "has no value", "has any value"],
        "date": [
            "=",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
            "is between",
            "is not between",
            "has no value",
            "has any value",
        ],
        "edtf": [
            "=",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
            "overlaps",
            "is during",
            "contains",
            "starts at",
            "finishes at",
            "has no value",
            "has any value",
        ],
        "file-list": [
            "size is greater than",
            "size is less than",
            "size is between",
            "count is greater than",
            "count is less than",
            "name is like",
            "extension is equals",
            "has no value",
            "has any value",
        ],
        "geojson-feature-collection": [
            "contains a point",
            "contains a line",
            "contains a polygon",
            "has no value",
            "has any value",
        ],
        "node-value": [],
        "non-localized-string": [
            "is like",
            "is not like",
            "starts with",
            "ends with",
            "equals",
            "does not equal",
            "has no value",
            "has any value",
        ],
        "number": [
            "=",
            "!=",
            "<",
            ">",
            "<=",
            ">=",
            "is between",
            "is not between",
            "has no value",
            "has any value",
        ],
        "reference": [
            "references any",
            "references all",
            "references only",
            "references none of",
            "descendant of",
            "ancestor of",
            "has no value",
            "has any value",
        ],
        "resource-instance": [
            "references any",
            "references all",
            "references only",
            "references none of",
            "has no value",
            "has any value",
        ],
        "resource-instance-list": [
            "references any",
            "references all",
            "references only",
            "references none of",
            "count is greater than",
            "count is less than",
            "has no value",
            "has any value",
        ],
        "semantic": [],
        "string": [
            "is like",
            "is not like",
            "starts with",
            "ends with",
            "equals",
            "does not equal",
            "has no value",
            "has any value",
        ],
        "url": [
            "is like",
            "is not like",
            "starts with",
            "ends with",
            "equals",
            "does not equal",
            "has no value",
            "has any value",
        ],
    }

    for datatype, facets in datatype_to_facet_map.items():
        ddatatype_instance = DDataType.objects.get(datatype=datatype)

        if List.objects.filter(name=f"Advanced Search Facets - {datatype}").exists():
            List.objects.filter(name=f"Advanced Search Facets - {datatype}").delete()

        if DatatypeXAdvancedSearchFacets.objects.filter(
            datatype=ddatatype_instance
        ).exists():
            DatatypeXAdvancedSearchFacets.objects.filter(
                datatype=ddatatype_instance
            ).delete()

        controlled_list = None
        if facets:
            controlled_list = List.objects.create(
                name=f"Advanced Search Facets - {datatype}",
                searchable=True,
            )

        DatatypeXAdvancedSearchFacets.objects.create(
            datatype=ddatatype_instance,
            controlled_list=controlled_list,
        )

        if controlled_list:
            sort_order = 0
            for facet in facets:
                list_item_id = uuid.uuid4()

                list_item = ListItem.objects.create(
                    id=list_item_id,
                    list=controlled_list,
                    sortorder=sort_order,
                    uri=generate_uri(list_item_id),
                )
                ListItemValue.objects.create(
                    list_item=list_item,
                    valuetype_id="prefLabel",
                    language_id="en",
                    value=facet,
                )
                sort_order += 1


def remove_datatype_advanced_search_facets(apps, schema_editor):
    DatatypeXAdvancedSearchFacets = apps.get_model(
        "arches_search", "DatatypeXAdvancedSearchFacets"
    )

    for (
        datatype_x_advanced_search_facets
    ) in DatatypeXAdvancedSearchFacets.objects.all():
        if datatype_x_advanced_search_facets.controlled_list:
            datatype_x_advanced_search_facets.controlled_list.delete()
        datatype_x_advanced_search_facets.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("arches_search", "0002_indexed_tables"),
        ("arches_controlled_lists", "0008_ensure_languages_in_sync"),
    ]

    operations = [
        migrations.CreateModel(
            name="DatatypeXAdvancedSearchFacets",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "controlled_list",
                    models.ForeignKey(
                        db_column="controlledlistid",
                        help_text="The controlled list associated with the data type, if applicable.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="arches_controlled_lists.list",
                        verbose_name="Controlled List",
                        null=True,
                        blank=True,
                    ),
                ),
                (
                    "datatype",
                    models.ForeignKey(
                        db_column="datatypeid",
                        help_text="The data type to which the advanced search facets apply.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="models.ddatatype",
                        verbose_name="Data Type",
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            code=populate_datatype_advanced_search_facets,
            reverse_code=remove_datatype_advanced_search_facets,
        ),
    ]
