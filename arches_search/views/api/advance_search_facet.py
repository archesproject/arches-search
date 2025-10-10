from typing import Any, Dict, List

from arches.app.views.api import APIBase
from arches.app.utils.response import JSONResponse

from arches_search.models.models import AdvancedSearchFacet


class DatatypeFacetsAPI(APIBase):
    """
    GET /api/advanced-search/datatypes/<datatype>/facets

    Returns a list of facets for the given datatype, ordered by sortorder (then id).
    """

    def get(self, request, datatype):
        facets = AdvancedSearchFacet.objects.filter(datatype=datatype).order_by(
            "sortorder"
        )
        return JSONResponse(list(facets))


class AllDatatypeFacetsAPI(APIBase):
    """
    GET /api/advanced-search/facets

    Returns all facets grouped by datatype. Each group's items are ordered by
    sortorder (then id). The response shape is:

    {
        "<datatype>": [
            {
                "id": ...,
                "arity": ...,
                "label": ...,
                "operator": ...,
                "param_formats": [...],
                "sortorder": ...,
                "orm_template": "...",
                "is_orm_template_negated": false,
                "sql_template": "..."
            },
            ...
        ],
        ...
    }
    """

    def get(self, request):
        rows = AdvancedSearchFacet.objects.select_related("datatype").order_by(
            "datatype_id", "sortorder"
        )

        return JSONResponse(rows)
