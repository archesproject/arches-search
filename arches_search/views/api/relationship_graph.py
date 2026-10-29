import uuid
from collections import defaultdict

from django.conf import settings
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

from arches_search.utils.advanced_search.metadata.resource_names_for_payload import (
    resolve_resource_display_name,
)
from arches_search.utils.readable_nodes import ReadableNodes

OUTGOING = "outgoing"
INCOMING = "incoming"

MAX_SELECTED_RESOURCES = 10
# A resource has a row for each kind of relationship it has, which is a few
# dozen at most; more than this is not a request the panel makes
MAX_ROWS_PER_SELECTION = 500
MAX_GRAPH_NODES = 300
# How far apart two resources may be for a path between them to be found, and
# how many resources the search may visit before it gives up
MAX_PATH_HOPS = 6
MAX_PATH_SEARCH_NODES = 5000

# What a relationship is described by, wherever one is returned
RELATION_FIELDS = (
    "resourcexid",
    "from_resource_id",
    "to_resource_id",
    "relationshiptype",
    "inverserelationshiptype",
    "notes",
)
# Relationships between resources, not between a resource and, say, a setting
BETWEEN_RESOURCES = {
    "from_resource_graph__isresource": True,
    "to_resource_graph__isresource": True,
}


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

        counts = _count_relationships(
            request.user, ReadableNodes(request.user), resource_id
        )

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


def _readable_relations(readable_nodes, *conditions, **filters):
    """The relationships matching the filters that were made through nodes the
    user may read."""
    return readable_nodes.exclude_unreadable_relations(
        ResourceXResource.objects.filter(*conditions, **filters)
    )


def _count_relationships(user, readable_nodes, resource_id):
    """Count relationships by (direction, relationship type id, related graph id)."""
    relations = _readable_relations(readable_nodes)
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
        ],
        "path_relationship_ids": ["<resourcexid>", ...]   (optional)
    }

    A row id is the id the summary endpoint gave the row. The graph holds each
    selected resource, plus the resources on the far end of the relationships
    its selected rows stand for. A resource with no selected rows is still
    drawn, on its own. The relationships of a path, as the path endpoint gave
    them, are always drawn too, with the resources they join, and are flagged
    `on_path`.

    Response shape:
    {
        "nodes": [
            {
                "id": "<uuid>",
                "name": "...",
                "model": {"id", "name", "color", "icon"},
                "is_seed": true,
                "related_count": 12,
                "on_path": false
            },
            ...
        ],
        "edges": [
            {
                "id": "<resourcexid>",
                "source": "<uuid>",
                "target": "<uuid>",
                "relationship_type_id": "...",
                "relationship_type_label": "...",
                "inverse_relationship_type_id": "...",
                "inverse_relationship_type_label": "...",
                "notes": "...",
                "on_path": false
            },
            ...
        ],
        "truncated": false,
        "node_limit": 300
    }

    The inverse relationship type, which names the relationship from the
    target's side, and the notes are empty when none were recorded. The graph
    stops adding resources at the node limit and says so with `truncated`.
    Only readable resources and relationships are included.
    """

    def post(self, request):
        try:
            body = JSONDeserializer().deserialize(request.body)
            selections = _parse_selections(body)
            path_relationship_ids = _parse_path_relationship_ids(body)
        except ValueError:
            return JSONErrorResponse(_("Invalid selection"), status=400)

        seed_ids = [resource_id for resource_id, _rows in selections]
        seeds = ResourceInstance.objects.filter(pk__in=seed_ids, graph__isresource=True)
        if len(seeds) != len(seed_ids) or not all(
            user_can_read_resource(request.user, resource=seed) for seed in seeds
        ):
            return JSONErrorResponse(_("Resource not found"), status=404)

        readable_nodes = ReadableNodes(request.user)
        path_relations = _readable_relations_by_id(
            request.user, readable_nodes, path_relationship_ids
        )
        if len(path_relations) != len(set(path_relationship_ids)):
            return JSONErrorResponse(_("Relationship not found"), status=404)
        path_node_ids = {
            end
            for relation in path_relations.values()
            for end in (relation["from_resource_id"], relation["to_resource_id"])
        }

        relations_by_id = {}
        for resource_id, rows in selections:
            relations_by_id.update(
                _selected_relations(request.user, readable_nodes, resource_id, rows)
            )
        relations_by_id.update(path_relations)

        node_ids = set(seed_ids) | path_node_ids
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
            {
                relationship_type or ""
                for relation in relations
                for relationship_type in (
                    relation["relationshiptype"],
                    relation["inverserelationshiptype"],
                )
            }
        )
        related_counts = _related_counts(request.user, readable_nodes, node_ids)
        resources = ResourceInstance.objects.filter(pk__in=node_ids)
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
                        "on_path": resource.pk in path_node_ids,
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
                        "inverse_relationship_type_id": (
                            relation["inverserelationshiptype"] or ""
                        ),
                        "inverse_relationship_type_label": relationship_type_labels[
                            relation["inverserelationshiptype"] or ""
                        ],
                        "notes": relation["notes"] or "",
                        "on_path": relation["resourcexid"] in path_relations,
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
        if (
            not isinstance(selection, dict)
            or not isinstance(selection.get("row_ids"), list)
            or len(selection["row_ids"]) > MAX_ROWS_PER_SELECTION
        ):
            raise ValueError("selection")
        resource_id = uuid.UUID(str(selection.get("resource_id")))
        parsed[resource_id] = [_parse_row_id(row_id) for row_id in selection["row_ids"]]
    return list(parsed.items())


def _parse_path_relationship_ids(body):
    """The ids of the relationships of a path, or none. Raises ValueError for
    anything that is not a short list of ids."""
    relationship_ids = body.get("path_relationship_ids", [])
    if not isinstance(relationship_ids, list) or len(relationship_ids) > MAX_PATH_HOPS:
        raise ValueError("path_relationship_ids")
    return [uuid.UUID(str(relationship_id)) for relationship_id in relationship_ids]


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
    relationshiptype, inverserelationshiptype, notes}}. Mirrors how the summary groups relationships, so a
    row selects exactly the relationships it counted."""
    outgoing_rows = Q()
    incoming_rows = Q()
    for direction, relationship_type_id, graph_id in rows:
        if direction == OUTGOING:
            outgoing_rows |= _outgoing_row_filter(relationship_type_id, graph_id)
        else:
            incoming_rows |= _incoming_row_filter(relationship_type_id, graph_id)

    relations = _readable_relations(readable_nodes)
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
        for relation in queryset.order_by().values(*RELATION_FIELDS)
    }


