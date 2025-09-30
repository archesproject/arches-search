from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField

from django.utils.translation import gettext_lazy as _


class DatatypeXAdvancedSearchFacets(models.Model):
    id = models.AutoField(primary_key=True)
    datatype = models.ForeignKey(
        "models.DDataType",
        on_delete=models.CASCADE,
        db_column="datatypeid",
        verbose_name=_("Data Type"),
        help_text=_("The data type to which the advanced search facets apply."),
    )
    controlled_list = models.ForeignKey(
        "arches_controlled_lists.List",
        on_delete=models.CASCADE,
        db_column="controlledlistid",
        verbose_name=_("Controlled List"),
        help_text=_(
            "The controlled list associated with the data type, if applicable."
        ),
        null=True,
        blank=True,
    )


class TermSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
    graph_alias = models.TextField()
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
            models.Index(fields=["graph_alias"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["value"]),
            GinIndex(fields=["search_vector"]),
        ]


class NumericSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
    graph_alias = models.TextField()
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
            models.Index(fields=["graph_alias"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["value"]),
        ]


class UUIDSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
    graph_alias = models.TextField()
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
            models.Index(fields=["graph_alias"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["value"]),
        ]


class DateSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
    graph_alias = models.TextField()
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
            models.Index(fields=["graph_alias"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["value"]),
        ]


class DateRangeSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
    graph_alias = models.TextField()
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
            models.Index(fields=["graph_alias"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["start_value", "end_value"]),
        ]


class BooleanSearch(models.Model):
    id = models.AutoField(primary_key=True)
    tileid = models.UUIDField()
    resourceinstanceid = models.UUIDField()
    graph_alias = models.TextField()
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
            models.Index(fields=["graph_alias"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["value"]),
        ]
