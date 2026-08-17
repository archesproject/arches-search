import uuid

from django.contrib.gis.db.models import GeometryField
from django.db import models
from django.db.models import F
from django.contrib.postgres.indexes import GinIndex, GistIndex
from django.contrib.postgres.search import SearchVectorField
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language, get_language_info
from arches.app.models.fields.i18n import I18n_TextField
from django.contrib.postgres.search import SearchVector
from django.conf import settings


class AdvancedSearchFacet(models.Model):
    id = models.AutoField(primary_key=True)
    arity = models.PositiveSmallIntegerField(default=0)
    datatype = models.ForeignKey(
        "models.DDataType",
        on_delete=models.CASCADE,
        db_column="datatypeid",
        verbose_name=_("Data Type"),
        help_text=_("The data type to which the advanced search facet applies."),
    )
    label = I18n_TextField()
    operator = models.CharField(max_length=50)
    param_formats = models.JSONField(default=list, blank=True)
    sortorder = models.PositiveSmallIntegerField()
    orm_template = models.CharField(max_length=255, blank=True)
    is_orm_template_negated = models.BooleanField(default=False)
    filter_field = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("Filter field"),
        help_text=_(
            "Name of a field on the target search model used to further filter rows "
            "based on operand metadata (e.g. 'language' for locale-keyed string operands). "
            "Empty means no additional filtering."
        ),
    )
    target_search_model = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        verbose_name=_("Target Search Model"),
        help_text=_("The concrete search-table model this facet should query against."),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["datatype", "operator", "target_search_model"],
                name="unique_operator_per_datatype_and_model",
            ),
            models.UniqueConstraint(
                fields=["datatype", "sortorder", "target_search_model"],
                name="unique_sortorder_per_datatype_and_model",
            ),
        ]

    def serialize(self, fields=None, exclude=None, **kwargs):
        data = {
            "id": self.id,
            "arity": self.arity,
            "datatype_id": self.datatype_id,
            "label": self.label,
            "operator": self.operator,
            "param_formats": self.param_formats,
            "sortorder": self.sortorder,
            "orm_template": self.orm_template,
            "is_orm_template_negated": self.is_orm_template_negated,
            "filter_field": self.filter_field,
            "target_search_model_id": self.target_search_model_id,
        }

        if fields is not None:
            data = {key: value for key, value in data.items() if key in fields}

        if exclude is not None:
            data = {key: value for key, value in data.items() if key not in exclude}

        return data

    @property
    def target_model_class(self):
        if self.target_search_model_id is None:
            return None
        return self.target_search_model.model_class()

    def filter_rows(self, rows, resolved_language):
        if not self.filter_field or resolved_language is None:
            return rows
        return rows.filter(**{self.filter_field: resolved_language})


class TermSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.ForeignKey(
        "models.Tile", on_delete=models.CASCADE, db_column="tileid"
    )
    resourceinstanceid = models.ForeignKey(
        "models.ResourceInstance",
        on_delete=models.CASCADE,
        db_column="resourceinstanceid",
    )
    graph_slug = models.TextField()
    node_alias = models.TextField()
    language = models.TextField()
    datatype = models.TextField()
    value = models.TextField()
    search_vector = models.GeneratedField(
        null=True,
        db_persist=True,
        expression=SearchVector(
            "value",
            config=next(
                (lang[1] for lang in settings.LANGUAGES if lang[0] == F("language")),
                get_language_info(get_language())["name"].lower(),
            ),
        ),
        output_field=SearchVectorField(),
    )

    @staticmethod
    def _extract_language_entry_text(language_entry):
        if isinstance(language_entry, dict) and "value" in language_entry:
            return language_entry["value"]
        return language_entry

    @staticmethod
    def _is_reference_value(raw_value):
        return (
            isinstance(raw_value, list)
            and raw_value
            and all(
                isinstance(reference_item, dict) and "labels" in reference_item
                for reference_item in raw_value
            )
        )

    @staticmethod
    def _normalize_reference_value(raw_value):
        return list(
            dict.fromkeys(
                label.get("value")
                for reference_item in raw_value
                for label in reference_item.get("labels") or []
                if label.get("value") is not None
            )
        )

    @staticmethod
    def _is_url_value(raw_value):
        return set(raw_value.keys()) <= {"url", "url_label"}

    @staticmethod
    def _normalize_url_value(raw_value):
        return raw_value.get("url_label") or raw_value.get("url")

    @classmethod
    def _resolve_localized_string_language(
        cls, operand_item, raw_value, active_language_code, short_language_code
    ):
        # The widget includes every configured language as a key even when
        # blank, so prefer non-empty entries over a bare key-presence check.
        non_empty_language_codes = [
            language_code
            for language_code, language_entry in raw_value.items()
            if cls._extract_language_entry_text(language_entry)
        ]

        display_value = operand_item.get("display_value")
        if display_value:
            displayed_language_codes = [
                language_code
                for language_code in non_empty_language_codes
                if cls._extract_language_entry_text(raw_value[language_code])
                == display_value
            ]
            if displayed_language_codes:
                non_empty_language_codes = displayed_language_codes

        candidate_language_codes = non_empty_language_codes or list(raw_value.keys())

        if active_language_code and active_language_code in candidate_language_codes:
            return active_language_code
        if short_language_code and short_language_code in candidate_language_codes:
            return short_language_code
        return candidate_language_codes[0]

    @classmethod
    def normalize_operands(cls, operand_items):
        active_language_code = get_language()
        short_language_code = (
            active_language_code.split("-")[0] if active_language_code else None
        )

        normalized_items = []
        resolved_language = None
        for operand_item in operand_items:
            raw_value = operand_item.get("value")

            if cls._is_reference_value(raw_value):
                normalized_items.append(
                    {
                        **operand_item,
                        "value": cls._normalize_reference_value(raw_value),
                    }
                )
                continue

            if not isinstance(raw_value, dict) or not raw_value:
                normalized_items.append(operand_item)
                continue

            if cls._is_url_value(raw_value):
                normalized_items.append(
                    {**operand_item, "value": cls._normalize_url_value(raw_value)}
                )
                continue

            chosen_language = cls._resolve_localized_string_language(
                operand_item, raw_value, active_language_code, short_language_code
            )
            if resolved_language is None:
                resolved_language = chosen_language
            elif chosen_language != resolved_language:
                raise ValueError(
                    "Localized string operands resolved to different languages"
                )

            language_value = cls._extract_language_entry_text(
                raw_value[chosen_language]
            )
            normalized_items.append({**operand_item, "value": language_value})

        return normalized_items, resolved_language

    class Meta:
        managed = True
        db_table = "arches_search_terms"
        constraints = []
        indexes = [
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["language"]),
            models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"]
            ),
            GinIndex(
                name="gslug_na_val",
                fields=["graph_slug", "node_alias", "value"],
                opclasses=["text_ops", "text_ops", "gin_trgm_ops"],
            ),
            GinIndex(
                name="gslug_na_lang_val",
                fields=["graph_slug", "node_alias", "language", "value"],
                opclasses=["text_ops", "text_ops", "text_ops", "gin_trgm_ops"],
            ),
            GinIndex(
                name="gslug_na_tile_val",
                fields=["graph_slug", "node_alias", "tileid", "value"],
                opclasses=["text_ops", "text_ops", "uuid_ops", "gin_trgm_ops"],
            ),
            GinIndex(
                name="gslug_na_tile_lang_val",
                fields=["graph_slug", "node_alias", "tileid", "language", "value"],
                opclasses=[
                    "text_ops",
                    "text_ops",
                    "uuid_ops",
                    "text_ops",
                    "gin_trgm_ops",
                ],
            ),
            GinIndex(fields=["search_vector"]),
            GinIndex(
                name="term_value_trgm", fields=["value"], opclasses=["gin_trgm_ops"]
            ),
        ]


class NumericSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.ForeignKey(
        "models.Tile", on_delete=models.CASCADE, db_column="tileid"
    )
    resourceinstanceid = models.ForeignKey(
        "models.ResourceInstance",
        on_delete=models.CASCADE,
        db_column="resourceinstanceid",
    )
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    value = models.DecimalField(decimal_places=10, max_digits=64)

    class Meta:
        managed = True
        db_table = "arches_search_numeric"
        constraints = []
        indexes = [
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["value"]),
            models.Index(fields=["graph_slug", "node_alias", "value"]),
            models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"]
            ),
            models.Index(fields=["graph_slug", "node_alias", "tileid", "value"]),
        ]


class UUIDSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.ForeignKey(
        "models.Tile", on_delete=models.CASCADE, db_column="tileid"
    )
    resourceinstanceid = models.ForeignKey(
        "models.ResourceInstance",
        on_delete=models.CASCADE,
        db_column="resourceinstanceid",
    )
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    value = models.UUIDField()

    class Meta:
        managed = True
        db_table = "arches_search_uuid"
        constraints = []
        indexes = [
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["value"]),
            models.Index(fields=["graph_slug", "node_alias", "value"]),
            models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"]
            ),
            models.Index(fields=["graph_slug", "node_alias", "tileid", "value"]),
        ]

    @classmethod
    def normalize_operands(cls, operand_items):
        def extract_resource_id(resource_reference):
            if isinstance(resource_reference, dict):
                return resource_reference.get("resourceId")
            return resource_reference

        normalized_items = []
        for operand_item in operand_items:
            raw_value = operand_item.get("value")
            if isinstance(raw_value, list):
                normalized_value = [
                    extract_resource_id(resource_reference)
                    for resource_reference in raw_value
                ]
            elif isinstance(raw_value, dict):
                normalized_value = extract_resource_id(raw_value)
            else:
                normalized_items.append(operand_item)
                continue
            normalized_items.append({**operand_item, "value": normalized_value})
        return normalized_items, None


class DateSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.ForeignKey(
        "models.Tile", on_delete=models.CASCADE, db_column="tileid"
    )
    resourceinstanceid = models.ForeignKey(
        "models.ResourceInstance",
        on_delete=models.CASCADE,
        db_column="resourceinstanceid",
    )
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    value = models.BigIntegerField()

    class Meta:
        managed = True
        db_table = "arches_search_date"
        constraints = []
        indexes = [
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["value"]),
            models.Index(fields=["graph_slug", "node_alias", "value"]),
            models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"]
            ),
            models.Index(fields=["graph_slug", "node_alias", "tileid", "value"]),
        ]

    @classmethod
    def normalize_operands(cls, operand_items):
        from arches.app.utils.date_utils import ExtendedDateFormat

        edtf = ExtendedDateFormat()
        normalized_items = []
        for operand_item in operand_items:
            raw_value = operand_item.get("value")
            if isinstance(raw_value, str) and raw_value.count("-") == 2:
                year_str, month_str, day_str = raw_value.split("-")
                sortable_value = edtf.to_sortable_date(
                    int(year_str), int(month_str), int(day_str)
                )
                normalized_items.append({**operand_item, "value": sortable_value})
            else:
                normalized_items.append(operand_item)
        return normalized_items, None


class DateRangeSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.ForeignKey(
        "models.Tile", on_delete=models.CASCADE, db_column="tileid"
    )
    resourceinstanceid = models.ForeignKey(
        "models.ResourceInstance",
        on_delete=models.CASCADE,
        db_column="resourceinstanceid",
    )
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    start_value = models.BigIntegerField()
    end_value = models.BigIntegerField()

    class Meta:
        managed = True
        db_table = "arches_search_date_range"
        constraints = []
        indexes = [
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["node_alias"]),
            models.Index(
                fields=["graph_slug", "node_alias", "start_value", "end_value"]
            ),
            models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"]
            ),
            models.Index(
                fields=[
                    "graph_slug",
                    "node_alias",
                    "tileid",
                    "start_value",
                    "end_value",
                ]
            ),
            models.Index(fields=["graph_slug", "node_alias", "end_value"]),
        ]

    normalize_operands = DateSearch.normalize_operands


class BooleanSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.ForeignKey(
        "models.Tile", on_delete=models.CASCADE, db_column="tileid"
    )
    resourceinstanceid = models.ForeignKey(
        "models.ResourceInstance",
        on_delete=models.CASCADE,
        db_column="resourceinstanceid",
    )
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    value = models.BooleanField()

    class Meta:
        managed = True
        db_table = "arches_search_boolean"
        constraints = []
        indexes = [
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["value"]),
            models.Index(fields=["graph_slug", "node_alias", "value"]),
            models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"]
            ),
            models.Index(fields=["graph_slug", "node_alias", "tileid", "value"]),
        ]


class GeometrySearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.ForeignKey(
        "models.Tile", on_delete=models.CASCADE, db_column="tileid"
    )
    resourceinstanceid = models.ForeignKey(
        "models.ResourceInstance",
        on_delete=models.CASCADE,
        db_column="resourceinstanceid",
    )
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    geom = GeometryField(srid=4326, spatial_index=False)

    class Meta:
        managed = True
        db_table = "arches_search_geometry"
        indexes = [
            models.Index(
                fields=["resourceinstanceid"],
                name="arches_sear_resourc_geo_idx",
            ),
            models.Index(fields=["tileid"], name="arches_sear_tileid_geo_idx"),
            models.Index(fields=["node_alias"], name="arches_sear_nodeal_geo_idx"),
            models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"],
                name="arches_sear_subject_geo_idx",
            ),
            GistIndex(fields=["geom"], name="arches_sear_geom_gist_idx"),
        ]


class FileListSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.ForeignKey(
        "models.Tile", on_delete=models.CASCADE, db_column="tileid"
    )
    resourceinstanceid = models.ForeignKey(
        "models.ResourceInstance",
        on_delete=models.CASCADE,
        db_column="resourceinstanceid",
    )
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    value = models.TextField(null=True, blank=True)
    extension = models.TextField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    modified_at = models.FloatField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = "arches_search_file_list"
        constraints = []
        indexes = [
            models.Index(fields=["resourceinstanceid"], name="afls_resource_idx"),
            models.Index(fields=["tileid"], name="afls_tile_idx"),
            models.Index(fields=["datatype"], name="afls_datatype_idx"),
            models.Index(fields=["node_alias"], name="afls_node_alias_idx"),
            models.Index(fields=["extension"], name="afls_extension_idx"),
            models.Index(fields=["file_size"], name="afls_file_size_idx"),
            models.Index(fields=["modified_at"], name="afls_modified_at_idx"),
            models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"],
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
            GinIndex(
                fields=["value"],
                name="afls_value_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                fields=["graph_slug", "node_alias", "value"],
                name="afls_subject_name_trgm",
                opclasses=["text_ops", "text_ops", "gin_trgm_ops"],
            ),
        ]


class SavedSearch(models.Model):
    savedsearchid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    query_definition = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_searches",
    )

    class Meta:
        managed = True
        db_table = "arches_search_saved_searches"


class SharedSearchXUser(models.Model):
    id = models.AutoField(primary_key=True)
    saved_search = models.ForeignKey(
        SavedSearch,
        on_delete=models.CASCADE,
        related_name="shared_users",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        managed = True
        db_table = "arches_search_shared_searches_x_users"
        constraints = [
            models.UniqueConstraint(
                fields=["saved_search", "user"],
                name="unique_shared_search_user",
            )
        ]


class NodeFilterConfig(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.JSONField(default=dict)
    slug = models.TextField(default="filtering")
    graph = models.ForeignKey(
        "models.GraphModel",
        on_delete=models.CASCADE,
        related_name="node_filter_configs",
    )

    class Meta:
        managed = True
        db_table = "arches_search_node_filter_config"
        constraints = [
            models.UniqueConstraint(
                fields=["graph", "slug"],
                name="unique_node_filter_config_slug_per_graph",
            )
        ]

    def __str__(self):
        graph_name = getattr(self.graph, "name", "Unknown")
        return f"NodeFilterConfig ({self.slug}) for {graph_name}"


class SharedSearchXGroup(models.Model):
    id = models.AutoField(primary_key=True)
    saved_search = models.ForeignKey(
        SavedSearch,
        on_delete=models.CASCADE,
        related_name="shared_groups",
    )
    group = models.ForeignKey(
        "auth.Group",
        on_delete=models.CASCADE,
    )

    class Meta:
        managed = True
        db_table = "arches_search_shared_searches_x_groups"
        constraints = [
            models.UniqueConstraint(
                fields=["saved_search", "group"],
                name="unique_shared_search_group",
            )
        ]
