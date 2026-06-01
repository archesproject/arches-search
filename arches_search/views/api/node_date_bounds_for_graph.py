import logging
from http import HTTPStatus

from django.db.models import Max, Min
from django.utils.translation import gettext as _

from arches.app.models import models as arches_models
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.views.api import APIBase

from arches_search.models.models import DateRangeSearch, DateSearch

logger = logging.getLogger(__name__)


class NodeDateBoundsForGraphAPI(APIBase):
    def get(self, request, graph_id):
        try:
            graph_slug = arches_models.GraphModel.objects.values_list(
                "slug", flat=True
            ).get(pk=graph_id)
        except arches_models.GraphModel.DoesNotExist:
            return JSONErrorResponse(
                message=_("Graph not found."), status=HTTPStatus.NOT_FOUND
            )

        all_date_node_aliases = set(
            arches_models.Node.objects.filter(
                graph_id=graph_id,
                datatype__in=["date", "edtf"],
                issearchable=True,
            ).values_list("alias", flat=True)
        )

        requested_aliases = request.GET.getlist("node_alias")
        if requested_aliases:
            date_node_aliases = [
                alias for alias in requested_aliases if alias in all_date_node_aliases
            ]
        else:
            date_node_aliases = list(all_date_node_aliases)

        node_alias_filter = {
            "graph_slug": graph_slug,
            "node_alias__in": date_node_aliases,
        }

        date_search_bounds = DateSearch.objects.filter(**node_alias_filter).aggregate(
            min_value=Min("value"), max_value=Max("value")
        )
        date_range_search_bounds = DateRangeSearch.objects.filter(
            **node_alias_filter
        ).aggregate(min_start_value=Min("start_value"), max_end_value=Max("end_value"))

        min_candidates = [
            candidate
            for candidate in [
                date_search_bounds["min_value"],
                date_range_search_bounds["min_start_value"],
            ]
            if candidate is not None
        ]
        max_candidates = [
            candidate
            for candidate in [
                date_search_bounds["max_value"],
                date_range_search_bounds["max_end_value"],
            ]
            if candidate is not None
        ]

        return JSONResponse(
            {
                "min_value": min(min_candidates) if min_candidates else None,
                "max_value": max(max_candidates) if max_candidates else None,
            }
        )
