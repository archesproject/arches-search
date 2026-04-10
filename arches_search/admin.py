from django.contrib import admin
from django.db import models
from django.forms import Textarea

from arches_search.models.models import (
    SavedSearch,
    NodeFilterConfig,
    SharedSearchXUser,
    SharedSearchXGroup,
)


class SharedSearchXUserInline(admin.TabularInline):
    model = SharedSearchXUser
    extra = 0


class SharedSearchXGroupInline(admin.TabularInline):
    model = SharedSearchXGroup
    extra = 0


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ["name", "creator", "created_at"]
    list_filter = ["creator", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["savedsearchid", "created_at"]
    inlines = [SharedSearchXUserInline, SharedSearchXGroupInline]


@admin.register(NodeFilterConfig)
class NodeFilterConfigAdmin(admin.ModelAdmin):
    list_display = ["graph", "slug"]
    list_filter = ["slug"]
    search_fields = ["graph__name"]
    formfield_overrides = {
        models.JSONField: {"widget": Textarea(attrs={"rows": 20, "cols": 80})},
    }


@admin.register(SharedSearchXUser)
class SharedSearchXUserAdmin(admin.ModelAdmin):
    list_display = ["saved_search", "user"]
    list_filter = ["user"]
    search_fields = ["saved_search__name", "user__username"]


@admin.register(SharedSearchXGroup)
class SharedSearchXGroupAdmin(admin.ModelAdmin):
    list_display = ["saved_search", "group"]
    list_filter = ["group"]
    search_fields = ["saved_search__name", "group__name"]
