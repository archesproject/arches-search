import json

from django.contrib.gis.geos import GEOSGeometry

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
        if isinstance(value, dict):
            value = json.dumps(value)
        geom = GEOSGeometry(value, srid=4326)
        split = GeoUtils().split_polygon_at_antimeridian(geom)
        if len(split) > 1:
            geom = split[0].union(split[1])
            geom.srid = 4326
        return geom
