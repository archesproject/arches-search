from typing import Any, Dict, List, Optional, Union

from django.db.models import Exists, OuterRef, Q, QuerySet

from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.clause_compiler import ClauseCompiler

from django.utils.translation import gettext as _


class GroupCompiler:
    def __init__(self, clause_compiler: ClauseCompiler) -> None:
        self.clause_compiler = clause_compiler

    def compile(
        self,
        group_payload: Dict[str, Any],
        parent_graph_slug: Optional[str],
    ) -> Union[Q, Exists]:
        if group_payload["logic"] not in {"AND", "OR"}:
            raise ValueError(_("Group logic must be either AND or OR."))

        predicate_path_segments: List[Union[Q, Exists]] = []
        subgroup_ids_queryset: List[QuerySet] = []

        for subgroup_payload in group_payload["groups"]:
            compiled_subgroup = self.compile(
                subgroup_payload,
                parent_graph_slug=group_payload["graph_slug"],
            )

            subgroup_base_queryset = arches_models.ResourceInstance.objects.filter(
                graph__slug=subgroup_payload["graph_slug"]
            ).only("resourceinstanceid")

            filtered_subgroup_queryset = subgroup_base_queryset.annotate(
                parent_resourceinstanceid=OuterRef("resourceinstanceid")
            ).filter(compiled_subgroup)

            subgroup_ids_queryset.append(
                filtered_subgroup_queryset.values_list("resourceinstanceid", flat=True)
            )

            predicate_path_segments.append(Exists(filtered_subgroup_queryset))

        unioned_subgroup_ids_queryset = None
        if subgroup_ids_queryset:
            unioned_subgroup_queryset = subgroup_ids_queryset[0]

            for next_subgroup_ids_queryset in subgroup_ids_queryset[1:]:
                unioned_subgroup_queryset = unioned_subgroup_queryset.union(
                    next_subgroup_ids_queryset
                )

            unioned_subgroup_ids_queryset = unioned_subgroup_queryset

        for clause_payload in group_payload["clauses"]:
            compiled_clause = self.clause_compiler.compile(
                clause_payload=clause_payload,
                anchor_graph_slug=group_payload["graph_slug"],
                parent_graph_slug=parent_graph_slug,
                unioned_subgroup_ids_queryset=unioned_subgroup_ids_queryset,
            )
            predicate_path_segments.append(compiled_clause)

        if not predicate_path_segments:
            return Q()

        combined_expression: Union[Q, Exists] = predicate_path_segments[0]
        if group_payload["logic"] == "AND":
            for next_expression in predicate_path_segments[1:]:
                combined_expression = combined_expression & next_expression
            return combined_expression

        for next_expression in predicate_path_segments[1:]:
            combined_expression = combined_expression | next_expression
        return combined_expression
