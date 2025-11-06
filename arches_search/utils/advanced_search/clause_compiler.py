# clause_compiler.py
from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from django.db.models import Exists, OuterRef, Q, QuerySet, Subquery
from arches.app.models import models as arches_models


class ClauseCompiler:
    def __init__(self, search_model_registry, facet_registry, path_navigator) -> None:
        self.search_model_registry = search_model_registry
        self.facet_registry = facet_registry
        self.path_navigator = path_navigator

    def compile(
        self,
        clause_payload: Dict[str, Any],
        anchor_graph_slug: str,
        *,
        correlate_to_tile: bool = False,
    ) -> Exists:
        if not clause_payload or not clause_payload.get("subject"):
            return Exists(arches_models.ResourceInstance.objects.none())
        if (clause_payload.get("type") or "").upper() == "RELATED":
            return Exists(arches_models.ResourceInstance.objects.none())

        quantifier = (clause_payload.get("quantifier") or "ANY").upper()
        if quantifier not in ("ANY", "ALL", "NONE"):
            quantifier = "ANY"

        subject_graph_slug, subject_alias = self._unpack_single_path(
            clause_payload["subject"]
        )
        if subject_graph_slug != anchor_graph_slug:
            return Exists(arches_models.ResourceInstance.objects.none())

        subject_rows = self._search_rows(subject_graph_slug, subject_alias)
        if subject_rows is None:
            return Exists(arches_models.ResourceInstance.objects.none())

        datatype_name = self._datatype_for_alias(subject_graph_slug, subject_alias)
        facet = self._facet(datatype_name, clause_payload.get("operator"))
        operands = clause_payload.get("operands") or []

        if correlate_to_tile:
            correlation_filters = {
                "resourceinstanceid": OuterRef("resourceinstance_id"),
                "tileid": OuterRef("tileid"),
            }
        else:
            correlation_filters = {"resourceinstanceid": OuterRef("resourceinstanceid")}

        correlated_rows = subject_rows.filter(**correlation_filters).order_by()

        operator_upper = (clause_payload.get("operator") or "").upper()
        is_orm_template_negated = bool(getattr(facet, "is_orm_template_negated", False))

        if not operands:
            if operator_upper == "HAS_ANY_VALUE":
                if quantifier in ("ANY", "ALL"):
                    return Exists(correlated_rows)
                return ~Exists(correlated_rows)
            if operator_upper == "HAS_NO_VALUE":
                if quantifier in ("NONE", "ALL"):
                    return ~Exists(correlated_rows)
                return Exists(correlated_rows)
            if not is_orm_template_negated:
                if quantifier in ("ANY", "ALL"):
                    return Exists(correlated_rows)
                return ~Exists(correlated_rows)
            else:
                if quantifier in ("ANY", "ALL"):
                    return ~Exists(correlated_rows)
                return Exists(correlated_rows)

        params = self._literal_params(operands)
        raw_predicate = self._predicate_from_facet(
            facet=facet, column_name="value", params=params
        )

        matches = (
            correlated_rows.filter(raw_predicate)
            if isinstance(raw_predicate, Q)
            else correlated_rows.filter(**raw_predicate)
        )

        if not is_orm_template_negated:
            violators = correlated_rows.exclude(pk__in=matches.values("pk"))
        else:
            positive_facet = (
                self.facet_registry.get_positive_facet_for(
                    clause_payload.get("operator"), datatype_name
                )
                if hasattr(self.facet_registry, "get_positive_facet_for")
                else getattr(facet, "positive_counterpart", None)
            )
            if positive_facet is not None:
                pos_pred = self._predicate_from_facet(
                    facet=positive_facet, column_name="value", params=params
                )
                pos_filtered = (
                    correlated_rows.filter(pos_pred)
                    if isinstance(pos_pred, Q)
                    else correlated_rows.filter(**pos_pred)
                )
                violators = pos_filtered
            elif isinstance(raw_predicate, Q) and getattr(
                raw_predicate, "negated", False
            ):
                violators = correlated_rows.filter(~raw_predicate)
            else:
                violators = correlated_rows.exclude(pk__in=matches.values("pk"))

        if quantifier == "ANY":
            return Exists(matches)
        if quantifier == "NONE":
            return ~Exists(matches)
        return Exists(correlated_rows) & ~Exists(violators)

    def related_child_exists_qs(
        self, clause_payload: Dict[str, Any], compiled_pair_info: Dict[str, Any]
    ) -> Optional[QuerySet]:
        subject_graph_slug, subject_alias = self._unpack_single_path(
            clause_payload.get("subject") or []
        )
        if subject_graph_slug != compiled_pair_info["terminal_graph_slug"]:
            return None

        correlated_subject_rows = self._correlated_subject_rows(
            graph_slug=subject_graph_slug,
            node_alias=subject_alias,
            correlate_on_field=compiled_pair_info["child_id_field"],
            anchor_id_field=compiled_pair_info["anchor_id_field"],
        )
        if correlated_subject_rows is None:
            return None

        operator_token = clause_payload.get("operator") or ""
        operands = clause_payload.get("operands") or []
        datatype_name = self._datatype_for_alias(subject_graph_slug, subject_alias)
        facet = self._facet(datatype_name, operator_token)

        if not operands:
            return correlated_subject_rows

        rhs_operand = next(
            (
                operand
                for operand in operands
                if isinstance(operand, dict)
                and (operand.get("type") or "").upper() == "PATH"
                and "value" in operand
            ),
            None,
        )
        if rhs_operand:
            rhs_path: Sequence[Tuple[str, str]] = rhs_operand["value"]
            _rhs_dtype, _rhs_graph, rhs_rows = self.path_navigator.build_path_queryset(
                rhs_path
            )
            rhs_scalar = Subquery(
                rhs_rows.filter(
                    resourceinstanceid=OuterRef("_anchor_resource_id")
                ).values("value")[:1]
            )
            params = [rhs_scalar]
        else:
            params = self._literal_params(operands)

        predicate = self._predicate_from_facet(
            facet=facet, column_name="value", params=params
        )
        return (
            correlated_subject_rows.filter(predicate)
            if isinstance(predicate, Q)
            else correlated_subject_rows.filter(**predicate)
        )

    def _compile_in_graph(
        self,
        clause_payload: Dict[str, Any],
        anchor_graph_slug: str,
        *,
        correlate_to_tile: bool,
    ) -> Exists:
        subject_graph_slug, subject_alias = self._unpack_single_path(
            clause_payload["subject"]
        )
        if subject_graph_slug != anchor_graph_slug:
            return Exists(arches_models.ResourceInstance.objects.none())

        subject_rows = self._search_rows(subject_graph_slug, subject_alias)
        if subject_rows is None:
            return Exists(arches_models.ResourceInstance.objects.none())

        datatype_name = self._datatype_for_alias(subject_graph_slug, subject_alias)
        facet = self._facet(datatype_name, clause_payload.get("operator"))
        operands = clause_payload.get("operands") or []

        if correlate_to_tile:
            correlation_filters: Dict[str, Any] = {
                "resourceinstanceid": OuterRef("resourceinstance_id"),
                "tileid": OuterRef("tileid"),
            }
        else:
            correlation_filters = {"resourceinstanceid": OuterRef("resourceinstanceid")}

        correlated = subject_rows.filter(**correlation_filters)

        if not operands:
            operator_upper = (clause_payload.get("operator") or "").upper()
            if operator_upper == "HAS_NO_VALUE":
                return ~Exists(correlated)
            if operator_upper == "HAS_ANY_VALUE":
                return Exists(correlated)
            is_negated = bool(getattr(facet, "is_orm_template_negated", False))
            return ~Exists(correlated) if is_negated else Exists(correlated)

        predicate = self._predicate_from_facet(
            facet=facet, column_name="value", params=self._literal_params(operands)
        )
        filtered = (
            correlated.filter(predicate)
            if isinstance(predicate, Q)
            else correlated.filter(**predicate)
        )
        return Exists(filtered)

    def _correlated_subject_rows(
        self,
        graph_slug: str,
        node_alias: str,
        correlate_on_field: str,
        anchor_id_field: str,
    ) -> Optional[QuerySet]:
        subject_rows = self._search_rows(graph_slug, node_alias)
        if subject_rows is None:
            return None
        return subject_rows.filter(
            resourceinstanceid=OuterRef(correlate_on_field)
        ).annotate(_anchor_resource_id=OuterRef(anchor_id_field))

    def _facet(self, datatype_name: str, operator_token: Optional[str]):
        return self.facet_registry.get_facet(datatype_name, (operator_token or ""))

    def _literal_params(self, operands: List[Any]) -> List[Any]:
        out: List[Any] = []
        for operand in operands:
            if operand is None:
                continue
            if isinstance(operand, dict):
                t = (operand.get("type") or "").upper()
                if t == "LITERAL" and "value" in operand:
                    out.append(operand["value"])
                elif "value" in operand and t == "":
                    out.append(operand["value"])
            else:
                out.append(operand)
        return out

    def _predicate_from_facet(
        self, *, facet, column_name: str, params: Sequence[Any]
    ) -> Q | Dict[str, Any]:
        lookup_key = (getattr(facet, "orm_template", "") or "").replace(
            "{col}", column_name
        )
        is_orm_template_negated = bool(getattr(facet, "is_orm_template_negated", False))
        value: Any = params[0] if params else True
        kwargs = {lookup_key: value}
        return ~Q(**kwargs) if is_orm_template_negated else kwargs

    def _datatype_for_alias(self, graph_slug: str, node_alias: str) -> str:
        return self.path_navigator.node_alias_datatype_registry.get_datatype_for_alias(
            graph_slug, node_alias
        )

    def _unpack_single_path(
        self, path_value: Iterable[Iterable[str]]
    ) -> Tuple[str, str]:
        try:
            [(graph_slug, node_alias)] = list(path_value)
            return graph_slug, node_alias
        except Exception:
            return "", ""

    def _search_rows(self, graph_slug: str, node_alias: str) -> Optional[QuerySet]:
        model = None
        try:
            model = self.search_model_registry.get_model_for_alias(
                graph_slug, node_alias
            )
        except Exception:
            pass
        if model is None:
            try:
                datatype_name = self._datatype_for_alias(graph_slug, node_alias)
                model = self.search_model_registry.get_model_for_datatype(datatype_name)
            except Exception:
                pass
        if model is None:
            return None
        return model.objects.filter(
            graph_slug=graph_slug, node_alias=node_alias
        ).order_by()
