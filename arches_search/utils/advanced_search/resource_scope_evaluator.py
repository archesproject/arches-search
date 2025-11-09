from typing import Any, Dict, Optional
from django.db.models import Q

LOGIC_AND = "AND"
LOGIC_OR = "OR"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"


class ResourceScopeEvaluator:
    def __init__(self, *, literal_evaluator, related_evaluator) -> None:
        self.literal_evaluator = literal_evaluator
        self.related_evaluator = related_evaluator

    def compose_group_predicate(self, group_payload: Dict[str, Any]) -> Optional[Q]:
        use_and_logic = group_payload["logic"].upper() == LOGIC_AND

        evaluator_for_clause_type = {
            CLAUSE_TYPE_LITERAL: self.literal_evaluator.exists_for_anchor,
            CLAUSE_TYPE_RELATED: self.related_evaluator.presence_for_anchor,
        }

        predicate_fragments = [
            Q(evaluator_for_clause_type[clause_payload["type"].upper()](clause_payload))
            for clause_payload in group_payload["clauses"]
        ]

        predicate_fragments.extend(
            self.compose_group_predicate(child_group_payload)
            for child_group_payload in group_payload["groups"]
        )

        combined_predicate = Q() if use_and_logic else Q(pk__in=[])

        for predicate_fragment in predicate_fragments:
            combined_predicate = (
                combined_predicate & predicate_fragment
                if use_and_logic
                else combined_predicate | predicate_fragment
            )

        return combined_predicate
