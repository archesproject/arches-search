import logging
import os
import uuid

from django.db.models import Q
from django.utils.translation import gettext as _

from arches.app.models import models

EXPORT_ETL_TYPE = "export"

logger = logging.getLogger(__name__)


def record_pending_export(load_id, user, resource_count):
    return models.SearchExportHistory.objects.create(
        searchexportid=load_id,
        user=user,
        numberofinstances=resource_count,
        url="",
    )


def attach_download_link(task_args, task_kwargs):
    """
    Completes any pending search export whose loadid was an argument of the
    task that just finished. Exporter tasks differ in signature, but each is
    handed the loadid. Only load events run by an export ETL module count, so
    other tasks that happen to take the same UUID are ignored.
    """
    candidate_ids = _uuid_arguments(task_args, task_kwargs)
    if not candidate_ids:
        return

    export_load_ids = models.LoadEvent.objects.filter(
        loadid__in=candidate_ids, etl_module__etl_type=EXPORT_ETL_TYPE
    ).values("loadid")
    pending_exports = models.SearchExportHistory.objects.filter(
        Q(downloadfile="") | Q(downloadfile__isnull=True),
        pk__in=export_load_ids,
    ).select_related("user")
    for export in pending_exports:
        _complete_export(export)


def handle_task_postrun(sender=None, args=None, kwargs=None, **extra):
    try:
        attach_download_link(args, kwargs)
    except Exception:
        # Never let this fail the task; the export itself has already finished.
        logger.exception("Could not attach a download link to a search export.")


def _uuid_arguments(task_args, task_kwargs):
    candidate_ids = set()
    for value in [*(task_args or ()), *(task_kwargs or {}).values()]:
        if not isinstance(value, (str, uuid.UUID)):
            continue
        try:
            candidate_ids.add(uuid.UUID(str(value)))
        except ValueError:
            continue
    return candidate_ids


def _complete_export(export):
    load_event = models.LoadEvent.objects.filter(loadid=export.pk).first()
    load_details = (load_event.load_details if load_event else None) or {}
    zip_file_id = (load_details.get("zipfile") or {}).get("fileid")
    temp_file = (
        models.TempFile.objects.filter(pk=zip_file_id).first() if zip_file_id else None
    )
    if temp_file is None:
        # The export failed, or the exporter saved no zip file to offer.
        export.delete()
        return

    export.downloadfile.name = temp_file.path.name
    export.save()

    files_context = {
        "files": [
            {
                "fileid": str(export.pk),
                "name": os.path.basename(temp_file.path.name),
            }
        ]
    }
    notification = _find_completion_notification(export.user, export.pk)
    if notification is None:
        notification = models.Notification.objects.create(
            message=_("Your search export is ready to download."),
            context=files_context,
        )
        models.UserXNotification.objects.create(
            notif=notification, recipient=export.user
        )
        return

    notification.context = {**(notification.context or {}), **files_context}
    notification.save()


def _find_completion_notification(user, load_id):
    """
    The exporter task tags the notification it sends when it finishes with the
    export's load id, so it can be told apart from the user's other
    notifications, including those of other exports.
    """
    user_notification = (
        models.UserXNotification.objects.filter(
            recipient=user, notif__context__loadid=str(load_id)
        )
        .select_related("notif")
        .order_by("-notif__created")
        .first()
    )
    return user_notification.notif if user_notification else None
