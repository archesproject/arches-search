from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils.translation import get_language

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.etl_modules.search_results_export import SearchResultsExportModule
from arches_search.utils.search import (
    SearchCompiler,
    SearchPayload,
    validate_search_payload,
)


class SearchExportAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        filename = body.get("filename", "search_export")
        all_descriptors = body.get("allDescriptors", False)

        if not filename.endswith(".xlsx"):
            filename = f"{filename}.xlsx"

        language = None if all_descriptors else get_language()

        # Only the matching queryset is needed, so this stops short of the
        # projection and pagination execute_search layers on top -- but the same
        # payload checks still run, or an export could quietly cover a different
        # set of resources than the search it came from.
        search_payload = SearchPayload.from_body(body)
        try:
            validate_search_payload(search_payload)
            queryset = SearchCompiler(search_payload, request.user).compile().results
        except ValidationError as error:
            return JSONResponse({"error": str(error)}, status=400)

        exporter = SearchResultsExportModule()
        excel_bytes = exporter.export(queryset, language=language)

        response = HttpResponse(
            excel_bytes.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
