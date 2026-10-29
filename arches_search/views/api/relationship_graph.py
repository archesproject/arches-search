import uuid
from collections import defaultdict

from django.db.models import Count
from django.utils.translation import gettext as _

from arches.app.models.models import GraphModel, ResourceInstance, ResourceXResource
from arches.app.utils.permission_backend import (
    filter_resource_queryset,
    user_can_read_resource,
)
from arches.app.utils.resource_relationship_utils import (
    get_resource_relationship_type_label,
)
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.readable_nodes import ReadableNodes

OUTGOING = "outgoing"
INCOMING = "incoming"


class RelationshipGraphSummaryAPI(APIBase):
    """Summarize the relationships of one resource, grouped by direction,
    relationship type, and the model of the resource on the other end.

    GET /arches_search/api/relationship-graph/summary?resource_id=<uuid>

    Response shape:
    {
        "resource_id": "<uuid>",
        "resource_model": {"id", "name", "color", "icon"},
        "rows": [
            {
                "id": "<direction>|<relationship type id>|<related model id>",
                "direction": "outgoing" | "incoming",
                "relationship_type_id": "...",
                "relationship_type_label": "...",
                "related_model": {"id", "name", "color", "icon"},
                "count": 3
            },
            ...
        ]
    }

    An incoming row is worded from this resource's side, so it carries the
    inverse relationship type, as the resource report does. Counts include
    only relationships the user can read, to resources the user can read.
    """

    def get(self, request):
        try:
            resource_id = uuid.UUID(request.GET.get("resource_id", ""))
        except (TypeError, ValueError):
            return JSONErrorResponse(_("Invalid resource ID"), status=400)

        resource = (
            ResourceInstance.objects.filter(pk=resource_id, graph__isresource=True)
            .select_related("graph")
            .first()
        )
        # A resource the user cannot read looks the same as one that is missing
        if resource is None or not user_can_read_resource(
            request.user, resource=resource
        ):
            return JSONErrorResponse(_("Resource not found"), status=404)

        counts = _count_relationships(request.user, resource_id)

        relationship_type_labels = _relationship_type_labels({key[1] for key in counts})
        models_by_id = _models_by_id({key[2] for key in counts} | {resource.graph_id})

        rows = []
        for (
            direction,
            relationship_type_id,
            related_graph_id,
        ), count in counts.items():
            rows.append(
                {
                    "id": f"{direction}|{relationship_type_id}|{related_graph_id}",
                    "direction": direction,
                    "relationship_type_id": relationship_type_id,
                    "relationship_type_label": relationship_type_labels[
                        relationship_type_id
                    ],
                    "related_model": models_by_id[related_graph_id],
                    "count": count,
                }
            )
        rows.sort(
            key=lambda row: (
                -row["count"],
                row["relationship_type_label"].lower(),
                row["related_model"]["name"].lower(),
                row["direction"],
            )
        )

        return JSONResponse(
            {
                "resource_id": str(resource_id),
                "resource_model": models_by_id[resource.graph_id],
                "rows": rows,
            }
        )


def _count_relationships(user, resource_id):
    """Count relationships by (direction, relationship type id, related graph id)."""
    relations = ReadableNodes(user).exclude_unreadable_relations(
        ResourceXResource.objects.all()
    )
    counts = defaultdict(int)

    outgoing = filter_resource_queryset(
        user,
        relations.filter(
            from_resource_id=resource_id, to_resource_graph__isresource=True
        ),
        resourceinstance_field="to_resource_id",
    )
    for row in (
        outgoing.order_by()
        .values("relationshiptype", "to_resource_graph_id")
        .annotate(count=Count("resourcexid"))
    ):
        key = (OUTGOING, row["relationshiptype"] or "", row["to_resource_graph_id"])
        counts[key] += row["count"]

    # A relationship to itself is counted once, as outgoing
    incoming = filter_resource_queryset(
        user,
        relations.filter(
            to_resource_id=resource_id, from_resource_graph__isresource=True
        ).exclude(from_resource_id=resource_id),
        resourceinstance_field="from_resource_id",
    )
    for row in (
        incoming.order_by()
        .values("relationshiptype", "inverserelationshiptype", "from_resource_graph_id")
        .annotate(count=Count("resourcexid"))
    ):
        # Without an inverse type, fall back to the forward one, as core does
        relationship_type_id = (
            row["inverserelationshiptype"] or row["relationshiptype"] or ""
        )
        key = (INCOMING, relationship_type_id, row["from_resource_graph_id"])
        counts[key] += row["count"]

    return counts


def _relationship_type_labels(relationship_type_ids):
    """Map each relationship type id to a display label. A type with no
    preferred label is shown as its raw value, trimmed to the last segment
    when that value is a URL."""
    preferred_labels = get_resource_relationship_type_label(relationship_type_ids)

    labels = {}
    for relationship_type_id in relationship_type_ids:
        label = preferred_labels.get(relationship_type_id) or relationship_type_id
        if label.startswith("http"):
            label = label.rsplit("/")[-1]
        labels[relationship_type_id] = label
    return labels


def _models_by_id(graph_ids):
    return {
        graph.pk: {
            "id": str(graph.pk),
            "name": str(graph.name),
            "color": graph.color,
            "icon": graph.iconclass,
        }
        for graph in GraphModel.objects.filter(pk__in=graph_ids)
    }
