"""
Saving a search's results as a static resource set (arches-resource-sets).

The set is a snapshot: its members are the resources the search matched, for
the user who ran it, at the moment it was saved. Nothing here re-runs the
search later.

Each set saved here is listed as a saved search whose query_definition is
{"resourceSetId": <id>}. Opening it searches with resource_set_id, so the
saved search table is the one list of what the user saved from search; sets
made elsewhere in arches-resource-sets are not in it.
"""

from itertools import batched
from typing import Tuple

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from arches.app.tasks import log_error, update_user_task_record
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.utils.task_management import check_if_celery_available
from arches.app.views.api import APIBase

from arches_resource_sets.models import ResourceSet, ResourceSetMember

from arches_search.models.models import SavedSearch, SharedSearchXGroup
from arches_search.tasks import create_resource_set_from_search
from arches_search.views.api.saved_search import (
    INVALID_SHARING_IDS_ERROR,
    is_valid_sharing_ids,
)
from arches_search.utils.search import (
    SearchCompiler,
    SearchPayload,
    validate_search_payload,
)


def _resource_set_limits() -> dict:
    """
    RESOURCE_SET_IMMEDIATE_THRESHOLD and RESOURCE_SET_MEMBER_LIMIT, defaulting
    to core's SEARCH_EXPORT_IMMEDIATE_DOWNLOAD_THRESHOLD and SEARCH_EXPORT_LIMIT.
    """
    return {
        "immediate_threshold": getattr(
            settings,
            "RESOURCE_SET_IMMEDIATE_THRESHOLD",
            settings.SEARCH_EXPORT_IMMEDIATE_DOWNLOAD_THRESHOLD,
        ),
        "member_limit": getattr(
            settings, "RESOURCE_SET_MEMBER_LIMIT", settings.SEARCH_EXPORT_LIMIT
        ),
    }


def create_resource_set_from_queryset(
    owner, queryset: QuerySet, name: str, description: str
) -> Tuple[ResourceSet, int]:
    """
    Creates a set holding every resource in queryset (a ResourceInstance
    queryset) and returns (resource_set, member_count). Call it inside a
    transaction, so nobody sees a set that is still filling.

    Members are read and created BULK_IMPORT_BATCH_SIZE at a time, so a large
    set is never held in memory at once.
    """
    batch_size = settings.BULK_IMPORT_BATCH_SIZE
    resource_ids = queryset.order_by().values_list("pk", flat=True)
    resource_set = ResourceSet.objects.create(
        owner=owner, name=name, description=description
    )
    member_count = 0
    for id_batch in batched(resource_ids.iterator(chunk_size=batch_size), batch_size):
        ResourceSetMember.objects.bulk_create(
            ResourceSetMember(
                resource_set=resource_set, resource_instance_id=resource_id
            )
            for resource_id in id_batch
        )
        member_count += len(id_batch)
    return resource_set, member_count


def save_search_as_resource_set(
    user,
    name,
    description,
    search_body,
    shared_group_ids=(),
    in_background=False,
) -> dict:
    """
    Runs the search as user and saves its results as a set, with the saved
    search that lists it, shared with shared_group_ids, or queues the
    create_resource_set_from_search task when there are too many to save now.
    The task calls this again with in_background=True, which always saves.

    Returns {"message"}, plus "resource_set_id" and "saved_search_id" once
    saved, or "task_id" when queued.
    Raises ValidationError for a bad search, or when the results can't be
    saved (none, over the limit, or too many to save without Celery).
    """
    limits = _resource_set_limits()

    search_payload = SearchPayload.from_body(search_body)
    validate_search_payload(search_payload)
    search_result = SearchCompiler(search_payload, user).compile()
    result_count = search_result.scoped_count

    # Checked again in the task: results can change before it runs.
    if result_count == 0:
        raise ValidationError(_("There are no results to save."))
    if result_count > limits["member_limit"]:
        raise ValidationError(
            _(
                "This search matches {count} resources, more than the limit of "
                "{limit}. Narrow the search and try again."
            ).format(count=result_count, limit=limits["member_limit"])
        )

    if result_count > limits["immediate_threshold"] and not in_background:
        if not check_if_celery_available():
            raise ValidationError(
                _(
                    "This search matches {count} resources, too many to save "
                    "right now. Narrow the search to {threshold} resources or "
                    "fewer, or try again later."
                ).format(count=result_count, threshold=limits["immediate_threshold"])
            )
        task = create_resource_set_from_search.apply_async(
            (user.pk, name, description, search_body, list(shared_group_ids)),
            link=update_user_task_record.s(),
            link_error=log_error.s(),
        )
        return {
            "task_id": task.task_id,
            "message": _(
                "Your resource set is being saved. You will be notified when it "
                "is ready."
            ),
        }

    # One transaction, so the saved search never lists a set still filling.
    with transaction.atomic():
        resource_set, member_count = create_resource_set_from_queryset(
            user, search_result.results, name, description
        )
        saved_search = SavedSearch.objects.create(
            name=name,
            description=description,
            # The set's id alone: re-applying the search's own filters would
            # drop members edited since, so it would no longer be a snapshot.
            query_definition={"resourceSetId": str(resource_set.pk)},
            creator=user,
        )
        # Groups deleted while a background save waited are left out.
        SharedSearchXGroup.objects.bulk_create(
            SharedSearchXGroup(saved_search=saved_search, group_id=group_id)
            for group_id in Group.objects.filter(
                pk__in=set(shared_group_ids)
            ).values_list("pk", flat=True)
        )
    return {
        "resource_set_id": str(resource_set.pk),
        "saved_search_id": str(saved_search.pk),
        "message": _(
            "Your resource set '{name}' is ready with {count} resources."
        ).format(name=name, count=member_count),
    }


class SearchResultsResourceSetAPI(APIBase):
    """
    Saves a search's results as a static resource set. GET returns the size
    limits the save is held to. The sets saved are listed, and deleted,
    through the saved searches API.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.username == "anonymous":
            return JSONResponse(
                {"error": _("User not authenticated. Access denied.")}, status=401
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return JSONResponse(_resource_set_limits())

    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        name = str(body.get("name") or "").strip()
        if not name:
            return JSONResponse({"error": _("A name is required.")}, status=400)
        description = str(body.get("description") or "").strip()
        shared_group_ids = body.get("groups", [])
        if not is_valid_sharing_ids([], shared_group_ids):
            return JSONResponse({"error": INVALID_SHARING_IDS_ERROR}, status=400)
        search_body = {
            key: value
            for key, value in body.items()
            if key not in ("name", "description", "groups")
        }

        try:
            saved = save_search_as_resource_set(
                request.user, name, description, search_body, shared_group_ids
            )
        except ValidationError as error:
            return JSONResponse({"error": " ".join(error.messages)}, status=400)
        return JSONResponse(saved, status=202 if "task_id" in saved else 201)
