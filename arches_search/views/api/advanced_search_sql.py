import sqlparse
from django.core.exceptions import ValidationError

from arches.app.utils import permission_backend
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)


class AdvancedSearchSQLAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        try:
            queryset = AdvancedSearchQueryCompiler(body, user=request.user).compile()
        except ValidationError as error:
            return JSONResponse({"error": str(error)}, status=400)
        queryset = permission_backend.filter_resource_queryset(request.user, queryset)
        raw_sql = str(queryset.query)

        formatted_sql = sqlparse.format(
            raw_sql,
            indent_width=4,
            keyword_case="upper",
            reindent=True,
        )

        return JSONResponse(
            {
                "sql": formatted_sql,
            }
        )
