from typing import Any, Dict, List

from arches.app.views.api import APIBase
from arches.app.utils.response import JSONResponse

from arches_search.models.models import AdvancedSearchFacet


class DatatypeFacetsAPI(APIBase):
    def get(self, request, datatype):
        facets = AdvancedSearchFacet.objects.filter(datatype=datatype).order_by(
            "sortorder"
        )
        return JSONResponse(list(facets))


class AllDatatypeFacetsAPI(APIBase):
    def get(self, request):
        facets = AdvancedSearchFacet.objects.select_related("datatype").order_by(
            "datatype_id", "sortorder"
        )
        return JSONResponse(list(facets))
