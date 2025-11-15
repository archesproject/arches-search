from typing import Any, Dict, List
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PayloadValidator:
    ALLOWED_SCOPE = {"RESOURCE", "TILE"}
    ALLOW_GROUP_LOGIC = {"AND", "OR"}
    ALLOWED_CLAUSE_TYPE = {"LITERAL", "RELATED"}
    ALLOWED_QUANTIFIER = {"ANY", "ALL", "NONE"}
    ALLOWED_OPERAND_TYPE = {"LITERAL", "PATH"}

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
    REQUIRED_RELATIONSHIP_KEYS = {"path", "is_inverse", "traversal_quantifiers"}

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
        if not self._is_valid_subject_path(subject_value):
            raise ValidationError(
                _(
                    "%(location)s subject must be a non-empty list of [graph_slug, node_alias] pairs."
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
            if not self._is_valid_subject_path(operand_payload["value"]):
                raise ValidationError(
                    _("%(location)s value must be a subject path when type is PATH."),
                    params={"location": location},
                )
        else:
            if operand_payload["value"] is None:
                raise ValidationError(
                    _("%(location)s value must not be null for type LITERAL."),
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
        if not isinstance(path_value, list) or len(path_value) == 0:
            raise ValidationError(
                _("%(location)s path must be a non-empty list."),
                params={"location": location},
            )

        for hop_index, hop_pair in enumerate(path_value):
            hop_location = " > ".join(location_parts + [f"path[{hop_index}]"])
            if not isinstance(hop_pair, list) or len(hop_pair) != 2:
                raise ValidationError(
                    _("%(location)s must be [graph_slug, node_alias]."),
                    params={"location": hop_location},
                )
            hop_graph_slug, hop_node_alias = hop_pair
            if not isinstance(hop_graph_slug, str) or not hop_graph_slug:
                raise ValidationError(
                    _("%(location)s[0] must be a non-empty string."),
                    params={"location": hop_location},
                )
            if not isinstance(hop_node_alias, str) or not hop_node_alias:
                raise ValidationError(
                    _("%(location)s[1] must be a non-empty string."),
                    params={"location": hop_location},
                )

        is_inverse_value = relationship_payload["is_inverse"]
        if not isinstance(is_inverse_value, bool):
            raise ValidationError(
                _("%(location)s is_inverse must be a boolean."),
                params={"location": location},
            )

        traversal_quantifiers_value = relationship_payload["traversal_quantifiers"]
        if (
            not isinstance(traversal_quantifiers_value, list)
            or len(traversal_quantifiers_value) == 0
        ):
            raise ValidationError(
                _("%(location)s traversal_quantifiers must be a non-empty list."),
                params={"location": location},
            )

        for quantifier_index, quantifier_value in enumerate(
            traversal_quantifiers_value
        ):
            if quantifier_value not in self.ALLOWED_QUANTIFIER:
                q_location = " > ".join(
                    location_parts + [f"traversal_quantifiers[{quantifier_index}]"]
                )
                raise ValidationError(
                    _("%(location)s must be one of %(choices)s."),
                    params={
                        "location": q_location,
                        "choices": ", ".join(sorted(self.ALLOWED_QUANTIFIER)),
                    },
                )

    def _is_valid_subject_path(self, subject_path: Any) -> bool:
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
