import json
import uuid
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm

from arches.app.models.models import (
    ETLModule,
    GraphModel,
    ResourceInstanceLifecycle,
    SearchExportHistory,
)

# python manage.py test tests.test_search_results_export_api --settings="tests.test_settings"

VIEW_MODULE = "arches_search.views.api.search_results_export"


class FakeExporter:
    """Records the request it is handed instead of queueing an export."""

    received_post = None

    def __init__(self, request=None, loadid=None):
        pass

    def export(self, request):
        FakeExporter.received_post = request.POST
        return {"success": True, "data": {}}


class UnavailableExporter(FakeExporter):
    """Answers as an exporter does when Celery is not running."""

    def export(self, request):
        return {"success": False, "data": {"message": "Celery is not running"}}


class BrokenExporter(FakeExporter):
    """Raises as an exporter with a different request contract might."""

    def export(self, request):
        raise KeyError("graphid")


class SearchResultsExportAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="export_admin", password="password123"
        )
        cls.member = User.objects.create_user(username="member", password="pw")
        cls.outsider = User.objects.create_user(username="outsider", password="pw")
        cls.exporters_group = Group.objects.create(name="test_exporters")
        cls.member.groups.add(cls.exporters_group)

        cls.granted_module = cls._create_export_module("search-test-granted")
        cls.ungranted_module = cls._create_export_module("search-test-ungranted")
        cls.hidden_module = cls._create_export_module(
            "search-test-hidden", config={"show": False}
        )
        cls.import_module = cls._create_export_module(
            "search-test-importer", etl_type="import"
        )
        for module in (cls.granted_module, cls.hidden_module, cls.import_module):
            assign_perm("view_etlmodule", cls.exporters_group, module)

        lifecycle = ResourceInstanceLifecycle.objects.create(name="Test lifecycle")
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="Export Graph",
            slug="export-test",
            isresource=True,
            resource_instance_lifecycle=lifecycle,
        )

    @staticmethod
    def _create_export_module(slug, *, etl_type="export", config=None):
        return ETLModule.objects.create(
            name=slug,
            slug=slug,
            description=f"{slug} description",
            icon="fa fa-download",
            etl_type=etl_type,
            component="",
            componentname=slug,
            config=config if config is not None else {},
        )

    def _available_slugs(self):
        response = self.client.get(reverse("search_results_export"))
        self.assertEqual(response.status_code, 200)
        return {exporter["slug"] for exporter in response.json()}

    def _post_export(self, export_format):
        return self.client.post(
            reverse("search_results_export"),
            json.dumps(
                {
                    "format": export_format,
                    "graph_slugs": [self.graph.slug],
                    "filename": "my_export",
                }
            ),
            content_type="application/json",
        )

    # --- GET: available formats ---

    def test_get_lists_nothing_for_an_anonymous_visitor(self):
        # Arches signs anonymous visitors in as its "anonymous" user, so they
        # see only the exporters an admin has granted that user.
        self.assertEqual(self._available_slugs(), set())

    def test_get_lists_only_exporters_the_user_was_granted(self):
        self.client.force_login(self.member)
        slugs = self._available_slugs()

        self.assertIn(self.granted_module.slug, slugs)
        self.assertNotIn(self.ungranted_module.slug, slugs)

    def test_get_omits_hidden_modules_and_non_exporters(self):
        self.client.force_login(self.member)
        slugs = self._available_slugs()

        self.assertNotIn(self.hidden_module.slug, slugs)
        self.assertNotIn(self.import_module.slug, slugs)

    def test_get_lists_nothing_for_a_user_without_grants(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self._available_slugs(), set())

    def test_get_lists_every_visible_exporter_for_a_superuser(self):
        self.client.force_login(self.superuser)
        slugs = self._available_slugs()

        self.assertTrue(
            {
                self.granted_module.slug,
                self.ungranted_module.slug,
                "branch-excel-exporter",
                "tile-excel-exporter",
            }.issubset(slugs)
        )
        self.assertNotIn(self.hidden_module.slug, slugs)

    # --- POST: starting an export ---

    def test_post_rejects_an_exporter_the_user_was_not_granted(self):
        self.client.force_login(self.member)
        response = self._post_export(self.ungranted_module.slug)
        self.assertEqual(response.status_code, 400)

    def test_post_rejects_a_hidden_exporter(self):
        self.client.force_login(self.member)
        response = self._post_export(self.hidden_module.slug)
        self.assertEqual(response.status_code, 400)

    def _post_export_of(self, resource_ids, exporter_class=FakeExporter):
        compiled = MagicMock()
        compiled.results.filter.return_value.values_list.return_value = resource_ids
        search_compiler = MagicMock()
        search_compiler.return_value.compile.return_value = compiled

        self.client.force_login(self.member)
        with (
            patch(f"{VIEW_MODULE}.SearchCompiler", search_compiler),
            patch(f"{VIEW_MODULE}.validate_search_payload"),
            patch.object(ETLModule, "get_class_module", return_value=exporter_class),
        ):
            return self._post_export(self.granted_module.slug)

    def test_post_hands_the_results_to_the_chosen_exporter(self):
        resource_id = uuid.uuid4()
        response = self._post_export_of([resource_id])

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            FakeExporter.received_post["module"], str(self.granted_module.pk)
        )
        self.assertEqual(FakeExporter.received_post["resource_ids"], [str(resource_id)])
        self.assertEqual(FakeExporter.received_post["filename"], "my_export")
        self.assertEqual(FakeExporter.received_post["export_concepts_as"], "uuids")

    def test_post_records_the_export_so_it_can_be_downloaded(self):
        response = self._post_export_of([uuid.uuid4(), uuid.uuid4()])

        export = SearchExportHistory.objects.get(pk=response.json()["loadid"])
        self.assertEqual(export.user, self.member)
        self.assertEqual(export.numberofinstances, 2)

    def test_post_discards_the_record_when_the_export_cannot_start(self):
        response = self._post_export_of([uuid.uuid4()], UnavailableExporter)

        self.assertEqual(response.status_code, 503)
        self.assertFalse(SearchExportHistory.objects.exists())

    def test_post_discards_the_record_when_the_exporter_raises(self):
        with self.assertLogs(VIEW_MODULE, level="ERROR"):
            response = self._post_export_of([uuid.uuid4()], BrokenExporter)

        self.assertEqual(response.status_code, 500)
        self.assertFalse(SearchExportHistory.objects.exists())
