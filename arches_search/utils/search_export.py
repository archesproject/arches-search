from io import BytesIO

from django.db.models import F, Func
from openpyxl import Workbook
from openpyxl.styles import Font

class SearchExcelExporter:
    BASE_COLUMNS = ["resourceinstanceid", "graph_slug", "name"]

    def export(self, queryset):
        languages = self._collect_languages(queryset)
        columns = self.BASE_COLUMNS + [f"{lang}-description" for lang in languages]

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Search Results"

        header_font = Font(bold=True)
        for col_index, header in enumerate(columns, start=1):
            cell = worksheet.cell(row=1, column=col_index, value=header)
            cell.font = header_font

        for row_index, resource in enumerate(
            queryset.select_related("graph").iterator(), start=2
        ):
            worksheet.cell(
                row=row_index,
                column=1,
                value=str(resource.resourceinstanceid),
            )
            worksheet.cell(
                row=row_index,
                column=2,
                value=resource.graph.slug if resource.graph else "",
            )
            worksheet.cell(
                row=row_index,
                column=3,
                value=str(resource.name),
            )
            for col_offset, lang in enumerate(languages, start=4):
                descriptor = (resource.descriptors or {}).get(lang)
                description = descriptor.get("description", "") if descriptor else ""
                if description == "Undefined":
                    description = ""
                
                worksheet.cell(
                    row=row_index,
                    column=col_offset,
                    value=description,
                )

        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        return output

    @staticmethod
    def _collect_languages(queryset):
        return sorted(
            queryset
            .filter(descriptors__isnull=False)
            .annotate(lang=Func(F("descriptors"), function="JSONB_OBJECT_KEYS"))
            .values_list("lang", flat=True)
            .distinct()
        )
