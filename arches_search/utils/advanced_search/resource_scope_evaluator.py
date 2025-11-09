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

    def q_for_group(self, group_payload: Dict[str, Any]) -> Optional[Q]:
        use_and_logic = (group_payload.get("logic") or LOGIC_AND).upper() == LOGIC_AND
        has_any_piece = False
        combined_q = Q()

        for clause_payload in group_payload.get("clauses") or []:
            clause_type = (clause_payload.get("type") or "").upper()
            if clause_type == CLAUSE_TYPE_LITERAL:
                exists_expression = self.literal_evaluator.exists_for_anchor(
                    clause_payload
                )
            elif clause_type == CLAUSE_TYPE_RELATED:
                exists_expression = self.related_evaluator.presence_for_anchor(
                    clause_payload
                )
            else:
                continue
            clause_q = Q(exists_expression)
            if not has_any_piece:
                combined_q = clause_q
                has_any_piece = True
            else:
                combined_q = (
                    combined_q & clause_q if use_and_logic else combined_q | clause_q
                )

        for child_group_payload in group_payload.get("groups") or []:
            if (child_group_payload.get("relationship") or {}).get("path"):
                return None
            child_q = self.q_for_group(child_group_payload)
            if child_q is None:
                return None
            if not has_any_piece:
                combined_q = child_q
                has_any_piece = True
            else:
                combined_q = (
                    combined_q & child_q if use_and_logic else combined_q | child_q
                )

        if not has_any_piece:
            return Q() if use_and_logic else Q(pk__in=[])
        return combined_q
