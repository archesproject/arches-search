import json

from django.contrib.gis.geos import GEOSGeometry

from arches.app.models.system_settings import settings
from arches.app.utils.geo_utils import GeoUtils as ArchesGeoUtils

_BUFFER_UNIT_FACTORS = {
    "meters": 1,
    "kilometers": 1000,
    "feet": 0.3048,
    "miles": 1609.344,
    "yards": 0.9144,
}


class GeoUtils(ArchesGeoUtils):
    def split_polygon_at_antimeridian(self, geom):
        """
        If a polygon is drawn starting in the west and extends into the east, its eastern coordinates
        will be less that -180. If a polygon starts in the east and extends west, its western coordinates
        will exceed 180.
        To correct for this, adjust the coordinates in the extended area, and split the polygon into two
        using an intersection with polygon for the corresponding hemisphere.
        """

        if geom.srid != 4326:
            raise ValueError(
                f"split_polygon_at_antimeridian requires EPSG:4326, got EPSG:{geom.srid}"
            )

        if geom.dims == 2:
            geom_coords = geom.coords[0]
            extends_into_western_hemisphere = max(lon for lon, lat in geom_coords) > 180
            extends_into_eastern_hemisphere = (
                min(lon for lon, lat in geom_coords) < -180
            )
            east = GEOSGeometry(
                '{"coordinates": [[[180.0, 86.0],[0.0,    86.0],[0.0,    -86.0],[180.0, -86.0],[180.0, 86.0]]],"type": "Polygon"}'
            )
            west = GEOSGeometry(
                '{"coordinates": [[[0.0,   86.0],[-180.0, 86.0],[-180.0, -86.0],[0.0,   -86.0],[0.0, 86.0]]],"type": "Polygon"}'
            )

            if extends_into_western_hemisphere or extends_into_eastern_hemisphere:
                new_coords = []
                for coords in geom_coords:
                    lon, lat = coords
                    if extends_into_western_hemisphere:
                        lon = lon - 360 if lon > 180 else -179.99
                    elif extends_into_eastern_hemisphere:
                        lon = lon + 360 if lon < 180 else 179.99
                    new_coords.append([lon, lat])
                updated_geom = GEOSGeometry(
                    json.dumps(
                        {
                            "coordinates": [
                                new_coords,
                            ],
                            "type": "Polygon",
                        }
                    )
                )
                if extends_into_western_hemisphere:
                    return (geom.intersection(east), updated_geom.intersection(west))
                elif extends_into_eastern_hemisphere:
                    return (geom.intersection(west), updated_geom.intersection(east))

        return [geom]

    def map_filter_to_union(self, feature_collection):
        """
        Convert a map filter FeatureCollection to a single union GEOSGeometry.
        Features with buffer_distance + buffer_units properties are expanded before unioning.
        Returns None if the collection has no valid geometries.
        """
        union_geom = None
        for feature in feature_collection.get("features", []):
            if not feature.get("geometry"):
                continue
            geom = GEOSGeometry(json.dumps(feature["geometry"]))

            props = feature.get("properties") or {}
            buffer_distance = props.get("buffer_distance")
            buffer_units = props.get("buffer_units")

            if (
                buffer_distance
                and buffer_units
                and buffer_units in _BUFFER_UNIT_FACTORS
            ):
                distance_meters = buffer_distance * _BUFFER_UNIT_FACTORS[buffer_units]
                geom.transform(settings.ANALYSIS_COORDINATE_SYSTEM_SRID)
                geom = geom.buffer(distance_meters)
                geom.transform(4326)

            union_geom = geom if union_geom is None else union_geom.union(geom)

        return union_geom
