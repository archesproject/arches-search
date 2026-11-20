import uuid
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import (
    ETLModule,
    LoadEvent,
    Notification,
    SearchExportHistory,
    TempFile,
    UserXNotification,
)

from arches_search.utils.search_results_export import (
    attach_download_link,
    handle_task_postrun,
    record_pending_export,
)

# python manage.py test tests.test_search_results_export_download_link --settings="tests.test_settings"

ZIP_PATH = "archestemp/my_export.zip"


class AttachDownloadLinkTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="exporter", password="pw")
        cls.etl_module = ETLModule.objects.get(slug="branch-excel-exporter")

    def setUp(self):
        self.load_id = uuid.uuid4()
        self.export = record_pending_export(self.load_id, self.user, 3)

    def _finish_export(self, *, with_zip=True):
        """What a Bulk Data Manager exporter task leaves behind when it ends."""
        load_details = {}
        if with_zip:
            temp_file = TempFile.objects.create(path=ZIP_PATH, source="test")
            load_details = {
                "zipfile": {"name": "my_export.zip", "fileid": str(temp_file.pk)}
            }
        LoadEvent.objects.create(
            loadid=self.load_id,
            user=self.user,
            etl_module=self.etl_module,
            status="indexed" if with_zip else "failed",
            load_details=load_details,
        )
        return self._notify("Excel Export: Completed")

    def _notify(self, message):
        notification = Notification.objects.create(message=message, context=None)
        UserXNotification.objects.create(notif=notification, recipient=self.user)
        return notification

    def _download_context(self):
        return {"files": [{"fileid": str(self.load_id), "name": "my_export.zip"}]}

    def _task_args(self):
        # The shape of core's export_branch_excel task arguments.
        return (self.user.pk, str(self.load_id), "graph", "Graph", ["a"], "f")

    def test_attaches_the_zip_and_offers_it_in_the_completion_notification(self):
        notification = self._finish_export()

        attach_download_link(self._task_args(), {})

        self.export.refresh_from_db()
        notification.refresh_from_db()
        self.assertEqual(self.export.downloadfile.name, ZIP_PATH)
        self.assertEqual(notification.context, self._download_context())

    def test_notification_file_downloads_the_zip(self):
        notification = self._finish_export()
        attach_download_link(self._task_args(), {})
        notification.refresh_from_db()

        # Core's notification panel links each file to /files/<fileid>.
        file_id = notification.context["files"][0]["fileid"]
        self.client.force_login(self.user)
        response = self.client.get(reverse("file_access", args=[file_id]))

        self.assertRedirects(
            response, settings.MEDIA_URL + ZIP_PATH, fetch_redirect_response=False
        )

    def test_finds_the_load_id_among_keyword_arguments(self):
        notification = self._finish_export()

        attach_download_link((), {"load_id": self.load_id})

        notification.refresh_from_db()
        self.assertEqual(notification.context, self._download_context())

    def test_leaves_notifications_from_before_the_export_alone(self):
        earlier = self._notify("Something else")
        Notification.objects.filter(pk=earlier.pk).update(
            created=self.export.exporttime - timedelta(minutes=5)
        )
        notification = self._finish_export()

        attach_download_link(self._task_args(), {})

        earlier.refresh_from_db()
        notification.refresh_from_db()
        self.assertIsNone(earlier.context)
        self.assertEqual(notification.context, self._download_context())

    def test_sends_its_own_notification_when_the_exporter_sent_none(self):
        temp_file = TempFile.objects.create(path=ZIP_PATH, source="test")
        LoadEvent.objects.create(
            loadid=self.load_id,
            user=self.user,
            etl_module=self.etl_module,
            load_details={"zipfile": {"fileid": str(temp_file.pk)}},
        )

        attach_download_link(self._task_args(), {})

        notification = UserXNotification.objects.get(recipient=self.user).notif
        self.assertEqual(notification.context, self._download_context())

    def test_discards_the_record_when_the_export_produced_no_file(self):
        notification = self._finish_export(with_zip=False)

        attach_download_link(self._task_args(), {})

        self.assertFalse(SearchExportHistory.objects.filter(pk=self.load_id).exists())
        notification.refresh_from_db()
        self.assertIsNone(notification.context)

    def test_ignores_tasks_unrelated_to_a_search_export(self):
        notification = self._finish_export()

        attach_download_link((self.user.pk, str(uuid.uuid4())), {})

        self.export.refresh_from_db()
        notification.refresh_from_db()
        self.assertFalse(self.export.downloadfile)
        self.assertIsNone(notification.context)

    def test_task_postrun_handler_never_raises(self):
        with (
            patch(
                "arches_search.utils.search_results_export.attach_download_link",
                side_effect=RuntimeError("boom"),
            ),
            self.assertLogs("arches_search.utils.search_results_export", level="ERROR"),
        ):
            handle_task_postrun(args=self._task_args(), kwargs=None, task=None)
