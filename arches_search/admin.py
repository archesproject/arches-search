from django.contrib import admin

from arches_search.models.models import (
    SavedSearch,
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
