import logging
from collections import defaultdict

from django.db.models import Count
from django.utils.translation import get_language
from arches.app.models.models import GraphModel, ResourceInstance, ResourceXResource, Value
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase
from arches_search.models.models import TermSearch

logger = logging.getLogger(__name__)

MAX_SEED_RESOURCES = 100
MAX_GRAPH_NODES = 300


class RelationshipViewerAPI(APIBase):
    def get(self, request):
        resource_ids_param = request.GET.get("resource_ids", "")
        depth = min(int(request.GET.get("depth", 1)), 2)
        rel_type_filter = request.GET.getlist("relationship_types")

        seed_ids = [rid.strip() for rid in resource_ids_param.split(",") if rid.strip()]
        if not seed_ids:
            return JSONResponse({"nodes": [], "edges": [], "relationship_types": []})

        seed_ids = seed_ids[:MAX_SEED_RESOURCES]
        seed_ids_set = set(seed_ids)
        all_ids = set(seed_ids)

        # Expand neighbors up to `depth` hops, skipping non-resource graphs
        frontier = set(seed_ids)
        for _ in range(depth):
            if len(all_ids) >= MAX_GRAPH_NODES:
                break
            neighbor_ids = set()
            from_qs = ResourceXResource.objects.filter(
                from_resource_id__in=frontier
            ).values_list("to_resource_id", flat=True)
            to_qs = ResourceXResource.objects.filter(
                to_resource_id__in=frontier
            ).values_list("from_resource_id", flat=True)
            for rid in list(from_qs) + list(to_qs):
                if rid and str(rid) not in all_ids:
                    neighbor_ids.add(str(rid))
                    all_ids.add(str(rid))
                    if len(all_ids) >= MAX_GRAPH_NODES:
                        break
            frontier = neighbor_ids

        # Remove non-resource instances (e.g. Arches System Settings) from the
        # working set before building edges and nodes.
        valid_ids = set(
            str(rid)
            for rid in ResourceInstance.objects.filter(
                pk__in=all_ids,
                graph__isresource=True,
            ).values_list("resourceinstanceid", flat=True)
        )
        all_ids = valid_ids
        seed_ids_set = seed_ids_set & all_ids

        # Fetch all edges where both endpoints are in the known node set
        edge_qs = ResourceXResource.objects.filter(
            from_resource_id__in=all_ids,
            to_resource_id__in=all_ids,
        ).values(
            "resourcexid",
            "from_resource_id",
            "to_resource_id",
            "relationshiptype",
            "tile_id",
        )

        all_edges = []
        for row in edge_qs:
            rel_type_id = str(row["relationshiptype"]) if row["relationshiptype"] else ""
            if rel_type_filter and rel_type_id not in rel_type_filter:
                continue
            all_edges.append(
                {
                    "id": str(row["resourcexid"]),
                    "source": str(row["from_resource_id"]),
                    "target": str(row["to_resource_id"]),
                    "relationship_type_id": rel_type_id,
                    "tile_id": str(row["tile_id"]) if row["tile_id"] else None,
                }
            )

        # Resolve relationship type labels from concept Values
        rel_type_ids = {e["relationship_type_id"] for e in all_edges if e["relationship_type_id"]}
        rel_type_labels = _resolve_value_labels(rel_type_ids)

        rel_type_counts: dict[str, int] = defaultdict(int)
        for edge in all_edges:
            label = rel_type_labels.get(edge["relationship_type_id"], edge["relationship_type_id"])
            edge["relationship_type_label"] = label
            rel_type_counts[edge["relationship_type_id"]] += 1

        relationship_types = [
            {
                "id": rid,
                "label": rel_type_labels.get(rid, rid),
                "count": count,
            }
            for rid, count in rel_type_counts.items()
        ]

        # Related-resource counts per node (directional: outgoing edges)
        related_counts: dict[str, int] = defaultdict(int)
        for row in (
            ResourceXResource.objects.filter(from_resource_id__in=all_ids)
            .values("from_resource_id")
            .annotate(cnt=Count("resourcexid"))
        ):
            related_counts[str(row["from_resource_id"])] = row["cnt"]

        # Node attributes from arches_search TermSearch (text values only)
        attrs_by_resource = _fetch_term_attributes(all_ids)

        # Build node list from ResourceInstance
        lang = get_language() or "en"
        resources = ResourceInstance.objects.filter(pk__in=all_ids).select_related("graph")

        nodes = []
        for resource in resources:
            rid = str(resource.resourceinstanceid)
            descriptors = resource.descriptors or {}
            name = (
                descriptors.get(lang, {}).get("name")
                or next(
                    (v.get("name") for v in descriptors.values() if v.get("name")),
                    rid,
                )
            )
            graph: GraphModel | None = resource.graph
            nodes.append(
                {
                    "id": rid,
                    "name": name,
                    "graph_id": str(graph.graphid) if graph else None,
                    "graph_slug": graph.slug if graph else None,
                    "graph_name": str(graph.name) if graph else None,
                    "graph_color": graph.color if graph else None,
                    "graph_icon": graph.iconclass if graph else None,
                    "is_seed": rid in seed_ids_set,
                    "related_count": related_counts.get(rid, 0),
                    "attributes": attrs_by_resource.get(rid, []),
                }
            )

        return JSONResponse(
            {
                "nodes": nodes,
                "edges": all_edges,
                "relationship_types": relationship_types,
            }
        )


def _resolve_value_labels(value_ids: set[str]) -> dict[str, str]:
    """Return a valueid → preferred label mapping for a set of concept value IDs."""
    if not value_ids:
        return {}
    lang = get_language() or "en"
    short_lang = lang.split("-")[0]
    labels: dict[str, str] = {}
    for row in Value.objects.filter(
        valueid__in=value_ids, valuetype="prefLabel"
    ).values("valueid", "value", "language_id"):
        vid = str(row["valueid"])
        lang_code = row.get("language_id") or ""
        if vid not in labels:
            labels[vid] = row["value"]
        elif lang_code == lang or lang_code.startswith(short_lang):
            labels[vid] = row["value"]
    return labels


def _fetch_term_attributes(resource_ids: set[str]) -> dict[str, list]:
    """Return a resourceinstanceid → list of {alias, values} dicts from TermSearch."""
    lang = get_language() or "en"
    short_lang = lang.split("-")[0]

    # Prefer matching language; fall back to any language
    rows = TermSearch.objects.filter(
        resourceinstanceid__in=resource_ids,
    ).values("resourceinstanceid", "node_alias", "value", "language")

    # Group by resource → node_alias, picking language-preferred values
    by_resource: dict[str, dict[str, dict[str, set]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(set))
    )
    for row in rows:
        rid = str(row["resourceinstanceid"])
        alias = row["node_alias"]
        lang_code = row["language"] or ""
        by_resource[rid][alias][lang_code].add(row["value"])

    result: dict[str, list] = {}
    for rid, aliases in by_resource.items():
        attrs = []
        for alias, lang_values in aliases.items():
            preferred = (
                lang_values.get(lang)
                or lang_values.get(short_lang)
                or next(iter(lang_values.values()), set())
            )
            if preferred:
                attrs.append({"alias": alias, "values": sorted(preferred)})
        result[rid] = attrs
    return result
