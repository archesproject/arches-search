from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path

from arches_search.views.api.advanced_search import AdvancedSearchAPI
from arches_search.views.api.advance_search_facet import (
    DatatypeFacetsAPI,
    AllDatatypeFacetsAPI,
)
from arches_search.views.api.graph_models import GraphModelsAPI
from arches_search.views.api.graph_nodes import GraphNodesAPI

from arches_search.views.api.graph_models import GraphModelsAPI
from arches_search.views.api.nodes_with_widget_labels_for_graph import (
    NodesWithWidgetLabelsForGraphAPI,
)

urlpatterns = [
    path("api/advanced-search", AdvancedSearchAPI.as_view(), name="advanced_search"),
    path(
        "api/advanced-search/datatypes/<str:datatype>/facets",
        DatatypeFacetsAPI.as_view(),
        name="datatype_facets",
    ),
    path(
        "api/advanced-search/facets",
        AllDatatypeFacetsAPI.as_view(),
        name="all_datatype_facets",
    ),
    path(
        "api/advanced-search/graph/models",
        GraphModelsAPI.as_view(),
        name="graph_models",
    ),
    path(
        "api/advanced-search/graph/<uuid:graph_id>/nodes",
        NodesWithWidgetLabelsForGraphAPI.as_view(),
        name="nodes_with_widget_labels_for_graph",
    ),
]

handler400 = "arches.app.views.main.custom_400"
handler403 = "arches.app.views.main.custom_403"
handler404 = "arches.app.views.main.custom_404"
handler500 = "arches.app.views.main.custom_500"

# Ensure Arches core urls are superseded by project-level urls
urlpatterns.append(path("", include("arches_controlled_lists.urls")))
urlpatterns.append(path("", include("arches_component_lab.urls")))
urlpatterns.append(path("", include("arches_querysets.urls")))

urlpatterns.append(path("", include("arches.urls")))

# Adds URL pattern to serve media files during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Only handle i18n routing in active project. This will still handle the routes provided by Arches core and Arches applications,
# but handling i18n routes in multiple places causes application errors.
if settings.ROOT_URLCONF == __name__:
    if settings.SHOW_LANGUAGE_SWITCH is True:
        urlpatterns = i18n_patterns(*urlpatterns)

    urlpatterns.append(path("i18n/", include("django.conf.urls.i18n")))
