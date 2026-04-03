from pathlib import Path

import django.contrib.postgres.indexes
import django.db.models.deletion
from django.db import migrations, models


FILE_LIST_FACET_SPECS = (
    {
        "operator": "FILE_SIZE_GREATER_THAN",
        "label": "size is greater than",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "file_size__gt",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_SIZE_LESS_THAN",
        "label": "size is less than",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "file_size__lt",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_SIZE_BETWEEN",
        "label": "size is between",
        "arity": 2,
        "param_formats": ["{value0}", "{value1}"],
        "orm_template": "file_size__range",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_NAME_LIKE",
        "label": "name is like",
        "arity": 1,
        "param_formats": ["%{value}%"],
        "orm_template": "value__icontains",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_EXTENSION_EQUALS",
        "label": "extension equals",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "extension__iexact",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_MODIFIED_BEFORE",
        "label": "modified before",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "modified_at__lt",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_MODIFIED_AFTER",
        "label": "modified after",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "modified_at__gt",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_MODIFIED_BETWEEN",
        "label": "modified between",
        "arity": 2,
        "param_formats": ["{value0}", "{value1}"],
        "orm_template": "modified_at__range",
        "is_orm_template_negated": False,
    },
    {
        "operator": "HAS_NO_VALUE",
        "label": "has no value",
        "arity": 0,
        "param_formats": [],
        "orm_template": "value__isnull",
        "is_orm_template_negated": False,
    },
    {
        "operator": "HAS_ANY_VALUE",
        "label": "has any value",
        "arity": 0,
        "param_formats": [],
        "orm_template": "value__isnull",
        "is_orm_template_negated": True,
    },
)


LEGACY_FILE_LIST_FACET_SPECS = (
    {
        "operator": "FILE_SIZE_GREATER_THAN",
        "label": "size is greater than",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "value__gt",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_SIZE_LESS_THAN",
        "label": "size is less than",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "value__lt",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_SIZE_BETWEEN",
        "label": "size is between",
        "arity": 2,
        "param_formats": ["{value0}", "{value1}"],
        "orm_template": "value__range",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_NAME_LIKE",
        "label": "name is like",
        "arity": 1,
        "param_formats": ["%{value}%"],
        "orm_template": "value__icontains",
        "is_orm_template_negated": False,
    },
    {
        "operator": "FILE_EXTENSION_EQUALS",
        "label": "extension equals",
        "arity": 1,
        "param_formats": ["{value}"],
        "orm_template": "value__iexact",
        "is_orm_template_negated": False,
    },
    {
        "operator": "HAS_NO_VALUE",
        "label": "has no value",
        "arity": 0,
        "param_formats": [],
        "orm_template": "value__isnull",
        "is_orm_template_negated": False,
    },
    {
        "operator": "HAS_ANY_VALUE",
        "label": "has any value",
        "arity": 0,
        "param_formats": [],
        "orm_template": "value__isnull",
        "is_orm_template_negated": True,
    },
)


def populate_file_list_rows(apps, schema_editor):
    FileListSearch = apps.get_model("arches_search", "FileListSearch")
    Node = apps.get_model("models", "Node")
    TileModel = apps.get_model("models", "TileModel")

    batch = []
    batch_size = 1000

    for node in Node.objects.filter(datatype="file-list").select_related("graph"):
        nodeid_text = str(node.nodeid)
        tile_queryset = TileModel.objects.filter(nodegroup_id=node.nodegroup_id).only(
            "tileid",
            "resourceinstance_id",
            "data",
        )

        for tile in tile_queryset.iterator(chunk_size=1000):
            file_items = (tile.data or {}).get(nodeid_text) or []
            if not isinstance(file_items, list):
                continue

            for file_item in file_items:
                if not isinstance(file_item, dict):
                    continue

                file_name = file_item.get("name")
                extension = None
                if file_name:
                    extension = Path(file_name).suffix.lstrip(".").lower() or None

                batch.append(
                    FileListSearch(
                        tileid_id=tile.tileid,
                        resourceinstanceid_id=tile.resourceinstance_id,
                        graph_slug=node.graph.slug,
                        node_alias=node.alias,
                        datatype=node.datatype,
                        value=file_name or None,
                        extension=extension,
                        file_size=file_item.get("size"),
                        modified_at=file_item.get("lastModified"),
                    )
                )

                if len(batch) >= batch_size:
                    FileListSearch.objects.bulk_create(batch, batch_size=batch_size)
                    batch.clear()

    if batch:
        FileListSearch.objects.bulk_create(batch, batch_size=batch_size)


