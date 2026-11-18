"""Index a resource's descriptor (display name) into the term index, so resources
are findable by values that only live in the descriptor — e.g. a primary reference
number, which is a ``number`` node indexed into NumericSearch, never TermSearch.

tileid is NOT NULL but a descriptor is per-resource: prefer the descriptor's name
nodegroup tile when configured, else any tile (tileid is only an FK anchor here).
"""
from arches.app.functions.multicard_resource_descriptor import extract_substrings
from arches.app.models.models import FunctionXGraph, Node, TileModel
from arches.app.models.system_settings import settings

from arches_search.models.models import TermSearch

DESCRIPTOR_NODE_ALIAS = "__descriptor__"


def _descriptor_name_config(resource):
    function_x_graph = FunctionXGraph.objects.filter(
        graph_id=resource.graph_id,
        function__functiontype="primarydescriptors",
    ).first()
    if function_x_graph is None:
        return {}
    try:
        return function_x_graph.config["descriptor_types"]["name"]
    except (KeyError, TypeError):
        return {}


def _descriptor_nodegroup_ids(resource, config):
    """The nodegroups the "name" descriptor is built from: the configured one, or
    for a multicard descriptor the nodegroups of the <alias> nodes in its template."""
    if config.get("nodegroup_id"):
        return [config["nodegroup_id"]]
    aliases = extract_substrings(config.get("string_template") or "")
    return list(
        Node.objects.filter(graph_id=resource.graph_id, alias__in=aliases)
        .values_list("nodegroup_id", flat=True)
        .distinct()
    )


def _is_provisional_only(tile):
    has_approved_value = any(value is not None for value in (tile.data or {}).values())
    return not has_approved_value and bool(tile.provisionaledits)


def build_descriptor_terms(resource):
    """Return the TermSearch rows for this resource's descriptor name(s), or []."""
    if str(resource.graph_id) == str(settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID):
        return []
    descriptors = resource.descriptors or {}
    if not descriptors:
        return []
    tiles = TileModel.objects.filter(resourceinstance_id=resource.resourceinstanceid)
    config = _descriptor_name_config(resource)
    nodegroup_ids = _descriptor_nodegroup_ids(resource, config)
    source_tiles = list(
        tiles.filter(nodegroup_id__in=nodegroup_ids).order_by("sortorder")
    )
    tiles_by_nodegroup = {}
    for source_tile in source_tiles:
        tiles_by_nodegroup.setdefault(source_tile.nodegroup_id, source_tile)
    for source_tile in tiles_by_nodegroup.values():
        if _is_provisional_only(source_tile):
            return []
    tile = source_tiles[0] if source_tiles else tiles.order_by("tileid").first()
    if tile is None:
        return []
    template_name = config.get("string_template") or ""
    for placeholder in extract_substrings(template_name):
        template_name = template_name.replace(f"<{placeholder}>", "")
    template_name = template_name.strip()
    graph_slug = resource.graph.slug
    rows = []
    for language, values in descriptors.items():
        name = (values or {}).get("name")
        if not name or name == "Undefined" or name.strip() == template_name:
            continue
        rows.append(
            TermSearch(
                node_alias=DESCRIPTOR_NODE_ALIAS,
                tileid_id=tile.tileid,
                resourceinstanceid_id=resource.resourceinstanceid,
                datatype="string",
                language=language,
                graph_slug=graph_slug,
                value=name,
            )
        )
    return rows


def write_descriptor_search_terms(resource, delete_existing=True):
    """Replace (or, during a fresh reindex, append) this resource's descriptor
    term rows. Idempotent when delete_existing is True."""
    if delete_existing:
        TermSearch.objects.filter(
            resourceinstanceid_id=resource.resourceinstanceid,
            node_alias=DESCRIPTOR_NODE_ALIAS,
        ).delete()
    rows = build_descriptor_terms(resource)
    if rows:
        TermSearch.objects.bulk_create(rows)
    return rows
