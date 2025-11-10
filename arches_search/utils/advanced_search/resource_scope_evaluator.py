from typing import Any, Dict, Optional
from django.db.models import Q

LOGIC_AND = "AND"
LOGIC_OR = "OR"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"


class ResourceScopeEvaluator:
    def __init__(self, literal_clause_evaluator, related_clause_evaluator) -> None:
        self.literal_clause_evaluator = literal_clause_evaluator
        self.related_clause_evaluator = related_clause_evaluator

    def compose_group_predicate(self, group_payload: Dict[str, Any]) -> Optional[Q]:
        predicate_fragments = []

        for clause_payload in group_payload["clauses"]:
            clause_type = clause_payload["type"]
            if clause_type == CLAUSE_TYPE_LITERAL:
                exists_expr = self.literal_clause_evaluator.evaluate(
                    mode="anchor", clause_payload=clause_payload
                )
            else:
                exists_expr = self.related_clause_evaluator.evaluate(
                    mode="anchor", clause_payload=clause_payload
                )
            predicate_fragments.append(Q(exists_expr))

        for child_group_payload in group_payload["groups"]:
            child_q = self.compose_group_predicate(child_group_payload)
            predicate_fragments.append(child_q)

        initial = Q() if group_payload["logic"] == LOGIC_AND else Q(pk__in=[])
        combined = initial
        for fragment in predicate_fragments:
            combined = (
                (combined & fragment)
                if group_payload["logic"] == LOGIC_AND
                else (combined | fragment)
            )

        return combined
