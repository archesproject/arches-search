import sqlparse

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)


class AdvancedSearchSQLAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)

        queryset = AdvancedSearchQueryCompiler(body).compile()
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
