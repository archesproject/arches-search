import uuid
from collections import defaultdict

from django.db.models import Count, F, Q
from django.utils.translation import get_language, gettext as _

from arches.app.models.models import GraphModel, ResourceInstance, ResourceXResource
from arches.app.utils.permission_backend import (
    filter_resource_queryset,
    user_can_read_resource,
)
from arches.app.utils.resource_relationship_utils import (
    get_resource_relationship_type_label,
)
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.readable_nodes import ReadableNodes

OUTGOING = "outgoing"
INCOMING = "incoming"

MAX_SELECTED_RESOURCES = 10
MAX_GRAPH_NODES = 300


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


class RelationshipGraphAPI(APIBase):
    """The resources and relationships to draw, for the summary rows the user
    has selected on one or more resources.

    POST /arches_search/api/relationship-graph/graph

    Request body:
    {
        "selections": [
            {"resource_id": "<uuid>", "row_ids": ["<summary row id>", ...]},
            ...
        ]
    }

    A row id is the id the summary endpoint gave the row. The graph holds each
    selected resource, plus the resources on the far end of the relationships
    its selected rows stand for. A resource with no selected rows is still
    drawn, on its own.

    Response shape:
    {
        "nodes": [
            {
                "id": "<uuid>",
                "name": "...",
                "model": {"id", "name", "color", "icon"},
                "is_seed": true,
                "related_count": 12
            },
            ...
        ],
        "edges": [
            {
                "id": "<resourcexid>",
                "source": "<uuid>",
                "target": "<uuid>",
                "relationship_type_id": "...",
                "relationship_type_label": "..."
            },
            ...
        ],
        "truncated": false,
        "node_limit": 300
    }

    The graph stops adding resources at the node limit and says so with
    `truncated`. Only readable resources and relationships are included.
    """

    def post(self, request):
        try:
            selections = _parse_selections(JSONDeserializer().deserialize(request.body))
        except ValueError:
            return JSONErrorResponse(_("Invalid selection"), status=400)

        seed_ids = [resource_id for resource_id, _rows in selections]
        seeds = ResourceInstance.objects.filter(pk__in=seed_ids, graph__isresource=True)
        if len(seeds) != len(seed_ids) or not all(
            user_can_read_resource(request.user, resource=seed) for seed in seeds
        ):
            return JSONErrorResponse(_("Resource not found"), status=404)

        readable_nodes = ReadableNodes(request.user)
        relations_by_id = {}
        for resource_id, rows in selections:
            relations_by_id.update(
                _selected_relations(request.user, readable_nodes, resource_id, rows)
            )

        node_ids = set(seed_ids)
        relations = []
        truncated = False
        for relation in sorted(
            relations_by_id.values(), key=lambda row: str(row["resourcexid"])
        ):
            ends = {relation["from_resource_id"], relation["to_resource_id"]}
            if len(node_ids | ends) > MAX_GRAPH_NODES:
                truncated = True
                continue
            node_ids |= ends
            relations.append(relation)

        relationship_type_labels = _relationship_type_labels(
            {relation["relationshiptype"] or "" for relation in relations}
        )
        related_counts = _related_counts(request.user, readable_nodes, node_ids)
        resources = ResourceInstance.objects.filter(pk__in=node_ids).select_related(
            "graph"
        )
        models_by_id = _models_by_id({resource.graph_id for resource in resources})

        return JSONResponse(
            {
                "nodes": [
                    {
                        "id": str(resource.pk),
                        "name": _display_name(resource),
                        "model": models_by_id[resource.graph_id],
                        "is_seed": resource.pk in seed_ids,
                        "related_count": related_counts[resource.pk],
                    }
                    for resource in resources
                ],
                "edges": [
                    {
                        "id": str(relation["resourcexid"]),
                        "source": str(relation["from_resource_id"]),
                        "target": str(relation["to_resource_id"]),
                        "relationship_type_id": relation["relationshiptype"] or "",
                        "relationship_type_label": relationship_type_labels[
                            relation["relationshiptype"] or ""
                        ],
                    }
                    for relation in relations
                ],
                "truncated": truncated,
                "node_limit": MAX_GRAPH_NODES,
            }
        )


def _parse_selections(body):
    """Read the request body as a list of (resource id, [(direction,
    relationship type id, related graph id), ...]). Raises ValueError for
    anything that is not shaped like that."""
    selections = body.get("selections") if isinstance(body, dict) else None
    if (
        not isinstance(selections, list)
        or not 0 < len(selections) <= MAX_SELECTED_RESOURCES
    ):
        raise ValueError("selections")

    parsed = {}
    for selection in selections:
        if not isinstance(selection, dict) or not isinstance(
            selection.get("row_ids"), list
        ):
            raise ValueError("selection")
        resource_id = uuid.UUID(str(selection.get("resource_id")))
        parsed[resource_id] = [_parse_row_id(row_id) for row_id in selection["row_ids"]]
    return list(parsed.items())


