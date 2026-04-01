from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.db.models import Q, QuerySet


@dataclass(frozen=True, slots=True)
class AggregatePredicateSpec:
    kind: str
    field_name: str | None = None
    values: tuple[Any, ...] = ()
    lookup: str | None = None


@dataclass(frozen=True, slots=True)
class TileScopePredicateSet:
    per_tile: Optional[Q]
    resource_level: Optional[Q]


@dataclass(frozen=True, slots=True)
class CorrelatedLiteralClauseContext:
    datatype_name: str
    correlated_rows: QuerySet
    normalized_operand_items: List[Dict[str, Any]]
    predicate_expression: Any
    is_template_negated: bool


@dataclass(frozen=True, slots=True)
class ClauseReductionResult:
    relationshipless_q: Optional[Q]
    constrained_child_rows: Optional[QuerySet]
    had_inner_filters: bool
