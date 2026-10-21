import os
import uuid

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.search import (
    SearchCompiler,
    SearchPayload,
    validate_search_payload,
)

# The ETL module slug of the Bulk Data Manager exporter behind each format.
EXPORTER_SLUGS = {
    "branch-excel": "branch-excel-exporter",
    "tile-excel": "tile-excel-exporter",
}
CONCEPTS_AS_CHOICES = ("labels", "uuids")
DEFAULT_FILENAME = "search_export"


class SearchResultsExportAPI(APIBase):
    """
    Hands a search's results to a Bulk Data Manager exporter, which queues the
    export on Celery. The user is told when the file is ready through an Arches
    notification, so this answers as soon as the export is queued.
    """

    def post(self, request):
        if not request.user.is_authenticated:
            return JSONResponse(
                {"error": _("User not authenticated. Access denied.")}, status=401
            )

        body = JSONDeserializer().deserialize(request.body)

        export_format = body.get("format")
        if export_format not in EXPORTER_SLUGS:
            return JSONResponse({"error": _("Unsupported export format.")}, status=400)

        export_concepts_as = body.get("exportConceptsAs", "labels")
        if export_concepts_as not in CONCEPTS_AS_CHOICES:
            return JSONResponse(
                {"error": _("exportConceptsAs must be 'labels' or 'uuids'.")},
                status=400,
            )

        search_payload = SearchPayload.from_body(body)
        if len(search_payload.graph_slugs or []) != 1:
            return JSONResponse(
                {"error": _("Select a single resource type to export.")}, status=400
            )

        try:
            validate_search_payload(search_payload)
            queryset = SearchCompiler(search_payload, request.user).compile().results
        except ValidationError as error:
            return JSONResponse({"error": str(error)}, status=400)

        graph = (
            models.GraphModel.objects.filter(
                slug=search_payload.graph_slugs[0], isresource=True
            )
            .values("graphid", "name")
            .first()
        )
        if graph is None:
            return JSONResponse({"error": _("Unknown resource type.")}, status=400)

        resource_ids = [
            str(resource_id)
            for resource_id in queryset.filter(graph_id=graph["graphid"]).values_list(
                "resourceinstanceid", flat=True
            )
        ]
        if not resource_ids:
            return JSONResponse(
                {"error": _("There are no results to export.")}, status=400
            )

        etl_module = models.ETLModule.objects.get(slug=EXPORTER_SLUGS[export_format])
        load_id = str(uuid.uuid4())

        request.POST = {
            "module": str(etl_module.pk),
            "load_id": load_id,
            "graph_id": str(graph["graphid"]),
            "graph_name": str(graph["name"]),
            "resource_ids": resource_ids,
            "export_concepts_as": export_concepts_as,
            # The exporters add ".zip" themselves.
            "filename": os.path.basename(str(body.get("filename") or "").strip())
            or DEFAULT_FILENAME,
        }
        exporter = etl_module.get_class_module()(request=request)
        response = exporter.export(request)

        if not response["success"]:
            return JSONResponse({"error": response["data"]["message"]}, status=503)
        return JSONResponse(
            {"loadid": load_id, "message": _("Your export has started.")}, status=202
        )
