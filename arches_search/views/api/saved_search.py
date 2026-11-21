import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_resource_sets.models import ResourceSet

from arches_search.models.models import (
    SavedSearch,
    SharedSearchXUser,
    SharedSearchXGroup,
)


def _is_list_of_ids(value):
    return isinstance(value, list) and all(
        isinstance(item, int) and not isinstance(item, bool) for item in value
    )


def _resource_set_id(query_definition):
    """
    The id of the resource set a saved search is narrowed to, or None. A
    malformed id is None too: there is no set it could delete.
    """
    if not isinstance(query_definition, dict):
        return None
    resource_set_id = query_definition.get("resourceSetId")
    if not isinstance(resource_set_id, str):
        return None
    try:
        return str(uuid.UUID(resource_set_id))
    except ValueError:
        return None


INVALID_SHARING_IDS_ERROR = "users and groups must be lists of existing ids"

# Needed to list groups and share searches with them; an admin grants it.
VIEW_GROUP_PERMISSION = "auth.view_group"


def is_valid_sharing_ids(user_ids, group_ids):
    """Whether the ids are lists of existing user and group ids."""
    if not _is_list_of_ids(user_ids) or not _is_list_of_ids(group_ids):
        return False

    # FK constraints are deferred, so an invalid id wouldn't raise until
    # commit; check existence up front instead.
    requested_user_ids = set(user_ids)
    requested_group_ids = set(group_ids)
    existing_user_ids = set(
        get_user_model()
        .objects.filter(pk__in=requested_user_ids)
        .values_list("pk", flat=True)
    )
    existing_group_ids = set(
        Group.objects.filter(pk__in=requested_group_ids).values_list("pk", flat=True)
    )
    return (
        existing_user_ids == requested_user_ids
        and existing_group_ids == requested_group_ids
    )


def _serialize_shared_groups(saved_search):
    return sorted(
        (
            {"id": shared.group_id, "name": shared.group.name}
            for shared in saved_search.shared_groups.all()
        ),
        key=lambda group: group["name"],
    )


def _serialize_saved_search(
    saved_search, include_created_at=True, include_shared_groups=False
):
    data = {
        "savedsearchid": str(saved_search.savedsearchid),
        "name": saved_search.name,
        "description": saved_search.description,
        "query_definition": saved_search.query_definition,
        "creator": {
            "id": saved_search.creator_id,
            "username": saved_search.creator.username,
        },
    }
    if include_created_at:
        data["created_at"] = saved_search.created_at.isoformat()
    # Only the creator sees whom a search is shared with.
    if include_shared_groups:
        data["shared_groups"] = _serialize_shared_groups(saved_search)
    return data


class SavedSearchAPI(APIBase):
    def get(self, request):
        scope = request.GET.get("scope", "mine")
        search = request.GET.get("search", "")

        if scope == "mine":
            saved_searches = SavedSearch.objects.filter(creator=request.user)

        else:  # if not mine, get all shared searches
            user_shared = SavedSearch.objects.filter(shared_users__user=request.user)
            group_shared = SavedSearch.objects.filter(
                shared_groups__group__in=request.user.groups.all()
            )
            saved_searches = (
                (user_shared | group_shared).exclude(creator=request.user).distinct()
            )

        if search:
            saved_searches = saved_searches.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        saved_searches = saved_searches.select_related("creator").order_by("name")
        is_mine = scope == "mine"
        if is_mine:
            saved_searches = saved_searches.prefetch_related("shared_groups__group")

        return JSONResponse(
            [
                _serialize_saved_search(s, include_shared_groups=is_mine)
                for s in saved_searches
            ]
        )

    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        name = body.get("name", "").strip()
        if not name:
            return JSONResponse({"error": "name is required"}, status=400)

        query_definition = body.get("query_definition")
        if query_definition is None:
            return JSONResponse({"error": "query_definition is required"}, status=400)

        shared_user_ids = body.get("users", [])
        shared_group_ids = body.get("groups", [])
        if not is_valid_sharing_ids(shared_user_ids, shared_group_ids):
            return JSONResponse({"error": INVALID_SHARING_IDS_ERROR}, status=400)
        if shared_group_ids and not request.user.has_perm(VIEW_GROUP_PERMISSION):
            return JSONResponse(status=403)

        saved_search = SavedSearch.objects.create(
            name=name,
            description=body.get("description", ""),
            query_definition=query_definition,
            creator=request.user,
        )

        SharedSearchXUser.objects.bulk_create(
            [
                SharedSearchXUser(saved_search=saved_search, user_id=uid)
                for uid in set(shared_user_ids)
            ]
        )
        SharedSearchXGroup.objects.bulk_create(
            [
                SharedSearchXGroup(saved_search=saved_search, group_id=gid)
                for gid in set(shared_group_ids)
            ]
        )

        return JSONResponse(
            _serialize_saved_search(
                saved_search, include_created_at=False, include_shared_groups=True
            ),
            status=201,
        )

    def patch(self, request, savedsearchid):
        """Replaces the groups a search is shared with."""
        try:
            saved_search = SavedSearch.objects.get(
                savedsearchid=savedsearchid,
                creator=request.user,
            )
        except SavedSearch.DoesNotExist:
            return JSONResponse(status=404)

        body = JSONDeserializer().deserialize(request.body)
        if "groups" not in body:
            return JSONResponse({"error": "groups is required"}, status=400)
        shared_group_ids = body["groups"]
        if not is_valid_sharing_ids([], shared_group_ids):
            return JSONResponse({"error": INVALID_SHARING_IDS_ERROR}, status=400)
        if shared_group_ids and not request.user.has_perm(VIEW_GROUP_PERMISSION):
            return JSONResponse(status=403)

        with transaction.atomic():
            SharedSearchXGroup.objects.filter(saved_search=saved_search).delete()
            SharedSearchXGroup.objects.bulk_create(
                SharedSearchXGroup(saved_search=saved_search, group_id=gid)
                for gid in set(shared_group_ids)
            )

        return JSONResponse(
            _serialize_saved_search(saved_search, include_shared_groups=True)
        )

    def delete(self, request, savedsearchid):
        try:
            saved_search = SavedSearch.objects.get(
                savedsearchid=savedsearchid,
                creator=request.user,
            )
        except SavedSearch.DoesNotExist:
            return JSONResponse(status=404)

        resource_set_id = _resource_set_id(saved_search.query_definition)
        with transaction.atomic():
            saved_search.delete()
            if (
                resource_set_id is not None
                and not SavedSearch.objects.filter(
                    query_definition__resourceSetId=resource_set_id
                ).exists()
            ):
                ResourceSet.objects.filter(
                    pk=resource_set_id, owner=request.user
                ).delete()
        return JSONResponse(status=204)


class SavedSearchGroupsAPI(APIBase):
    """Lists the groups a saved search can be shared with."""

    def get(self, request):
        if not request.user.is_authenticated or request.user.username == "anonymous":
            return JSONResponse(status=401)
        if not request.user.has_perm(VIEW_GROUP_PERMISSION):
            return JSONResponse(status=403)
        groups = Group.objects.order_by("name").values("id", "name")
        return JSONResponse(list(groups))
