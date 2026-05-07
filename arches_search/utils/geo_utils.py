import json

from django.contrib.gis.geos import GEOSGeometry

from arches.app.utils.geo_utils import GeoUtils as ArchesGeoUtils


class GeoUtils(ArchesGeoUtils):
    def split_polygon_at_antimeridian(self, geom):
        """
        If a polygon is drawn starting in the west and extends into the east, its eastern coordinates
        will be less that -180. If a polygon starts in the east and extends west, its western coordinates
        will exceed 180.
        To correct for this, adjust the coordinates in the extended area, and split the polygon into two
        using an intersection with polygon for the corresponding hemisphere.
        """

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
