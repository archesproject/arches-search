import uuid
from django.db import migrations


LAYER_UUID = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
SOURCE_NAME = "arches-search-results"
LAYER_NAME = "Search Results"
SOURCE_LAYER = "search-results"
COLOR = "#4f6ef7"


def add_map_layer(apps, schema_editor):
    MapSource = apps.get_model("models", "MapSource")
    MapLayer = apps.get_model("models", "MapLayer")

    MapSource.objects.get_or_create(
        name=SOURCE_NAME,
        defaults={
            "source": {
                "type": "vector",
                "tiles": ["/api/arches-search/mvt/empty/{z}/{x}/{y}.pbf"],
                "minzoom": 0,
                "maxzoom": 22,
            }
        },
    )

    layer_definitions = [
        {
            "id": "arches-search-results-fill",
            "type": "fill",
            "source": SOURCE_NAME,
            "source-layer": SOURCE_LAYER,
            "filter": ["==", "$type", "Polygon"],
            "paint": {
                "fill-color": COLOR,
                "fill-opacity": 0.25,
            },
        },
        {
            "id": "arches-search-results-fill-outline",
            "type": "line",
            "source": SOURCE_NAME,
            "source-layer": SOURCE_LAYER,
            "filter": ["==", "$type", "Polygon"],
            "paint": {
                "line-color": COLOR,
                "line-width": 1.5,
            },
        },
        {
            "id": "arches-search-results-line",
            "type": "line",
            "source": SOURCE_NAME,
            "source-layer": SOURCE_LAYER,
            "filter": ["==", "$type", "LineString"],
            "paint": {
                "line-color": COLOR,
                "line-width": 2,
            },
        },
        {
            "id": "arches-search-results-circle",
            "type": "circle",
            "source": SOURCE_NAME,
            "source-layer": SOURCE_LAYER,
            "filter": ["==", "$type", "Point"],
            "paint": {
                "circle-color": COLOR,
                "circle-radius": 5,
                "circle-stroke-color": "#ffffff",
                "circle-stroke-width": 1,
            },
        },
    ]

    MapLayer.objects.get_or_create(
        maplayerid=LAYER_UUID,
        defaults={
            "name": LAYER_NAME,
            "layerdefinitions": layer_definitions,
            "isoverlay": True,
            "addtomap": True,
            "activated": True,
            "icon": "fa fa-map-marker",
            "sortorder": 0,
        },
    )


def remove_map_layer(apps, schema_editor):
    MapSource = apps.get_model("models", "MapSource")
    MapLayer = apps.get_model("models", "MapLayer")

    MapLayer.objects.filter(maplayerid=LAYER_UUID).delete()
    MapSource.objects.filter(name=SOURCE_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("models", "0001_initial"),
        ("arches_search", "0019_node_filter_config"),
    ]

    operations = [
        migrations.RunPython(add_map_layer, remove_map_layer),
    ]
