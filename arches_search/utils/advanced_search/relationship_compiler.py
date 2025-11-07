from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet

CLAUSE_TYPE_LITERAL = "LITERAL"

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"


class RelationshipCompiler:
    def __init__(
        self, search_model_registry, facet_registry, path_navigator, operand_compiler
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.operand_compiler = operand_compiler

    def related_presence_exists(self, clause_payload: Dict[str, Any]) -> Exists:
        operator_token = (clause_payload["operator"] or "").upper()
        quantifier_token = (clause_payload["quantifier"] or "").upper()
        subject_path_sequence = clause_payload["subject"]

        compiled_pair_info, pairs_scoped_to_anchor_resource = (
            self.path_navigator.build_relationship_pairs(
                {"path": subject_path_sequence, "is_inverse": False}
            )
        )
        correlated_pairs = pairs_scoped_to_anchor_resource

        terminal_graph_slug = compiled_pair_info["terminal_graph_slug"]
        terminal_node_alias = compiled_pair_info["terminal_node_alias"]
        terminal_datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                terminal_graph_slug, terminal_node_alias
            )
        )

        presence_means_match = self._presence_means_match_for_zero_operands(
            terminal_datatype_name, operator_token
        )

        if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
            return (
                Exists(correlated_pairs)
                if presence_means_match
                else ~Exists(correlated_pairs)
            )
        if quantifier_token == QUANTIFIER_NONE:
            return (
                ~Exists(correlated_pairs)
                if presence_means_match
                else Exists(correlated_pairs)
            )
        return Exists(
            self.search_model_registry.get_model_for_datatype(
                terminal_datatype_name
            ).objects.none()
        )

    def filter_pairs_by_clause(
        self,
        pairs_queryset: QuerySet,
        clause_payload: Dict[str, Any],
        correlate_field: str,
    ) -> Tuple[QuerySet, bool]:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload["operator"] or "").upper()
        operand_items = clause_payload.get("operands") or []

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)
        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug, node_alias=subject_node_alias
        )
        correlated_rows = subject_rows.filter(
            resourceinstanceid=OuterRef(correlate_field)
        )

        if not operand_items:
            presence_means_match = self._presence_means_match_for_zero_operands(
                datatype_name, operator_token
            )
            return (
                (pairs_queryset.filter(Exists(correlated_rows)), True)
                if presence_means_match
                else (pairs_queryset.filter(~Exists(correlated_rows)), True)
            )

        predicate_expression, is_template_negated = (
            self.operand_compiler.build_predicate(
                datatype_name=datatype_name,
                operator_token=operator_token,
                operands=operand_items,
                anchor_resource_id_annotation=None,
            )
        )

        if not is_template_negated:
            if isinstance(predicate_expression, Q):
                return (
                    pairs_queryset.filter(
                        Exists(correlated_rows.filter(predicate_expression))
                    ),
                    True,
                )
            return (
                pairs_queryset.filter(
                    Exists(correlated_rows.filter(**predicate_expression))
                ),
                True,
            )

        positive_facet = self.facet_registry.get_positive_facet_for(
            operator_token, datatype_name
        )
        if positive_facet is not None:
            positive_expression, _ = self.facet_registry.predicate(
                datatype_name,
                positive_facet.operator,
                "value",
                self.operand_compiler.literal_values_only(operand_items),
            )
            if isinstance(positive_expression, Q):
                return (
                    pairs_queryset.filter(
                        ~Exists(correlated_rows.filter(positive_expression))
                    ),
                    True,
                )
            return (
                pairs_queryset.filter(
                    ~Exists(correlated_rows.filter(**positive_expression))
                ),
                True,
            )

        if isinstance(predicate_expression, Q) and getattr(
            predicate_expression, "negated", False
        ):
            return (
                pairs_queryset.filter(
                    ~Exists(correlated_rows.filter(~predicate_expression))
                ),
                True,
            )

        if isinstance(predicate_expression, Q):
            return (
                pairs_queryset.filter(
                    ~Exists(correlated_rows.filter(predicate_expression))
                ),
                True,
            )
        return (
            pairs_queryset.filter(
                ~Exists(correlated_rows.filter(**predicate_expression))
            ),
            True,
        )

    def related_child_exists_qs(
        self, clause_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ) -> Optional[QuerySet]:
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = (clause_payload["operator"] or "").upper()
        operand_items = clause_payload.get("operands") or []

        datatype_name = (
            self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                subject_graph_slug, subject_node_alias
            )
        )
        model_class = self.search_model_registry.get_model_for_datatype(datatype_name)
        subject_rows = model_class.objects.filter(
            graph_slug=subject_graph_slug, node_alias=subject_node_alias
        )

        correlated_subject_rows = subject_rows.filter(
            resourceinstanceid=OuterRef(compiled_pair_info["child_id_field"])
        ).annotate(_anchor_resource_id=OuterRef(compiled_pair_info["anchor_id_field"]))

        if not operand_items:
            return correlated_subject_rows

        predicate_expression, _ = self.operand_compiler.build_predicate(
            datatype_name=datatype_name,
            operator_token=operator_token,
            operands=operand_items,
            anchor_resource_id_annotation="_anchor_resource_id",
        )

        if isinstance(predicate_expression, Q):
            return correlated_subject_rows.filter(predicate_expression)
        return correlated_subject_rows.filter(**predicate_expression)

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

            pending_nodes: List[Dict[str, Any]] = [child_group_payload]
            while pending_nodes:
                node_payload = pending_nodes.pop()
                if (node_payload.get("relationship") or {}).get("path"):
                    continue

                for clause_payload in node_payload.get("clauses") or []:
                    if (
                        clause_payload.get("type") or ""
                    ).upper() != CLAUSE_TYPE_LITERAL:
                        continue
                    subject_graph_slug, _ = clause_payload["subject"][0]
                    if subject_graph_slug != terminal_graph_slug:
                        return None
                    literal_clauses.append(clause_payload)

                for nested in node_payload.get("groups") or []:
                    pending_nodes.append(nested)

        if not literal_clauses:
            return None

        accumulated_rows: Optional[QuerySet] = None

        for clause_payload in literal_clauses:
            subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
            operator_token = (clause_payload["operator"] or "").upper()
            operand_items = clause_payload.get("operands") or []

            datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    subject_graph_slug, subject_node_alias
                )
            )
            model_class = self.search_model_registry.get_model_for_datatype(
                datatype_name
            )
            subject_rows = model_class.objects.filter(
                graph_slug=subject_graph_slug, node_alias=subject_node_alias
            )
            correlated_rows = subject_rows.filter(
                resourceinstanceid=OuterRef(child_id_field)
            )

            if not operand_items:
                presence_means_match = self._presence_means_match_for_zero_operands(
                    datatype_name, operator_token
                )
                predicate_rows = (
                    correlated_rows if presence_means_match else correlated_rows.none()
                )
            else:
                predicate_expression, is_template_negated = (
                    self.operand_compiler.build_predicate(
                        datatype_name=datatype_name,
                        operator_token=operator_token,
                        operands=operand_items,
                        anchor_resource_id_annotation=None,
                    )
                )
                filtered_rows = (
                    correlated_rows.filter(predicate_expression)
                    if isinstance(predicate_expression, Q)
                    else correlated_rows.filter(**predicate_expression)
                )
                if not is_template_negated:
                    predicate_rows = filtered_rows
                else:
                    positive_facet = self.facet_registry.get_positive_facet_for(
                        operator_token, datatype_name
                    )
                    if positive_facet is not None:
                        positive_expression, _ = self.facet_registry.predicate(
                            datatype_name,
                            positive_facet.operator,
                            "value",
                            self.operand_compiler.literal_values_only(operand_items),
                        )
                        predicate_rows = (
                            correlated_rows.exclude(positive_expression)
                            if isinstance(positive_expression, Q)
                            else correlated_rows.exclude(**positive_expression)
                        )
                    elif isinstance(predicate_expression, Q) and getattr(
                        predicate_expression, "negated", False
                    ):
                        predicate_rows = correlated_rows.exclude(~predicate_expression)
                    else:
                        predicate_rows = (
                            correlated_rows.exclude(predicate_expression)
                            if isinstance(predicate_expression, Q)
                            else correlated_rows.exclude(**predicate_expression)
                        )

            if accumulated_rows is None:
                accumulated_rows = predicate_rows
            else:
                accumulated_rows = accumulated_rows.filter(
                    pk__in=predicate_rows.values("pk")
                )

        return accumulated_rows

    def _presence_means_match_for_zero_operands(
        self, datatype_name: str, operator_token: str
    ) -> bool:
        facet = self.facet_registry.get_facet(datatype_name, operator_token)
        accepts_no_operands = not bool(getattr(facet, "operand_types", None))
        if not accepts_no_operands:
            return False
        return bool(getattr(facet, "is_orm_template_negated", False))