def _related_counts(user, readable_nodes, resource_ids):
    """How many readable relationships each resource has, to readable
    resources, in either direction. A relationship to itself counts once."""
    relations = _readable_relations(readable_nodes, **BETWEEN_RESOURCES)
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
    return resolve_resource_display_name(
        resource.descriptors,
        resource.name,
        get_language() or settings.LANGUAGE_CODE,
        settings.LANGUAGE_CODE,
    ) or str(resource.pk)


def _readable_relations_by_id(user, readable_nodes, relationship_ids):
    """The given relationships the user may read, between resources the user
    may read, as {resourcexid: {resourcexid, from_resource_id, to_resource_id,
    relationshiptype, inverserelationshiptype, notes}}."""
    relations = _readable_relations(
        readable_nodes, pk__in=relationship_ids, **BETWEEN_RESOURCES
    )
    for resource_field in ("from_resource_id", "to_resource_id"):
        relations = filter_resource_queryset(
            user, relations, resourceinstance_field=resource_field
        )
    return {
        relation["resourcexid"]: relation
        for relation in relations.order_by().values(*RELATION_FIELDS)
    }


class RelationshipGraphPathAPI(APIBase):
    """How two resources are related: the relationships between them, and the
    shortest chain of relationships that links them, if there is one.

    GET /arches_search/api/relationship-graph/path?from=<uuid>&to=<uuid>

    Response shape:
    {
        "from_resource_id": "<uuid>",
        "to_resource_id": "<uuid>",
        "direct_relationships": [
            {
                "id": "<resourcexid>",
                "direction": "outgoing" | "incoming",
                "relationship_type_id": "...",
                "relationship_type_label": "..."
            },
            ...
        ],
        "hops": 2,
        "relationship_ids": ["<resourcexid>", ...],
        "max_hops": 6,
        "limit_reached": false
    }

    A direct relationship is worded from the `from` resource's side, as a
    summary row is. `hops` is the number of relationships in the shortest
    chain, ignoring which way each points, and `relationship_ids` lists them
    in order from `from` to `to`. Both are empty when no chain of at most
    `max_hops` was found; `limit_reached` says the search gave up on the
    number of resources it had to visit rather than on the distance. Only
    readable resources and relationships are followed.
    """

    def get(self, request):
        try:
            from_id = uuid.UUID(request.GET.get("from", ""))
            to_id = uuid.UUID(request.GET.get("to", ""))
        except (TypeError, ValueError):
            return JSONErrorResponse(_("Invalid resource ID"), status=400)
        if from_id == to_id:
            return JSONErrorResponse(_("Choose two different resources"), status=400)

        resources = ResourceInstance.objects.filter(
            pk__in=(from_id, to_id), graph__isresource=True
        )
        if len(resources) != 2 or not all(
            user_can_read_resource(request.user, resource=resource)
            for resource in resources
        ):
            return JSONErrorResponse(_("Resource not found"), status=404)

        readable_nodes = ReadableNodes(request.user)
        relationship_ids, limit_reached = _shortest_path(
            request.user, readable_nodes, from_id, to_id
        )

        return JSONResponse(
            {
                "from_resource_id": str(from_id),
                "to_resource_id": str(to_id),
                "direct_relationships": _direct_relationships(
                    readable_nodes, from_id, to_id
                ),
                "hops": len(relationship_ids) or None,
                "relationship_ids": [
                    str(relationship_id) for relationship_id in relationship_ids
                ],
                "max_hops": MAX_PATH_HOPS,
                "limit_reached": limit_reached,
            }
        )


