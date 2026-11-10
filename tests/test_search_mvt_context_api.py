import json
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.test import TestCase, override_settings
from django.urls import reverse

from arches.app.models.models import GraphModel

from arches_search.utils.search import SearchCompiler
from arches_search.views.api.search_mvt import SearchMVTAPI

# python manage.py test tests.test_search_mvt_context_api --settings="tests.test_settings"

TILE_BYTES = b"fixed-tile"
SEARCHRESULTS_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "searchresults": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "mvt-context-test",
    },
}


@override_settings(CACHES=SEARCHRESULTS_CACHES)
class SearchMVTSkipsCountTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username="mvt-context-admin",
            email="mvt-context@example.com",
            password="password",
        )
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="MVT",
            slug="mvt-context-graph",
            isresource=True,
            is_active=True,
        )

    def setUp(self):
        self.client.force_login(self.user)
        compile_patcher = patch.object(
            SearchCompiler,
            "compile",
            side_effect=AssertionError("compile() should not be called"),
        )
        compile_patcher.start()
        self.addCleanup(compile_patcher.stop)

    def _post_context(self, body):
        return self.client.post(
            reverse("search_mvt_context"),
            json.dumps(body),
            content_type="application/json",
        )

    def test_a_valid_context_is_created_without_compile(self):
        response = self._post_context({"graph_slugs": [self.graph.slug]})

        self.assertEqual(response.status_code, 200)
        self.assertIn("context_id", response.json())

    def test_an_invalid_payload_is_still_a_400(self):
        response = self._post_context(
            {
                "graph_slugs": [self.graph.slug],
                "advanced_search_queries": [
                    {
                        "graph_slug": self.graph.slug + "-typo",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_a_tile_is_generated_from_the_matches_without_compile(self):
        context_id = self._post_context({"graph_slugs": [self.graph.slug]}).json()[
            "context_id"
        ]

        with patch.object(
            SearchMVTAPI, "_generate_tile", return_value=TILE_BYTES
        ) as generate_tile:
            response = self.client.get(
                reverse(
                    "search_mvt",
                    kwargs={"context_id": context_id, "zoom": 6, "x": 9, "y": 24},
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, TILE_BYTES)
        self.assertIsInstance(generate_tile.call_args.args[0], QuerySet)