def _parse_row_id(row_id):
    """Split a summary row id, "<direction>|<relationship type id>|<graph id>".
    The type id may itself contain "|", the graph id never does."""
    if not isinstance(row_id, str):
        raise ValueError("row id")
    direction, _separator, rest = row_id.partition("|")
    relationship_type_id, separator, graph_id = rest.rpartition("|")
    if direction not in (OUTGOING, INCOMING) or not separator:
        raise ValueError("row id")
    return direction, relationship_type_id, uuid.UUID(graph_id)


def _is_blank(field):
    return Q(**{f"{field}__isnull": True}) | Q(**{field: ""})


def _outgoing_row_filter(relationship_type_id, graph_id):
    if relationship_type_id:
        type_filter = Q(relationshiptype=relationship_type_id)
    else:
        type_filter = _is_blank("relationshiptype")
    return type_filter & Q(to_resource_graph_id=graph_id)


def _incoming_row_filter(relationship_type_id, graph_id):
    # An incoming row is worded from the resource's side, so it is the inverse
    # type, or the forward one when no inverse was recorded
    if relationship_type_id:
        type_filter = Q(inverserelationshiptype=relationship_type_id) | (
            _is_blank("inverserelationshiptype")
            & Q(relationshiptype=relationship_type_id)
        )
    else:
        type_filter = _is_blank("inverserelationshiptype") & _is_blank(
            "relationshiptype"
        )
    return type_filter & Q(from_resource_graph_id=graph_id)


def _selected_relations(user, readable_nodes, resource_id, rows):
    """The relationships of one resource that the summary rows stand for, as
    {resourcexid: {resourcexid, from_resource_id, to_resource_id,
    relationshiptype}}. Mirrors how the summary groups relationships, so a
    row selects exactly the relationships it counted."""
    outgoing_rows = Q()
    incoming_rows = Q()
    for direction, relationship_type_id, graph_id in rows:
        if direction == OUTGOING:
            outgoing_rows |= _outgoing_row_filter(relationship_type_id, graph_id)
        else:
            incoming_rows |= _incoming_row_filter(relationship_type_id, graph_id)

    relations = readable_nodes.exclude_unreadable_relations(
        ResourceXResource.objects.all()
    )
    querysets = []
    if outgoing_rows:
        querysets.append(
            filter_resource_queryset(
                user,
                relations.filter(
                    outgoing_rows,
                    from_resource_id=resource_id,
                    to_resource_graph__isresource=True,
                ),
                resourceinstance_field="to_resource_id",
            )
        )
    if incoming_rows:
        querysets.append(
            filter_resource_queryset(
                user,
                relations.filter(
                    incoming_rows,
                    to_resource_id=resource_id,
                    from_resource_graph__isresource=True,
                ).exclude(from_resource_id=resource_id),
                resourceinstance_field="from_resource_id",
            )
        )

    return {
        relation["resourcexid"]: relation
        for queryset in querysets
        for relation in queryset.order_by().values(
            "resourcexid", "from_resource_id", "to_resource_id", "relationshiptype"
        )
    }


def _related_counts(user, readable_nodes, resource_ids):
    """How many readable relationships each resource has, to readable
    resources, in either direction. A relationship to itself counts once."""
    relations = readable_nodes.exclude_unreadable_relations(
        ResourceXResource.objects.filter(
            from_resource_graph__isresource=True, to_resource_graph__isresource=True
        )
    )
    counts = defaultdict(int)

    outgoing = filter_resource_queryset(
        user,
        relations.filter(from_resource_id__in=resource_ids),
        resourceinstance_field="to_resource_id",
    )
    for row in (
        outgoing.order_by()
        .values("from_resource_id")
        .annotate(count=Count("resourcexid"))
    ):
        counts[row["from_resource_id"]] += row["count"]

    incoming = filter_resource_queryset(
        user,
        relations.filter(to_resource_id__in=resource_ids).exclude(
            from_resource_id=F("to_resource_id")
        ),
        resourceinstance_field="from_resource_id",
    )
    for row in (
        incoming.order_by()
        .values("to_resource_id")
        .annotate(count=Count("resourcexid"))
    ):
        counts[row["to_resource_id"]] += row["count"]

    return counts


def _display_name(resource):
    descriptors = resource.descriptors or {}
    name = (descriptors.get(get_language()) or {}).get("name")
    if not name:
        name = next(
            (
                descriptor["name"]
                for descriptor in descriptors.values()
                if descriptor and descriptor.get("name")
            ),
            str(resource.pk),
        )
    return name
