from typing import Any, Dict, Optional
from django.db.models import Exists, OuterRef, Q
from django.utils.translation import gettext as _

QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

CLAUSE_TYPE_RELATED = "RELATED"


class RelatedClauseEvaluator:
    def __init__(
        self, search_model_registry, facet_registry, path_navigator, predicate_builder
    ) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator
        self.predicate_builder = predicate_builder

    def evaluate(
        self,
        mode: str,
        clause_payload: Dict[str, Any],
        traversal_context: Optional[Dict[str, Any]] = None,
        terminal_datatype_name: Optional[str] = None,
    ):
        if mode == "anchor":
            return self._build_anchor_presence_exists(
                clause_payload, terminal_datatype_name
            )
        if mode == "child":
            if traversal_context is None:
                raise ValueError("traversal_context is required for mode='child'")
            return self._build_child_presence_exists(clause_payload, traversal_context)
        raise ValueError(f"Unsupported evaluation mode: {mode}")

    def _build_anchor_presence_exists(
        self,
        clause_payload: Dict[str, Any],
        terminal_datatype_name: Optional[str],
    ):
        operator_token = clause_payload["operator"]
        quantifier_token = clause_payload["quantifier"]
        subject_path_sequence = clause_payload["subject"]

        traversal_context, child_row_set = self.path_navigator.build_relationship_pairs(
            {"path": subject_path_sequence, "is_inverse": False}
        )

        if terminal_datatype_name is None:
            terminal_datatype_name = (
                self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
                    traversal_context["terminal_graph_slug"],
                    traversal_context["terminal_node_alias"],
                )
            )

        presence_implies_match = self.facet_registry.presence_implies_match(
            terminal_datatype_name, operator_token
        )

        if quantifier_token in (QUANTIFIER_ANY, QUANTIFIER_ALL):
            return (
                Exists(child_row_set)
                if presence_implies_match
                else ~Exists(child_row_set)
            )

        if quantifier_token == QUANTIFIER_NONE:
            return (
                ~Exists(child_row_set)
                if presence_implies_match
                else Exists(child_row_set)
            )

        return Exists(child_row_set.none())

    def _build_child_presence_exists(
        self, clause_payload: Dict[str, Any], traversal_context: Dict[str, Any]
    ):
        subject_graph_slug, subject_node_alias = clause_payload["subject"][0]
        operator_token = clause_payload["operator"]
        operand_items = clause_payload["operands"]

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
            resourceinstanceid=OuterRef(traversal_context["child_id_field"])
        ).annotate(_anchor_resource_id=OuterRef(traversal_context["anchor_id_field"]))

        if not operand_items:
            presence_implies_match = self.facet_registry.presence_implies_match(
                datatype_name, operator_token
            )
            return (
                Exists(correlated_subject_rows)
                if presence_implies_match
                else ~Exists(correlated_subject_rows)
            )

        predicate_expression, _ = self.predicate_builder.build_predicate(
            datatype_name=datatype_name,
            operator_token=operator_token,
            operands=operand_items,
            anchor_resource_id_annotation="_anchor_resource_id",
        )

        if isinstance(predicate_expression, Q):
            return Exists(correlated_subject_rows.filter(predicate_expression))
        return Exists(correlated_subject_rows.filter(**predicate_expression))
