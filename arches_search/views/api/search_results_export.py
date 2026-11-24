import logging
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
from arches_search.utils.search_results_export import record_pending_export

EXPORT_ETL_TYPE = "export"
VIEW_ETL_MODULE_PERMISSION = "view_etlmodule"
# The exporters that honor export_concepts_as; others ignore it.
EXPORTERS_OFFERING_CONCEPTS_AS = {"tile-excel-exporter"}
CONCEPTS_AS_CHOICES = ("labels", "uuids")
DEFAULT_CONCEPTS_AS = "labels"
DEFAULT_FILENAME = "search_export"

logger = logging.getLogger(__name__)


def get_available_exporters(user):
    """
    The Bulk Data Manager exporters this user may run, decided by the same rules
    the Bulk Data Manager applies to its own module list: modules configured
    with "show": false are hidden, and the user needs view_etlmodule on the
    module. Admins grant that permission per user or group from the ETL module
    admin page, or for every module with `manage.py permissions`.
    """
    return [
        etl_module
        for etl_module in models.ETLModule.objects.filter(
            etl_type=EXPORT_ETL_TYPE, slug__isnull=False
        )
        if (etl_module.config or {}).get("show") is not False
        and user.has_perm(VIEW_ETL_MODULE_PERMISSION, etl_module)
    ]


class SearchResultsExportAPI(APIBase):
    """
    Hands a search's results to a Bulk Data Manager exporter, which queues the
    export on Celery. The user is told when the file is ready through an Arches
    notification, so this answers as soon as the export is queued.

    A format is the slug of an exporter's ETL module. GET lists the formats the
    user may choose from, and whether each offers a choice of exporting
    concepts as labels or UUIDs.

    Every visible export module is offered, so each must follow the contract
    branch-excel and tile-excel follow:
      - it is built as cls(request=request) and export(request) reads
        module, load_id, graph_id, graph_name, resource_ids,
        export_concepts_as and filename from request.POST;
      - export() queues its work with load_data_async and returns
        {"success": bool, "data": {...}}, with data["message"] on failure;
      - the task writes the zip's TempFile id to load_details.zipfile.fileid,
        which arches_search.utils.search_results_export uses to link the file.
    An exporter that raises instead is reported as a 500 and its pending
    export record is discarded.
    """

    def get(self, request):
        if not request.user.is_authenticated:
            return JSONResponse(
                {"error": _("User not authenticated. Access denied.")}, status=401
            )

        return JSONResponse(
            [
                {
                    "slug": etl_module.slug,
                    "name": str(etl_module.name),
                    "description": str(etl_module.description or ""),
                    "offersExportConceptsAs": etl_module.slug
                    in EXPORTERS_OFFERING_CONCEPTS_AS,
                }
                for etl_module in get_available_exporters(request.user)
            ]
        )

    def post(self, request):
        if not request.user.is_authenticated:
            return JSONResponse(
                {"error": _("User not authenticated. Access denied.")}, status=401
            )

        body = JSONDeserializer().deserialize(request.body)

        export_format = body.get("format")
        etl_module = next(
            (
                exporter
                for exporter in get_available_exporters(request.user)
                if exporter.slug == export_format
            ),
            None,
        )
        # Also the answer when the user lacks permission on the module, so the
        # response does not disclose which exporters exist.
        if etl_module is None:
            return JSONResponse({"error": _("Unsupported export format.")}, status=400)

        export_concepts_as = body.get("exportConceptsAs", DEFAULT_CONCEPTS_AS)
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
            queryset = (
                SearchCompiler(search_payload, request.user)
                .compile(return_counts=False)
                .results
            )
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
        # Recorded before the export is queued so the task cannot finish first;
        # see arches_search.utils.search_results_export.
        pending_export = record_pending_export(load_id, request.user, len(resource_ids))
        try:
            exporter = etl_module.get_class_module()(request=request)
            response = exporter.export(request)
        except Exception:
            logger.exception(
                "Exporter %s failed to start search export %s",
                etl_module.slug,
                load_id,
            )
            pending_export.delete()
            return JSONResponse({"error": _("The export could not start.")}, status=500)

        if not response["success"]:
            pending_export.delete()
            return JSONResponse({"error": response["data"]["message"]}, status=503)
        return JSONResponse(
            {"loadid": load_id, "message": _("Your export has started.")}, status=202
        )
