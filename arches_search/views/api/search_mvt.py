import functools
import uuid

from django.core.cache import caches
from django.core.cache.backends.dummy import DummyCache
from django.db import connection
from django.http import Http404, HttpResponse

from arches.app.models.system_settings import settings
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.views.api.simple_search import build_search_queryset


MVT_LAYER_NAME = "search-results"
CONTEXT_CACHE_TIMEOUT = 3600


@functools.cache
def _locmem_fallback():
    from django.core.cache.backends.locmem import LocMemCache

    return LocMemCache("arches_search_mvt", {})


def _get_mvt_cache():
    for alias in ("searchresults", "default"):
        try:
            backend = caches[alias]
            if not isinstance(backend, DummyCache):
                return backend
        except Exception:
            continue
    return _locmem_fallback()


def _context_cache_key(context_id):
    return f"search:mvt:{context_id}"


def _tile_cache_key(context_id, zoom, x, y):
    return f"search:mvt:tile:{context_id}:{zoom}:{x}:{y}"


class EmptySearchTileAPI(APIBase):
    def get(self, request, **_):
        return HttpResponse(b"", content_type="application/x-protobuf")


class SearchMVTContextAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        context_id = str(uuid.uuid4())
        _get_mvt_cache().set(
            _context_cache_key(context_id), body, CONTEXT_CACHE_TIMEOUT
        )
        return JSONResponse({"context_id": context_id})


class SearchMVTAPI(APIBase):
    def get(self, request, context_id, zoom, x, y):
        cache = _get_mvt_cache()
        body = cache.get(_context_cache_key(context_id))
        if body is None:
            raise Http404()

        tile_key = _tile_cache_key(context_id, zoom, x, y)
        cached_tile = cache.get(tile_key)
        if cached_tile is not None:
            return HttpResponse(cached_tile, content_type="application/x-protobuf")

        qs = build_search_queryset(body).values("resourceinstanceid")
        tile = self._generate_tile(qs, zoom, x, y)

        cache.set(tile_key, tile, settings.TILE_CACHE_TIMEOUT)

        return HttpResponse(tile, content_type="application/x-protobuf")

    def _generate_tile(self, qs, zoom, x, y):
        compiler = qs.query.get_compiler(using="default")
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
            row = cursor.fetchone()
        return bytes(row[0]) if row and row[0] else b""
