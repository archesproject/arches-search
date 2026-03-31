import uuid

from django.contrib.gis.db.models import GeometryField
from django.db import models
from django.db.models import F
from django.contrib.postgres.indexes import GinIndex
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
    target_search_model = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        verbose_name=_("Target Search Model"),
        help_text=_("The concrete search-table model this facet should query against."),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["datatype", "operator"], name="unique_operator_per_datatype"
            ),
            models.UniqueConstraint(
                fields=["datatype", "sortorder"], name="unique_sortorder_per_datatype"
            ),
        ]

    @property
    def target_model_class(self):
        if self.target_search_model_id is None:
            return None
        return self.target_search_model.model_class()


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
        ]


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
    geom = GeometryField(srid=4326)

    class Meta:
        managed = True
        db_table = "arches_search_geometry"
        indexes = [
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["node_alias"]),
            models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"]
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
