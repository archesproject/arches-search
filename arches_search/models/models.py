from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField


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
            models.Index(fields=["tileid", "node_alias", "start_date", "end_date"]),
            models.Index(fields=["tileid"]),
            models.Index(fields=["resourceinstanceid"]),
            models.Index(fields=["graph_alias"]),
            models.Index(fields=["node_alias"]),
            models.Index(fields=["datatype"]),
            models.Index(fields=["start_date", "end_date"]),
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
