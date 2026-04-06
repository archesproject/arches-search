from typing import Any, Dict, List
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches_search.utils.advanced_search.constants import (
    SUBJECT_TYPE_NODE,
    SUBJECT_TYPE_SEARCH_MODELS,
)
from arches_search.utils.advanced_search.relationship_utils import (
    is_node_relationship_path,
)


class PayloadValidator:
    ALLOWED_SCOPE = {"RESOURCE", "TILE"}
    ALLOW_GROUP_LOGIC = {"AND", "OR"}
    ALLOWED_CLAUSE_TYPE = {"LITERAL", "RELATED"}
    ALLOWED_QUANTIFIER = {"ANY", "ALL", "NONE"}
    ALLOWED_OPERAND_TYPE = {"LITERAL", "GEO_LITERAL", "PATH"}

    REQUIRED_GROUP_KEYS = {
        "graph_slug",
        "scope",
        "logic",
        "clauses",
        "groups",
        "aggregations",
        "relationship",
    }
    REQUIRED_CLAUSE_KEYS = {"type", "quantifier", "subject", "operator", "operands"}
    REQUIRED_OPERAND_KEYS = {"type", "value"}
    REQUIRED_RELATIONSHIP_KEYS = {"path", "is_inverse", "traversal_quantifier"}
    REQUIRED_SUBJECT_KEYS = {"type", "graph_slug", "node_alias", "search_models"}

    def validate(self, root_payload: Dict[str, Any]) -> None:
        if not isinstance(root_payload, dict):
            raise ValidationError(_("Top-level group must be an object."))
        self._validate_group(root_payload, ["group"])

    def _validate_group(
        self, group_payload: Dict[str, Any], location_parts: List[str]
    ) -> None:
        location = " > ".join(location_parts)

        missing_keys = self.REQUIRED_GROUP_KEYS - set(group_payload.keys())
        if missing_keys:
            raise ValidationError(
                _("%(location)s is missing required keys: %(keys)s"),
                params={"location": location, "keys": ", ".join(sorted(missing_keys))},
            )

        graph_slug_value = group_payload["graph_slug"]
        if not isinstance(graph_slug_value, str) or not graph_slug_value:
            raise ValidationError(
                _("%(location)s graph_slug must be a non-empty string."),
                params={"location": location},
            )

        scope_value = group_payload["scope"]
        if scope_value not in self.ALLOWED_SCOPE:
            raise ValidationError(
                _("%(location)s scope must be one of %(choices)s."),
                params={
                    "location": location,
                    "choices": ", ".join(sorted(self.ALLOWED_SCOPE)),
                },
            )

        logic_value = group_payload["logic"]
        if logic_value not in self.ALLOW_GROUP_LOGIC:
            raise ValidationError(
                _("%(location)s logic must be one of %(choices)s."),
                params={
                    "location": location,
                    "choices": ", ".join(sorted(self.ALLOW_GROUP_LOGIC)),
                },
            )

        clauses_value = group_payload["clauses"]
        if not isinstance(clauses_value, list):
            raise ValidationError(
                _("%(location)s clauses must be a list."),
                params={"location": location},
            )

        groups_value = group_payload["groups"]
        if not isinstance(groups_value, list):
            raise ValidationError(
                _("%(location)s groups must be a list."),
                params={"location": location},
            )

        aggregations_value = group_payload["aggregations"]
        if not isinstance(aggregations_value, list):
            raise ValidationError(
                _("%(location)s aggregations must be a list."),
                params={"location": location},
            )

        relationship_value = group_payload["relationship"]
        if relationship_value is not None and not isinstance(relationship_value, dict):
            raise ValidationError(
                _("%(location)s relationship must be null or an object."),
                params={"location": location},
            )

        for clause_index, clause_payload in enumerate(clauses_value):
            self._validate_clause(
                clause_payload, location_parts + [f"clauses[{clause_index}]"]
            )

        for subgroup_index, subgroup_payload in enumerate(groups_value):
            subgroup_location = " > ".join(
                location_parts + [f"groups[{subgroup_index}]"]
            )
            if not isinstance(subgroup_payload, dict):
                raise ValidationError(
                    _("%(location)s must be an object."),
                    params={"location": subgroup_location},
                )
            self._validate_group(
                subgroup_payload, location_parts + [f"groups[{subgroup_index}]"]
            )

        if relationship_value is not None:
            self._validate_relationship(
                relationship_value, location_parts + ["relationship"]
            )

    def _validate_clause(
        self, clause_payload: Dict[str, Any], location_parts: List[str]
    ) -> None:
        location = " > ".join(location_parts)

        if not isinstance(clause_payload, dict):
            raise ValidationError(
                _("%(location)s must be an object."),
                params={"location": location},
            )

        missing_keys = self.REQUIRED_CLAUSE_KEYS - set(clause_payload.keys())
        if missing_keys:
            raise ValidationError(
                _("%(location)s is missing required keys: %(keys)s"),
                params={"location": location, "keys": ", ".join(sorted(missing_keys))},
            )

        clause_type = clause_payload["type"]
        if clause_type not in self.ALLOWED_CLAUSE_TYPE:
            raise ValidationError(
                _("%(location)s type must be one of %(choices)s."),
                params={
                    "location": location,
                    "choices": ", ".join(sorted(self.ALLOWED_CLAUSE_TYPE)),
                },
            )

        quantifier_value = clause_payload["quantifier"]
        if quantifier_value not in self.ALLOWED_QUANTIFIER:
            raise ValidationError(
                _("%(location)s quantifier must be one of %(choices)s."),
                params={
                    "location": location,
                    "choices": ", ".join(sorted(self.ALLOWED_QUANTIFIER)),
                },
            )

        subject_value = clause_payload["subject"]
        if not self._is_valid_subject_dict(subject_value, clause_type):
            raise ValidationError(
                _(
                    "%(location)s subject must be an object with type, graph_slug, "
                    "node_alias, and search_models. Node subjects require a non-empty "
                    "node_alias and empty search_models. Search-model subjects require "
                    "an empty node_alias and a non-empty search_models list. RELATED "
                    "clauses must use a node subject."
                ),
                params={"location": location},
            )

        operator_value = clause_payload["operator"]
        if not isinstance(operator_value, str) or not operator_value:
            raise ValidationError(
                _("%(location)s operator must be a non-empty string."),
                params={"location": location},
            )

        operands_value = clause_payload["operands"]
        if not isinstance(operands_value, list):
            raise ValidationError(
                _("%(location)s operands must be a list."),
                params={"location": location},
            )

        for operand_index, operand_payload in enumerate(operands_value):
            self._validate_operand(
                operand_payload, location_parts + [f"operands[{operand_index}]"]
            )

    def _validate_operand(
        self, operand_payload: Any, location_parts: List[str]
    ) -> None:
        location = " > ".join(location_parts)

        if not isinstance(operand_payload, dict):
            raise ValidationError(
                _("%(location)s must be an object."),
                params={"location": location},
            )

        missing_keys = self.REQUIRED_OPERAND_KEYS - set(operand_payload.keys())
        if missing_keys:
            raise ValidationError(
                _("%(location)s is missing required keys: %(keys)s"),
                params={"location": location, "keys": ", ".join(sorted(missing_keys))},
            )

        operand_type = operand_payload["type"]
        if operand_type not in self.ALLOWED_OPERAND_TYPE:
            raise ValidationError(
                _("%(location)s type must be one of %(choices)s."),
                params={
                    "location": location,
                    "choices": ", ".join(sorted(self.ALLOWED_OPERAND_TYPE)),
                },
            )

        if operand_type == "PATH":
            if not self._is_valid_path_list(operand_payload["value"]):
                raise ValidationError(
                    _("%(location)s value must be a subject path when type is PATH."),
                    params={"location": location},
                )
        else:
            if operand_payload["value"] is None:
                raise ValidationError(
                    _("%(location)s value must not be null."),
                    params={"location": location},
                )

    def _validate_relationship(
        self, relationship_payload: Dict[str, Any], location_parts: List[str]
    ) -> None:
        location = " > ".join(location_parts)

        missing_keys = self.REQUIRED_RELATIONSHIP_KEYS - set(
            relationship_payload.keys()
        )
        if missing_keys:
            raise ValidationError(
                _("%(location)s is missing required keys: %(keys)s"),
                params={"location": location, "keys": ", ".join(sorted(missing_keys))},
            )

        path_value = relationship_payload["path"]
        if not is_node_relationship_path(path_value):
            raise ValidationError(
                _(
                    "%(location)s path must be an object with type, graph_slug, "
                    "and node_alias."
                ),
                params={"location": location},
            )

        path_graph_slug = path_value.get("graph_slug")
        if not isinstance(path_graph_slug, str) or not path_graph_slug:
            raise ValidationError(
                _("%(location)s path.graph_slug must be a non-empty string."),
                params={"location": location},
            )

        path_node_alias = path_value.get("node_alias")
        if not isinstance(path_node_alias, str) or not path_node_alias:
            raise ValidationError(
                _("%(location)s path.node_alias must be a non-empty string."),
                params={"location": location},
            )

        is_inverse_value = relationship_payload["is_inverse"]
        if not isinstance(is_inverse_value, bool):
            raise ValidationError(
                _("%(location)s is_inverse must be a boolean."),
                params={"location": location},
            )

        traversal_quantifier_value = relationship_payload["traversal_quantifier"]
        if not isinstance(traversal_quantifier_value, str):
            raise ValidationError(
                _("%(location)s traversal_quantifier must be a string."),
                params={"location": location},
            )

        if traversal_quantifier_value not in self.ALLOWED_QUANTIFIER:
            raise ValidationError(
                _("%(location)s traversal_quantifier must be one of %(choices)s."),
                params={
                    "location": location,
                    "choices": ", ".join(sorted(self.ALLOWED_QUANTIFIER)),
                },
            )

    def _is_valid_subject_dict(self, subject: Any, clause_type: str) -> bool:
        if not isinstance(subject, dict):
            return False

        missing_keys = self.REQUIRED_SUBJECT_KEYS - set(subject.keys())
        if missing_keys:
            return False

        subject_type = subject.get("type")
        if subject_type not in {SUBJECT_TYPE_NODE, SUBJECT_TYPE_SEARCH_MODELS}:
            return False

        graph_slug = subject.get("graph_slug")
        if not isinstance(graph_slug, str) or not graph_slug:
            return False

        node_alias = subject.get("node_alias")
        if not isinstance(node_alias, str):
            return False

        search_models = subject.get("search_models")
        if not isinstance(search_models, list):
            return False
        if not all(
            isinstance(model_name, str) and model_name for model_name in search_models
        ):
            return False

        if clause_type == "RELATED" and subject_type != SUBJECT_TYPE_NODE:
            return False

        if subject_type == SUBJECT_TYPE_NODE:
            return bool(node_alias) and len(search_models) == 0

        return node_alias == "" and len(search_models) > 0

    def _is_valid_path_list(self, subject_path: Any) -> bool:
        if not isinstance(subject_path, list) or len(subject_path) == 0:
            return False
        for pair in subject_path:
            if not isinstance(pair, list) or len(pair) != 2:
                return False
            graph_slug_value, node_alias_value = pair
            if not isinstance(graph_slug_value, str) or not graph_slug_value:
                return False
            if not isinstance(node_alias_value, str) or not node_alias_value:
                return False
        return True