def clear_file_list_rows(apps, schema_editor):
    FileListSearch = apps.get_model("arches_search", "FileListSearch")
    FileListSearch.objects.all().delete()


def _sync_file_list_facets(apps, facet_specs, target_model_name):
    AdvancedSearchFacet = apps.get_model("arches_search", "AdvancedSearchFacet")
    ContentType = apps.get_model("contenttypes", "ContentType")
    DDataType = apps.get_model("models", "DDataType")

    datatype = DDataType.objects.get(datatype="file-list")
    target_search_model, _created = ContentType.objects.get_or_create(
        app_label="arches_search",
        model=target_model_name,
    )

    AdvancedSearchFacet.objects.filter(datatype=datatype).delete()

    for sortorder, spec in enumerate(facet_specs):
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


def forwards_sync_file_list_facets(apps, schema_editor):
    _sync_file_list_facets(apps, FILE_LIST_FACET_SPECS, "filelistsearch")


def reverse_sync_file_list_facets(apps, schema_editor):
    _sync_file_list_facets(apps, LEGACY_FILE_LIST_FACET_SPECS, "termsearch")


class Migration(migrations.Migration):
    dependencies = [
        ("arches_search", "0015_normalise_orm_templates"),
    ]

    operations = [
        migrations.CreateModel(
            name="FileListSearch",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("graph_slug", models.TextField()),
                ("node_alias", models.TextField()),
                ("datatype", models.TextField()),
                ("value", models.TextField(blank=True, null=True)),
                ("extension", models.TextField(blank=True, null=True)),
                ("file_size", models.BigIntegerField(blank=True, null=True)),
                ("modified_at", models.FloatField(blank=True, null=True)),
                (
                    "resourceinstanceid",
                    models.ForeignKey(
                        db_column="resourceinstanceid",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="models.resourceinstance",
                    ),
                ),
                (
                    "tileid",
                    models.ForeignKey(
                        db_column="tileid",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="models.tile",
                    ),
                ),
            ],
            options={
                "db_table": "arches_search_file_list",
                "managed": True,
                "constraints": [],
                "indexes": [
                    models.Index(
                        fields=["resourceinstanceid"],
                        name="afls_resource_idx",
                    ),
                    models.Index(fields=["tileid"], name="afls_tile_idx"),
                    models.Index(fields=["datatype"], name="afls_datatype_idx"),
                    models.Index(fields=["node_alias"], name="afls_node_alias_idx"),
                    models.Index(fields=["extension"], name="afls_extension_idx"),
                    models.Index(fields=["file_size"], name="afls_file_size_idx"),
                    models.Index(
                        fields=["modified_at"],
                        name="afls_modified_at_idx",
                    ),
                    models.Index(
                        fields=[
                            "graph_slug",
                            "node_alias",
                            "resourceinstanceid",
                            "tileid",
                        ],
                        name="afls_scope_idx",
                    ),
                    models.Index(
                        fields=["graph_slug", "node_alias", "extension"],
                        name="afls_subject_ext_idx",
                    ),
                    models.Index(
                        fields=["graph_slug", "node_alias", "file_size"],
                        name="afls_subject_size_idx",
                    ),
                    models.Index(
                        fields=["graph_slug", "node_alias", "modified_at"],
                        name="afls_subject_mod_idx",
                    ),
                    django.contrib.postgres.indexes.GinIndex(
                        fields=["value"],
                        name="afls_value_trgm_idx",
                        opclasses=["gin_trgm_ops"],
                    ),
                    django.contrib.postgres.indexes.GinIndex(
                        fields=["graph_slug", "node_alias", "value"],
                        name="afls_subject_name_trgm",
                        opclasses=["text_ops", "text_ops", "gin_trgm_ops"],
                    ),
                ],
            },
        ),
        migrations.RunPython(populate_file_list_rows, clear_file_list_rows),
        migrations.RunPython(
            forwards_sync_file_list_facets,
            reverse_sync_file_list_facets,
        ),
    ]
