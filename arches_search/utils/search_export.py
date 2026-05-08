from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font


def _get_descriptor(descriptors, language, field):
    """Extract a descriptor field for the given language, with fallback."""
    if not descriptors:
        return ""
    lang_descriptors = descriptors.get(language)
    if not lang_descriptors:
        first_key = next(iter(descriptors), None)
        if first_key is None:
            return ""
        lang_descriptors = descriptors[first_key]
    return lang_descriptors.get(field, "")


class SearchExcelExporter:
    COLUMNS = ["resourceinstanceid", "graph_slug", "name", "description"]

    def export(self, queryset, language="en"):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Search Results"

        header_font = Font(bold=True)
        for col_index, header in enumerate(self.COLUMNS, start=1):
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
                value=_get_descriptor(resource.descriptors, language, "name"),
            )
            worksheet.cell(
                row=row_index,
                column=4,
                value=_get_descriptor(
                    resource.descriptors, language, "description"
                ),
            )

        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        return output
