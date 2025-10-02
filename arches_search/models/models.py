from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.utils.translation import gettext_lazy as _

from arches.app.models.fields.i18n import I18n_TextField


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
    sql_template = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["datatype", "operator"],
                name="unique_operator_per_datatype",
            ),
            models.UniqueConstraint(
                fields=["datatype", "sortorder"],
                name="unique_sortorder_per_datatype",
            ),
        ]


class TermSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
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
            models.Index(fields=["tileid", "node_alias", "value"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["graph_slug"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["value"]),
            GinIndex(fields=["search_vector"]),
        ]


class NumericSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    value = models.DecimalField(decimal_places=10, max_digits=64)

    class Meta:
        managed = True
        db_table = "arches_search_numeric"
        constraints = []
        indexes = [
            models.Index(fields=["tileid", "node_alias", "value"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["graph_slug"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["value"]),
        ]


class UUIDSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    value = models.UUIDField()

    class Meta:
        managed = True
        db_table = "arches_search_uuid"
        constraints = []
        indexes = [
            models.Index(fields=["tileid", "node_alias", "value"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["graph_slug"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["value"]),
        ]


class DateSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    value = models.BigIntegerField()

    class Meta:
        managed = True
        db_table = "arches_search_date"
        constraints = []
        indexes = [
            models.Index(fields=["tileid", "node_alias", "value"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["graph_slug"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["value"]),
        ]


class DateRangeSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
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
            models.Index(fields=["tileid", "node_alias", "start_value", "end_value"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["graph_slug"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["start_value", "end_value"]),
        ]


class BooleanSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
    graph_slug = models.TextField()
    node_alias = models.TextField()
    datatype = models.TextField()
    value = models.BooleanField()

    class Meta:
        managed = True
        db_table = "arches_search_boolean"
        constraints = []
        indexes = [
            models.Index(fields=["tileid", "node_alias", "value"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["graph_slug"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["value"]),
        ]
