from django.db import models
from django.db.models import F, Func
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from arches.app.models.fields.i18n import I18n_TextField


class DDatatypeXAdvancedSearchModel(models.Model):
    id = models.AutoField(primary_key=True)
    datatype = models.OneToOneField(
        "models.DDataType",
        on_delete=models.CASCADE,
        db_column="datatypeid",
        verbose_name=_("Data Type"),
        help_text=_("The data type this mapping applies to."),
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        verbose_name=_("Search Model"),
        help_text=_("The concrete search-table model for this data type."),
    )

    class Meta:
        managed = True
        constraints = [
            models.UniqueConstraint(
                fields=["datatype"], name="unique_search_model_per_datatype"
            )
        ]
        indexes = [
            models.Index(fields=["datatype"]),
            models.Index(fields=["content_type"]),
        ]

    @property
    def model_class(self):
        return self.content_type.model_class()

    @property
    def db_table_name(self):
        model_class = self.model_class
        return model_class._meta.db_table if model_class else None


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["datatype", "operator"], name="unique_operator_per_datatype"
            ),
            models.UniqueConstraint(
                fields=["datatype", "sortorder"], name="unique_sortorder_per_datatype"
            ),
        ]


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
    search_vector = SearchVectorField(null=True)

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
            models.Index(fields=["value"]),
            models.Index(fields=["graph_slug", "node_alias", "value"]),
            models.Index(fields=["graph_slug", "node_alias", "language", "value"]),
            models.Index(
                fields=["graph_slug", "node_alias", "resourceinstanceid", "tileid"]
            ),
            models.Index(fields=["graph_slug", "node_alias", "tileid", "value"]),
            models.Index(
                fields=["graph_slug", "node_alias", "tileid", "language", "value"]
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
