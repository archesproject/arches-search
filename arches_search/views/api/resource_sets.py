"""
Saving a search's results as a static resource set (arches-resource-sets).

The set is a snapshot: its members are the resources the search matched, for
the user who ran it, at the moment it was saved. Nothing here re-runs the
search later.
"""

import uuid
from itertools import batched
from typing import Optional, Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, QuerySet
from django.http import HttpResponse
from django.utils.translation import gettext as _

from arches.app.tasks import log_error, update_user_task_record
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.utils.task_management import check_if_celery_available
from arches.app.views.api import APIBase

from arches_resource_sets.models import ResourceSet, ResourceSetMember

from arches_search.tasks import create_resource_set_from_search
from arches_search.utils.search import (
    SearchCompiler,
    SearchPayload,
    validate_search_payload,
)


def create_resource_set_from_queryset(
    owner,
    queryset: QuerySet,
    name: str = "",
    description: str = "",
    set_id: Optional[uuid.UUID] = None,
) -> Tuple[ResourceSet, int]:
    """
    Creates a set holding every resource in queryset (a ResourceInstance
    queryset) and returns (resource_set, member_count).

    The set and its members are created in one transaction, so nobody sees a
    set that is still filling, and a failure leaves nothing behind. Members
    are read and created BULK_IMPORT_BATCH_SIZE at a time, so a large set is
    never held in memory at once.
    """
    batch_size = settings.BULK_IMPORT_BATCH_SIZE
    resource_ids = queryset.order_by().values_list("pk", flat=True).distinct()
    member_count = 0

    with transaction.atomic(using=queryset.db):
        resource_set = ResourceSet.objects.using(queryset.db).create(
            id=set_id or uuid.uuid4(),
            owner=owner,
            name=name,
            description=description,
        )
        for id_batch in batched(
            resource_ids.iterator(chunk_size=batch_size), batch_size
        ):
            ResourceSetMember.objects.using(queryset.db).bulk_create(
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
    resource_set_id=None,
    in_background=False,
) -> dict:
    """
    Runs the search as user and saves its results as a set, or queues the
    create_resource_set_from_search task when there are too many to save now.
    The task calls this again with in_background=True, which always saves.

    Returns {"resource_set_id", "message"}, plus "task_id" when queued.
    Raises ValidationError for a bad search, or when the results can't be
    saved (none, over the limit, or too many to save without Celery).
    """
    immediate_threshold = getattr(
        settings,
        "RESOURCE_SET_IMMEDIATE_THRESHOLD",
        settings.SEARCH_EXPORT_IMMEDIATE_DOWNLOAD_THRESHOLD,
    )
    member_limit = getattr(
        settings, "RESOURCE_SET_MEMBER_LIMIT", settings.SEARCH_EXPORT_LIMIT
    )

    search_payload = SearchPayload.from_body(search_body)
    validate_search_payload(search_payload)
    search_result = SearchCompiler(search_payload, user).compile()
    result_count = search_result.scoped_count

    # Checked again in the task: results can change before it runs.
    if result_count == 0:
        raise ValidationError(_("There are no results to save."))
    if result_count > member_limit:
        raise ValidationError(
            _(
                "This search matches {count} resources, more than the limit of "
                "{limit}. Narrow the search and try again."
            ).format(count=result_count, limit=member_limit)
        )

    if result_count > immediate_threshold and not in_background:
        if not check_if_celery_available():
            raise ValidationError(
                _(
                    "This search matches {count} resources, too many to save "
                    "right now. Narrow the search to {threshold} resources or "
                    "fewer, or try again later."
                ).format(count=result_count, threshold=immediate_threshold)
            )
        resource_set_id = str(uuid.uuid4())
        task = create_resource_set_from_search.apply_async(
            (user.pk, resource_set_id, name, description, search_body),
            link=update_user_task_record.s(),
            link_error=log_error.s(),
        )
        return {
            "resource_set_id": resource_set_id,
            "task_id": task.task_id,
            "message": _(
                "Your resource set is being saved. You will be notified when it "
                "is ready."
            ),
        }

    resource_set, member_count = create_resource_set_from_queryset(
        user,
        search_result.results,
        name=name,
        description=description,
        set_id=resource_set_id,
    )
    return {
        "resource_set_id": str(resource_set.pk),
        "message": _(
            "Your resource set '{name}' is ready with {count} resources."
        ).format(name=name, count=member_count),
    }


class SearchResultsResourceSetAPI(APIBase):
    """
    Saves a search's results as a static resource set.
    RESOURCE_SET_IMMEDIATE_THRESHOLD and RESOURCE_SET_MEMBER_LIMIT default to
    core's SEARCH_EXPORT_IMMEDIATE_DOWNLOAD_THRESHOLD and SEARCH_EXPORT_LIMIT.
    """

    def get(self, request):
        if not request.user.is_authenticated or request.user.username == "anonymous":
            return JSONResponse(
                {"error": _("User not authenticated. Access denied.")}, status=401
            )

        owned_resource_sets = (
            ResourceSet.objects.filter(owner=request.user)
            .values("id", "name", "description", "date_created")
            .annotate(member_count=Count("resourcesetmember"))
            .order_by("-date_created")
        )
        return JSONResponse(
            {
                "resource_sets": owned_resource_sets,
                "immediate_threshold": getattr(
                    settings,
                    "RESOURCE_SET_IMMEDIATE_THRESHOLD",
                    settings.SEARCH_EXPORT_IMMEDIATE_DOWNLOAD_THRESHOLD,
                ),
                "member_limit": getattr(
                    settings, "RESOURCE_SET_MEMBER_LIMIT", settings.SEARCH_EXPORT_LIMIT
                ),
            }
        )

    def post(self, request):
        if not request.user.is_authenticated or request.user.username == "anonymous":
            return JSONResponse(
                {"error": _("User not authenticated. Access denied.")}, status=401
            )

        body = JSONDeserializer().deserialize(request.body)
        name = str(body.get("name") or "").strip()
        if not name:
            return JSONResponse({"error": _("A name is required.")}, status=400)
        description = str(body.get("description") or "").strip()
        search_body = {
            key: value
            for key, value in body.items()
            if key not in ("name", "description")
        }

        try:
            saved = save_search_as_resource_set(
                request.user, name, description, search_body
            )
        except ValidationError as error:
            return JSONResponse({"error": " ".join(error.messages)}, status=400)
        return JSONResponse(saved, status=202 if "task_id" in saved else 201)

    def delete(self, request, resource_set_id):
        # Only the owner's own sets; others' (and anonymous) get a 404.
        deleted_count = ResourceSet.objects.filter(
            pk=resource_set_id, owner=request.user
        ).delete()[0]
        if not deleted_count:
            return JSONResponse({"error": _("Resource set not found.")}, status=404)
        return HttpResponse(status=204)
