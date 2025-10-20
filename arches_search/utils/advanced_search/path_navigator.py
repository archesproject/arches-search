from typing import Any, Sequence, Tuple

from django.db.models import OuterRef, QuerySet, Subquery

from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.advanced_search.node_alias_datatype_registry import (
    NodeAliasDatatypeRegistry,
)

from django.utils.translation import gettext as _


class PathNavigator:
    def __init__(
        self,
        search_model_registry: SearchModelRegistry,
        node_alias_datatype_registry: NodeAliasDatatypeRegistry,
    ) -> None:
        self.search_model_registry = search_model_registry
        self.node_alias_datatype_registry = node_alias_datatype_registry

    def _build_resource_instance_ids_subquery(
        self,
        outer_resource_instance_id_reference: str,
        starting_graph_slug: str,
        path_segments: Sequence[str],
    ) -> Subquery:
        if not path_segments:
            base_queryset = (
                arches_models.ResourceInstance.objects.only("resourceinstanceid")
                .filter(
                    resourceinstanceid=OuterRef(outer_resource_instance_id_reference)
                )
                .values_list("resourceinstanceid", flat=True)[:1]
            )
            return Subquery(base_queryset)

        first_graph_slug, first_node_alias = path_segments[0].split(":")
        first_datatype_name = self.node_alias_datatype_registry.lookup_node_datatype(
            first_graph_slug, first_node_alias
        )
        first_model = self.search_model_registry.get_model_for_datatype(
            first_datatype_name
        )

        if self.search_model_registry.is_relationship_datatype(first_datatype_name):
            if first_graph_slug == starting_graph_slug:
                first_owner_ids_queryset = (
                    first_model.objects.only(
                        "graph_slug", "node_alias", "resourceinstanceid", "value"
                    )
                    .filter(
                        graph_slug=first_graph_slug,
                        node_alias=first_node_alias,
                        resourceinstanceid=OuterRef(
                            outer_resource_instance_id_reference
                        ),
                    )
                    .values_list("value", flat=True)
                )
            else:
                first_owner_ids_queryset = (
                    first_model.objects.only(
                        "graph_slug", "node_alias", "resourceinstanceid", "value"
                    )
                    .filter(
                        graph_slug=first_graph_slug,
                        node_alias=first_node_alias,
                        value=OuterRef(outer_resource_instance_id_reference),
                    )
                    .values_list("resourceinstanceid", flat=True)
                )
        else:
            first_owner_ids_queryset = (
                arches_models.ResourceInstance.objects.only("resourceinstanceid")
                .filter(
                    resourceinstanceid=OuterRef(outer_resource_instance_id_reference)
                )
                .values_list("resourceinstanceid", flat=True)[:1]
            )

        accumulated_owner_ids: Subquery = Subquery(first_owner_ids_queryset)

        for hop_segment in path_segments[1:-1]:
            hop_graph_slug, hop_node_alias = hop_segment.split(":")
            hop_datatype_name = self.node_alias_datatype_registry.lookup_node_datatype(
                hop_graph_slug, hop_node_alias
            )

            if not self.search_model_registry.is_relationship_datatype(
                hop_datatype_name
            ):
                raise ValueError(
                    _("Intermediate path segments must be of relationship datatype.")
                )

            hop_model = self.search_model_registry.get_model_for_datatype(
                hop_datatype_name
            )
            hop_queryset = (
                hop_model.objects.only(
                    "graph_slug", "node_alias", "resourceinstanceid", "value"
                )
                .filter(
                    graph_slug=hop_graph_slug,
                    node_alias=hop_node_alias,
                    resourceinstanceid__in=accumulated_owner_ids,
                )
                .values_list("value", flat=True)
            )
            accumulated_owner_ids = Subquery(hop_queryset)

        return accumulated_owner_ids

    def build_values_subquery(
        self,
        outer_resource_instance_id_reference: str,
        starting_graph_slug: str,
        path_segments: Sequence[str],
    ) -> Subquery:
        if not path_segments:
            base_queryset = (
                arches_models.ResourceInstance.objects.only("resourceinstanceid")
                .filter(
                    resourceinstanceid=OuterRef(outer_resource_instance_id_reference)
                )
                .values_list("resourceinstanceid", flat=True)
            )
            return Subquery(base_queryset)

        last_graph_slug, last_node_alias = path_segments[-1].split(":")
        last_datatype_name = self.node_alias_datatype_registry.lookup_node_datatype(
            last_graph_slug, last_node_alias
        )
        last_model = self.search_model_registry.get_model_for_datatype(
            last_datatype_name
        )

        if len(path_segments) == 1:
            single_segment_queryset = (
                last_model.objects.only(
                    "graph_slug", "node_alias", "resourceinstanceid", "value"
                )
                .filter(
                    graph_slug=last_graph_slug,
                    node_alias=last_node_alias,
                    resourceinstanceid=OuterRef(outer_resource_instance_id_reference),
                )
                .values_list("value", flat=True)
            )
            return Subquery(single_segment_queryset)

        accumulated_owner_ids = self._build_resource_instance_ids_subquery(
            outer_resource_instance_id_reference, starting_graph_slug, path_segments
        )

        final_values_queryset = (
            last_model.objects.only(
                "graph_slug", "node_alias", "resourceinstanceid", "value"
            )
            .annotate(
                **{
                    outer_resource_instance_id_reference: OuterRef(
                        outer_resource_instance_id_reference
                    )
                }
            )
            .filter(
                graph_slug=last_graph_slug,
                node_alias=last_node_alias,
                resourceinstanceid__in=accumulated_owner_ids,
            )
            .values_list("value", flat=True)
        )
        return Subquery(final_values_queryset)

    def build_path_queryset(
        self,
        path_segments: Sequence[str],
        context_graph_slug: str,
    ) -> Tuple[str, Any, QuerySet]:
        if not path_segments:
            raise ValueError(_("Path must not be empty."))

        last_graph_slug, last_node_alias = path_segments[-1].split(":")
        last_datatype_name = self.node_alias_datatype_registry.lookup_node_datatype(
            last_graph_slug, last_node_alias
        )
        last_model = self.search_model_registry.get_model_for_datatype(
            last_datatype_name
        )

        if len(path_segments) == 1:
            if last_graph_slug == context_graph_slug:
                queryset = last_model.objects.only(
                    "graph_slug", "node_alias", "resourceinstanceid", "value"
                ).filter(
                    graph_slug=last_graph_slug,
                    node_alias=last_node_alias,
                    resourceinstanceid=OuterRef("resourceinstanceid"),
                )
            else:
                queryset = last_model.objects.only(
                    "graph_slug", "node_alias", "resourceinstanceid", "value"
                ).filter(
                    graph_slug=last_graph_slug,
                    node_alias=last_node_alias,
                    value=OuterRef("resourceinstanceid"),
                )
            return last_datatype_name, last_model, queryset

        accumulated_owner_ids = self._build_resource_instance_ids_subquery(
            outer_resource_instance_id_reference="anchor_resourceinstanceid",
            starting_graph_slug=context_graph_slug,
            path_segments=path_segments,
        )
        queryset = (
            last_model.objects.only("value")
            .annotate(**{"anchor_resourceinstanceid": OuterRef("resourceinstanceid")})
            .filter(
                graph_slug=last_graph_slug,
                node_alias=last_node_alias,
                resourceinstanceid__in=accumulated_owner_ids,
            )
        )
        return last_datatype_name, last_model, queryset