def _direct_relationships(readable_nodes, from_id, to_id):
    relations = _readable_relations(
        readable_nodes,
        Q(from_resource_id=from_id, to_resource_id=to_id)
        | Q(from_resource_id=to_id, to_resource_id=from_id),
    )
    rows = list(
        relations.order_by().values(
            "resourcexid",
            "from_resource_id",
            "relationshiptype",
            "inverserelationshiptype",
        )
    )

    direct_relationships = []
    for row in rows:
        is_outgoing = row["from_resource_id"] == from_id
        relationship_type_id = (
            row["relationshiptype"]
            if is_outgoing
            else row["inverserelationshiptype"] or row["relationshiptype"]
        ) or ""
        direct_relationships.append(
            {
                "id": str(row["resourcexid"]),
                "direction": OUTGOING if is_outgoing else INCOMING,
                "relationship_type_id": relationship_type_id,
            }
        )

    labels = _relationship_type_labels(
        {relationship["relationship_type_id"] for relationship in direct_relationships}
    )
    for relationship in direct_relationships:
        relationship["relationship_type_label"] = labels[
            relationship["relationship_type_id"]
        ]
    return sorted(
        direct_relationships,
        key=lambda relationship: (
            relationship["relationship_type_label"].lower(),
            relationship["direction"],
        ),
    )


class _SearchSide:
    """One end of a search for the shortest chain between two resources. It
    knows how far each resource it has reached is from its start, and how it
    got there."""

    def __init__(self, start):
        self.depth = 0
        self.depths = {start: 0}
        self.previous = {}
        self.frontier = {start}

    def expand(self, user, relations, other_depths):
        """Reach every resource one relationship further, in either direction.
        Returns those the other end of the search had already reached."""
        reached = {}
        for near, far in (
            ("from_resource_id", "to_resource_id"),
            ("to_resource_id", "from_resource_id"),
        ):
            rows = filter_resource_queryset(
                user,
                relations.filter(**{f"{near}__in": self.frontier}).exclude(
                    from_resource_id=F("to_resource_id")
                ),
                resourceinstance_field=far,
            )
            for row in rows.order_by().values("resourcexid", near, far):
                if row[far] not in self.depths and row[far] not in reached:
                    reached[row[far]] = (row[near], row["resourcexid"])

        self.depth += 1
        for resource_id, (previous_id, relationship_id) in reached.items():
            self.depths[resource_id] = self.depth
            self.previous[resource_id] = (previous_id, relationship_id)
        self.frontier = set(reached)
        return [resource_id for resource_id in reached if resource_id in other_depths]

    def trace(self, resource_id):
        """The relationships from the start to a resource this side reached,
        in order."""
        relationship_ids = []
        while resource_id in self.previous:
            resource_id, relationship_id = self.previous[resource_id]
            relationship_ids.append(relationship_id)
        return relationship_ids[::-1]


def _shortest_path(user, readable_nodes, from_id, to_id):
    """Search outward from both resources at once, always widening the end
    with fewer resources to look at, until the two meet. Because the ends
    only ever grow by whole steps, the first meeting is the shortest chain.

    Returns the relationships of the chain, in order from `from_id`, and
    whether the search gave up on its size. The chain is empty when none was
    found."""
    relations = _readable_relations(readable_nodes, **BETWEEN_RESOURCES)
    from_side = _SearchSide(from_id)
    to_side = _SearchSide(to_id)

    while from_side.depth + to_side.depth < MAX_PATH_HOPS:
        if len(from_side.frontier) <= len(to_side.frontier):
            side, other = from_side, to_side
        else:
            side, other = to_side, from_side
        if not side.frontier:
            return [], False

        meeting_ids = side.expand(user, relations, other.depths)
        if meeting_ids:
            meeting_id = min(meeting_ids, key=str)
            return (
                from_side.trace(meeting_id) + to_side.trace(meeting_id)[::-1],
                False,
            )
        if len(from_side.depths) + len(to_side.depths) > MAX_PATH_SEARCH_NODES:
            return [], True
    return [], False
