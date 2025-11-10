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
        def _eval_clause(clause_payload: Dict[str, Any]):
            clause_type = clause_payload["type"].upper()
            if clause_type == CLAUSE_TYPE_LITERAL:
                return self.literal_clause_evaluator.evaluate(
                    mode="anchor", clause_payload=clause_payload
                )
            return self.related_clause_evaluator.presence_for_anchor(clause_payload)

        predicate_fragments = [Q(_eval_clause(c)) for c in group_payload["clauses"]]

        predicate_fragments.extend(
            self.compose_group_predicate(child_group_payload)
            for child_group_payload in group_payload["groups"]
        )

        combined_predicate = (
            Q() if group_payload["logic"].upper() == LOGIC_AND else Q(pk__in=[])
        )

        for predicate_fragment in predicate_fragments:
            combined_predicate = (
                combined_predicate & predicate_fragment
                if group_payload["logic"].upper() == LOGIC_AND
                else combined_predicate | predicate_fragment
            )

        return combined_predicate
