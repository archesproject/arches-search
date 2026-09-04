import json

from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches.app.datatypes.datatypes import DataTypeFactory

from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)
from arches_search.utils.geo_utils import GeoUtils


class GeojsonFeatureCollectionOperandNormalizer(BaseOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("geojson-feature-collection")

    def normalize_value(self, operand_item):
        value = operand_item.get("value")

        if isinstance(value, dict) and value.get("type") == "FeatureCollection":
            return self._union_feature_collection(value)

        if isinstance(value, dict):
            value = json.dumps(value)

        # GEOSGeometry raises GEOSException/ValueError, which would surface as
        # a 500 where a bad FeatureCollection gives a 400.
        try:
            geom = GEOSGeometry(value, srid=4326)
            split = GeoUtils().split_polygon_at_antimeridian(geom)
        except ValidationError:
            raise
        except Exception as error:
            raise ValidationError(
                _("Could not read the geometry operand: %(reason)s.")
                % {"reason": error}
            )

        if len(split) > 1:
            geom = split[0].union(split[1])
            geom.srid = 4326
        return geom

    @staticmethod
    def _union_feature_collection(feature_collection):
        """
        A FeatureCollection is not a geometry, so it is reduced to one.

        Each feature may carry its own buffer_distance/buffer_units, which have
        to be applied before the features are unioned -- the same conversion a
        map filter has always used.

        The antimeridian split above is deliberately not applied here. Unioning
        several features usually yields a MultiPolygon, which that helper cannot
        walk (it reads a Polygon's exterior ring), and map filters have never
        been split -- so leaving them alone keeps this identical to the filter it
        replaces.
        """
        union_geometry = GeoUtils().map_filter_to_union(feature_collection)
        if union_geometry is None:
            raise ValidationError(
                _("A geometry operand must carry at least one geometry.")
            )
        if union_geometry.srid is None:
            union_geometry.srid = 4326
        return union_geometry
