from django.http import HttpResponse
from django.utils.translation import get_language

from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.views.api import APIBase

from arches_search.utils.search_export import SearchExcelExporter
from arches_search.views.api.simple_search import build_search_queryset


class SearchExportAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        filename = body.get("filename", "search_export")
        all_descriptors = body.get("allDescriptors", False)

        if not filename.endswith(".xlsx"):
            filename = f"{filename}.xlsx"

        language = None if all_descriptors else get_language()
        queryset = queryset = build_search_queryset(body)

        exporter = SearchExcelExporter()
        excel_bytes = exporter.export(queryset, language=language)

        response = HttpResponse(
            excel_bytes.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
