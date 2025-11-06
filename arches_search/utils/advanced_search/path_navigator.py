from __future__ import annotations
from typing import Tuple, Sequence, Dict, Any, Optional, List

from django.db.models import QuerySet, OuterRef, Exists, Q
from django.utils.translation import gettext as _
from arches_search.utils.advanced_search.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.advanced_search.node_alias_datatype_registry import (
    NodeAliasDatatypeRegistry,
)


class PathNavigator:
    def __init__(
        self,
        search_model_registry: SearchModelRegistry,
        node_alias_datatype_registry: NodeAliasDatatypeRegistry,
    ) -> None:
        self.search_model_registry = search_model_registry
        self.node_alias_datatype_registry = node_alias_datatype_registry

    def build_path_queryset(
        self,
        path_segments: Sequence[Tuple[str, str]] | None = None,
    ) -> Tuple[str, str, QuerySet]:
        if not path_segments:
            raise ValueError(_("path must contain at least one segment"))

        terminal_graph_slug, terminal_node_alias = path_segments[-1]
        terminal_datatype_name = (
            self.node_alias_datatype_registry.get_datatype_for_alias(
                terminal_graph_slug, terminal_node_alias
            )
        )
        terminal_search_model = self.search_model_registry.get_model_for_datatype(
            terminal_datatype_name
        )
        terminal_queryset = terminal_search_model.objects.filter(
            graph_slug=terminal_graph_slug, node_alias=terminal_node_alias
        ).order_by()
        return terminal_datatype_name, terminal_graph_slug, terminal_queryset

    def build_relationship_pairs(
        self,
        relationship_context: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], QuerySet]:
        relationship_path = relationship_context["path"]
        is_inverse_relationship: bool = relationship_context["is_inverse"]

        terminal_datatype_name, terminal_graph_slug, base_pair_rows = (
            self.build_path_queryset(relationship_path)
        )
        if terminal_datatype_name.lower() not in {
            "resource-instance",
            "resource-instance-list",
        }:
            raise ValueError(
                _(
                    "Relationship must end on a resource-instance or resource-instance-list node"
                )
            )

        if is_inverse_relationship:
            pairs_scoped_to_anchor = base_pair_rows.filter(
                value=OuterRef("resourceinstanceid")
            )
            anchor_id_field = "value"
            child_id_field = "resourceinstanceid"
        else:
            pairs_scoped_to_anchor = base_pair_rows.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            )
            anchor_id_field = "resourceinstanceid"
            child_id_field = "value"

        compiled_pair_info = {
            "pair_queryset": base_pair_rows,
            "anchor_id_field": anchor_id_field,
            "child_id_field": child_id_field,
            "terminal_graph_slug": terminal_graph_slug,
            "terminal_node_alias": relationship_path[-1][1],
            "is_inverse": is_inverse_relationship,
        }
        return compiled_pair_info, pairs_scoped_to_anchor

    def build_scoped_pairs_for_path(
        self,
        path_segments: Sequence[Tuple[str, str]],
        is_inverse_relationship: bool,
        correlate_on_field: str,
    ) -> Tuple[str, str, QuerySet, str]:
        terminal_datatype_name, terminal_graph_slug, base_pair_rows = (
            self.build_path_queryset(path_segments)
        )
        if terminal_datatype_name.lower() not in {
            "resource-instance",
            "resource-instance-list",
        }:
            raise ValueError(
                _(
                    "Nested relationship must end on a resource-instance or resource-instance-list node"
                )
            )

        if is_inverse_relationship:
            scoped_pairs = base_pair_rows.filter(value=OuterRef(correlate_on_field))
            nested_child_id_field = "resourceinstanceid"
        else:
            scoped_pairs = base_pair_rows.filter(
                resourceinstanceid=OuterRef(correlate_on_field)
            )
            nested_child_id_field = "value"

        return (
            terminal_datatype_name,
            terminal_graph_slug,
            scoped_pairs,
            nested_child_id_field,
        )

    def normalize_relationship_context(
        self, relationship_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        is_inverse = bool(relationship_context.get("is_inverse"))
        path_segments = relationship_context.get("path") or []
        raw_quantifiers = relationship_context.get("traversal_quantifiers") or ["ANY"]
        hop_quantifier = (raw_quantifiers[0] or "ANY").upper()
        return {
            "is_inverse": is_inverse,
            "path_segments": path_segments,
            "hop_quantifier": hop_quantifier,
        }

    def child_ok_rows_from_literals(
        self, group_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ) -> Optional[QuerySet]:
        terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]
        child_id_field = compiled_pair_info["child_id_field"]

        literal_clauses: List[Dict[str, Any]] = []
        for child_group_payload in group_payload.get("groups") or []:
            if (child_group_payload.get("relationship") or {}).get("path"):
                continue
            if (child_group_payload.get("logic") or "AND").upper() != "AND":
                return None

            child_group_graph_slug = (
                child_group_payload.get("graph_slug") or ""
            ).strip()
            stack: List[Dict[str, Any]] = [child_group_payload]
            while stack:
                node_payload = stack.pop()
                if (node_payload.get("relationship") or {}).get("path"):
                    continue
                for clause_payload in node_payload.get("clauses") or []:
                    if (clause_payload.get("type") or "").upper() != "LITERAL":
                        continue
                    subject_path = clause_payload.get("subject") or []
                    subject_graph_slug, subject_alias = (
                        subject_path[0] if subject_path else ("", "")
                    )
                    if not subject_graph_slug or (
                        child_group_graph_slug
                        and subject_graph_slug != child_group_graph_slug
                    ):
                        continue
                    if subject_graph_slug != terminal_graph_slug:
                        return None
                    literal_clauses.append(clause_payload)
                for nested_group_payload in node_payload.get("groups") or []:
                    stack.append(nested_group_payload)

        if not literal_clauses:
            return None

        from arches_search.utils.advanced_search.clause_compiler import (
            ClauseCompiler,
        )  # local import to avoid cycle on type hints

        clause_compiler: ClauseCompiler = getattr(
            self, "_clause_compiler_for_fastpath", None
        )  # optional backreference
        if clause_compiler is None:
            return None

        child_ok_rows: Optional[QuerySet] = None
        for clause_payload in literal_clauses:
            subject_path = clause_payload.get("subject") or []
            subject_graph_slug, subject_alias = (
                subject_path[0] if subject_path else ("", "")
            )
            subject_rows = clause_compiler.rows_for(subject_graph_slug, subject_alias)
            if subject_rows is None:
                continue

            datatype_name = self.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_alias
            )
            facet_registry = clause_compiler.facet_registry
            operand_items = clause_payload.get("operands") or []

            correlated = subject_rows.filter(
                resourceinstanceid=OuterRef(child_id_field)
            ).order_by()

            if not operand_items:
                facet = facet_registry.get_facet(
                    datatype_name, clause_payload.get("operator")
                )
                operator_upper = (clause_payload.get("operator") or "").upper()
                is_negated_template = bool(
                    getattr(facet, "is_orm_template_negated", False)
                )
                if operator_upper == "HAS_NO_VALUE":
                    predicate_queryset = correlated.none()
                elif operator_upper == "HAS_ANY_VALUE":
                    predicate_queryset = correlated
                else:
                    predicate_queryset = (
                        correlated.none() if is_negated_template else correlated
                    )
            else:
                params = clause_compiler._literal_params(operand_items)
                predicate_expr, is_negated_template = facet_registry.predicate(
                    datatype_name, clause_payload.get("operator"), "value", params
                )
                filtered = (
                    correlated.filter(predicate_expr)
                    if isinstance(predicate_expr, Q)
                    else correlated.filter(**predicate_expr)
                )
                if not is_negated_template:
                    predicate_queryset = filtered
                else:
                    positive_facet = facet_registry.get_positive_facet_for(
                        clause_payload.get("operator"), datatype_name
                    )
                    if positive_facet is not None:
                        positive_expr, _ = facet_registry.predicate(
                            datatype_name, positive_facet.operator, "value", params
                        )
                        positive_filtered = (
                            correlated.filter(positive_expr)
                            if isinstance(positive_expr, Q)
                            else correlated.filter(**positive_expr)
                        )
                        predicate_queryset = correlated.exclude(
                            pk__in=positive_filtered.values("pk")
                        )
                    elif isinstance(predicate_expr, Q) and getattr(
                        predicate_expr, "negated", False
                    ):
                        predicate_queryset = correlated.exclude(
                            pk__in=correlated.filter(~predicate_expr).values("pk")
                        )
                    else:
                        predicate_queryset = correlated.exclude(
                            pk__in=filtered.values("pk")
                        )

            child_ok_rows = (
                predicate_queryset
                if child_ok_rows is None
                else child_ok_rows.filter(pk__in=predicate_queryset.values("pk"))
            )

        return child_ok_rows

    def attach_clause_compiler_for_fastpath(self, clause_compiler) -> None:
        self._clause_compiler_for_fastpath = clause_compiler
