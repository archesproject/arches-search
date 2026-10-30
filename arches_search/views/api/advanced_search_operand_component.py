from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.models.models import AdvancedSearchOperandComponent


class AdvancedSearchOperandComponentsAPI(APIBase):
    def get(self, request):
        operand_components = AdvancedSearchOperandComponent.objects.order_by(
            "datatype_id"
        )
        return JSONResponse(list(operand_components))
