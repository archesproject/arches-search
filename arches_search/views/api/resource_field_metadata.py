from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.resource_field_search.metadata import (
    resource_field_metadata,
)


class ResourceFieldMetadataAPI(APIBase):
    def get(self, request):
        return JSONResponse(
            {"fields": resource_field_metadata(request.GET.getlist("graph_slugs"))}
        )
