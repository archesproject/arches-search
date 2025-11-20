from typing import Any, Dict, Tuple, Set

from django.conf import settings
from django.utils.translation import get_language
from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.node_alias_datatype_registry import (
    NodeAliasDatatypeRegistry,
)


def build_node_alias_metadata_for_payload_query(
    group_payload: Dict[str, Any],
) -> Dict[Tuple[str, str], Dict[str, str]]:
    language_code = get_language() or settings.LANGUAGE_CODE
    default_language_code = settings.LANGUAGE_CODE

    node_alias_datatype_registry = NodeAliasDatatypeRegistry(group_payload)
    datatype_cache_by_graph = node_alias_datatype_registry.datatype_cache_by_graph

    required_aliases_by_graph: Dict[str, Set[str]] = {
        graph_slug: set(alias_to_datatype_map.keys())
        for graph_slug, alias_to_datatype_map in datatype_cache_by_graph.items()
    }

    graph_slugs = list(required_aliases_by_graph.keys())
    all_required_aliases: Set[str] = set().union(*required_aliases_by_graph.values())

    widget_rows = arches_models.CardXNodeXWidget.objects.filter(
        node__graph__slug__in=graph_slugs,
        node__alias__in=all_required_aliases,
    ).values("node__graph__slug", "node__alias", "config")

    label_by_graph_and_alias: Dict[Tuple[str, str], str] = {}

    for widget_row in widget_rows.iterator():
        graph_slug = widget_row["node__graph__slug"]
        node_alias = widget_row["node__alias"]
        widget_config = widget_row["config"]
        raw_label_value = widget_config.get("label", "")

        if isinstance(raw_label_value, dict):
            label_text = str(
                raw_label_value.get(
                    language_code,
                    raw_label_value.get(
                        default_language_code,
                        next(iter(raw_label_value.values()), ""),
                    ),
                )
            )
        else:
            label_text = str(raw_label_value)

        label_by_graph_and_alias[(graph_slug, node_alias)] = label_text

    node_metadata_by_graph_and_alias: Dict[Tuple[str, str], Dict[str, str]] = {}

    for graph_slug, alias_set in required_aliases_by_graph.items():
        for node_alias in alias_set:
            node_metadata_by_graph_and_alias[(graph_slug, node_alias)] = {
                "datatype": node_alias_datatype_registry.get_datatype_for_alias(
                    graph_slug,
                    node_alias,
                ),
                "card_x_node_x_widget_label": label_by_graph_and_alias.get(
                    (graph_slug, node_alias), ""
                ),
            }

    return node_metadata_by_graph_and_alias
