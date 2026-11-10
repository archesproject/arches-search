import gzip
import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from arches_search.views.api.search_mvt import (
    SearchMVTAPI,
    _context_cache_key,
    _get_mvt_cache,
)

# python manage.py test tests.test_search_mvt_api --settings="tests.test_settings"

TILE = b"tile" * 1000
CONTEXT_BODY = {"groups": [{"op": "and", "clauses": []}]}
TEST_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "searchresults": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test_search_mvt_api",
    },
}
GENERATE_TILE = "arches_search.views.api.search_mvt.SearchMVTAPI._generate_tile"


@override_settings(CACHES=TEST_CACHES)
class SearchMVTAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="mvt_admin", email="mvt@example.com", password="x"
        )

    def setUp(self):
        _get_mvt_cache().clear()
        self.addCleanup(_get_mvt_cache().clear)
        self.client.force_login(self.admin)
        self.context_id = str(uuid.uuid4())
        _get_mvt_cache().set(_context_cache_key(self.context_id), CONTEXT_BODY, 3600)

    def _get_tile(self, **headers):
        url = reverse(
            "search_mvt",
            kwargs={"context_id": self.context_id, "zoom": 6, "x": 9, "y": 24},
        )
        return self.client.get(url, **headers)

    def test_cache_set_failure_still_returns_tile(self):
        with patch(GENERATE_TILE, return_value=TILE):
            with patch.object(
                _get_mvt_cache().__class__,
                "set",
                side_effect=Exception("object too large for cache"),
            ):
                response = self._get_tile()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, TILE)

    def test_cache_get_failure_regenerates_tile(self):
        original_get = _get_mvt_cache().__class__.get

        def failing_tile_get(cache, key, *args, **kwargs):
            if key.startswith("search:mvt:tile:"):
                raise Exception("cache unavailable")
            return original_get(cache, key, *args, **kwargs)

        with patch(GENERATE_TILE, return_value=TILE) as generate_tile:
            with patch.object(_get_mvt_cache().__class__, "get", failing_tile_get):
                response = self._get_tile()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, TILE)
        generate_tile.assert_called_once()

    def test_gzip_accepted_serves_gzipped_body(self):
        with patch(GENERATE_TILE, return_value=TILE):
            response = self._get_tile(HTTP_ACCEPT_ENCODING="gzip, deflate")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Encoding"], "gzip")
        self.assertEqual(gzip.decompress(response.content), TILE)
        self.assertIn("Accept-Encoding", response["Vary"])

    def test_gzip_not_accepted_serves_raw_body(self):
        with patch(GENERATE_TILE, return_value=TILE):
            response = self._get_tile()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, TILE)
        self.assertFalse(response.has_header("Content-Encoding"))
        self.assertIn("Accept-Encoding", response["Vary"])

    def test_second_request_is_served_from_cache(self):
        with patch(GENERATE_TILE, return_value=TILE) as generate_tile:
            first = self._get_tile()
            second = self._get_tile(HTTP_ACCEPT_ENCODING="gzip")

        generate_tile.assert_called_once()
        self.assertEqual(first.content, TILE)
        self.assertEqual(gzip.decompress(second.content), TILE)
        self.assertEqual(second["Content-Encoding"], "gzip")

    def test_empty_tile_has_no_content_encoding(self):
        with patch(GENERATE_TILE, return_value=b""):
            response = self._get_tile(HTTP_ACCEPT_ENCODING="gzip")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        self.assertFalse(response.has_header("Content-Encoding"))

    def test_unknown_context_returns_404(self):
        url = reverse(
            "search_mvt",
            kwargs={"context_id": str(uuid.uuid4()), "zoom": 6, "x": 9, "y": 24},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
