from typing import Any, Callable, Dict, List, Optional, Union

from django.db.models import Exists, OuterRef, Q, QuerySet, F

from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.clause_compiler import ClauseCompiler

from django.utils.translation import gettext as _


class GroupCompiler:
    def __init__(
        self,
        clause_compiler: ClauseCompiler,
        get_graph_id_for_slug: Callable[[str], int],
    ) -> None:
        self.clause_compiler = clause_compiler
        self.get_graph_id_for_slug = get_graph_id_for_slug

    def _does_group_use_resultset(self, group_payload: Dict[str, Any]) -> bool:
        for clause in group_payload.get("clauses", []):
            for operand in clause.get("operands", []) or []:
                if isinstance(operand, dict) and operand.get("type") == "RESULTSET":
                    return True
        return False

    def compile(
        self,
        group_payload: Dict[str, Any],
        parent_graph_slug: Optional[str],
    ) -> Union[Q, Exists]:
        logic = group_payload["logic"]

        if logic not in {"AND", "OR"}:
            raise ValueError(_("Group logic must be either AND or OR."))

        uses_resultset_here = self._does_group_use_resultset(group_payload)

        predicate_path_segments: List[Union[Q, Exists]] = []
        subgroup_ids_queryset: List[QuerySet] = []

        for subgroup_payload in group_payload["groups"]:
            compiled_subgroup = self.compile(
                subgroup_payload,
                parent_graph_slug=group_payload["graph_slug"],
            )
            subgroup_graph_id = self.get_graph_id_for_slug(
                subgroup_payload["graph_slug"]
            )

            subgroup_base_queryset = arches_models.ResourceInstance.objects.filter(
                graph_id=subgroup_graph_id
            ).only("resourceinstanceid")

            filtered_subgroup_queryset = subgroup_base_queryset.annotate(
                anchor_resourceinstanceid=F("resourceinstanceid"),
                parent_resourceinstanceid=OuterRef("resourceinstanceid"),
            ).filter(compiled_subgroup)

            subgroup_ids_queryset.append(
                filtered_subgroup_queryset.values_list("resourceinstanceid", flat=True)
                .order_by()
                .distinct()
            )

            if not uses_resultset_here:
                predicate_path_segments.append(Exists(filtered_subgroup_queryset))

        unioned_subgroup_ids_queryset = None
        if subgroup_ids_queryset:
            unioned_subgroup_queryset = subgroup_ids_queryset[0]
            for next_subgroup_ids_queryset in subgroup_ids_queryset[1:]:
                unioned_subgroup_queryset = unioned_subgroup_queryset.union(
                    next_subgroup_ids_queryset,
                    all=True,
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

        if logic == "AND":
            for next_expression in predicate_path_segments[1:]:
                combined_expression = combined_expression & next_expression
            return combined_expression

        for next_expression in predicate_path_segments[1:]:
            combined_expression = combined_expression | next_expression
        return combined_expression
