import functools
import uuid

from django.core.cache import caches
from django.core.cache.backends.dummy import DummyCache
from django.core.exceptions import ValidationError
from django.db import connection
from django.http import Http404, HttpResponse

from arches.app.models.system_settings import settings
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.search import (
    SearchCompiler,
    SearchPayload,
    validate_search_payload,
)

MVT_LAYER_NAME = "search-results"
CONTEXT_CACHE_TIMEOUT = 3600


@functools.cache
def _locmem_fallback():
    from django.core.cache.backends.locmem import LocMemCache

    return LocMemCache("arches_search_mvt", {})


def _get_mvt_cache():
    for cache_alias in ("searchresults", "default"):
        try:
            backend = caches[cache_alias]
            if not isinstance(backend, DummyCache):
                return backend
        except Exception:
            continue
    return _locmem_fallback()


def _context_cache_key(context_id):
    return f"search:mvt:{context_id}"


def _tile_cache_key(context_id, user_id, zoom, x, y):
    return f"search:mvt:tile:{context_id}:{user_id}:{zoom}:{x}:{y}"


class EmptySearchTileAPI(APIBase):
    def get(self, request, **_):
        return HttpResponse(b"", content_type="application/x-protobuf")


class SearchMVTContextAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        # Checked here, not at tile time, where there is no way to report it.
        try:
            validate_search_payload(SearchPayload.from_body(body))
        except ValidationError as error:
            return JSONResponse({"error": str(error)}, status=400)

        context_id = str(uuid.uuid4())
        _get_mvt_cache().set(
            _context_cache_key(context_id), body, CONTEXT_CACHE_TIMEOUT
        )
        return JSONResponse({"context_id": context_id})


class SearchMVTAPI(APIBase):
    def get(self, request, context_id, zoom, x, y):
        mvt_cache = _get_mvt_cache()
        body = mvt_cache.get(_context_cache_key(context_id))
        if body is None:
            raise Http404()

        tile_key = _tile_cache_key(context_id, request.user.id, zoom, x, y)
        cached_tile = mvt_cache.get(tile_key)
        if cached_tile is not None:
            return HttpResponse(cached_tile, content_type="application/x-protobuf")

        search_result = SearchCompiler(
            SearchPayload.from_body(body), request.user
        ).compile()

        search_results_queryset = search_result.results.values("resourceinstanceid")
        mvt_tile = self._generate_tile(search_results_queryset, zoom, x, y)

        mvt_cache.set(tile_key, mvt_tile, settings.TILE_CACHE_TIMEOUT)

        return HttpResponse(mvt_tile, content_type="application/x-protobuf")

    def _generate_tile(self, search_results_queryset, zoom, x, y):
        compiler = search_results_queryset.query.get_compiler(using="default")
        sub_sql, sub_params = compiler.as_sql()

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT ST_AsMVT(tile, %s, 4096, 'geom', 'id') FROM (
                    SELECT
                        id,
                        resourceinstanceid,
                        nodeid,
                        ST_AsMVTGeom(
                            geom,
                            TileBBox(%s, %s, %s, 3857),
                            4096,
                            256,
                            false
                        ) AS geom
                    FROM geojson_geometries
                    WHERE resourceinstanceid IN ({sub_sql})
                    AND geom && ST_TileEnvelope(%s, %s, %s, margin => (64.0 / 4096))
                ) AS tile
                """,
                [MVT_LAYER_NAME, zoom, x, y, *sub_params, zoom, x, y],
            )
            mvt_query_row = cursor.fetchone()
        return bytes(mvt_query_row[0]) if mvt_query_row and mvt_query_row[0] else b""
