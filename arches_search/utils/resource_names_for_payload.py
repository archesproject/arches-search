import uuid as uuid_module
from typing import Any, Dict, List

from django.conf import settings
from django.utils.translation import get_language

from arches.app.models import models as arches_models

OPERAND_TYPE_LITERAL = "LITERAL"


def _is_valid_uuid_string(value: str) -> bool:
    try:
        uuid_module.UUID(value)
        return True
    except ValueError:
        return False


def _collect_uuid_strings_from_group_payload(
    group_payload: Dict[str, Any],
) -> List[str]:
    uuid_strings_found: List[str] = []

    for clause in group_payload.get("clauses", []):
        for operand in clause.get("operands", []):
            if operand.get("type") != OPERAND_TYPE_LITERAL:
                continue
            operand_value = operand.get("value")
            if not isinstance(operand_value, list):
                continue
            for item in operand_value:
                if isinstance(item, str) and _is_valid_uuid_string(item):
                    uuid_strings_found.append(item)

    for child_group in group_payload.get("groups", []):
        uuid_strings_found.extend(_collect_uuid_strings_from_group_payload(child_group))

    return uuid_strings_found


def _resolve_resource_display_name(
    descriptors_field_value: Any,
    i18n_name_field_value: Any,
    language_code: str,
    default_language_code: str,
) -> str:
    if isinstance(descriptors_field_value, dict):
        for candidate_language_code in (language_code, default_language_code):
            language_descriptor_entry = descriptors_field_value.get(
                candidate_language_code
            )
            if isinstance(language_descriptor_entry, dict):
                candidate_name = language_descriptor_entry.get("name", "")
                if isinstance(candidate_name, str) and candidate_name.strip():
                    return candidate_name.strip()
        for language_descriptor_entry in descriptors_field_value.values():
            if isinstance(language_descriptor_entry, dict):
                candidate_name = language_descriptor_entry.get("name", "")
                if isinstance(candidate_name, str) and candidate_name.strip():
                    return candidate_name.strip()

    if isinstance(i18n_name_field_value, str):
        return i18n_name_field_value.strip()

    if isinstance(i18n_name_field_value, dict):
        for candidate_language_code in (language_code, default_language_code):
            candidate_name = i18n_name_field_value.get(candidate_language_code)
            if isinstance(candidate_name, str) and candidate_name.strip():
                return candidate_name.strip()
        for candidate_name in i18n_name_field_value.values():
            if isinstance(candidate_name, str) and candidate_name.strip():
                return candidate_name.strip()

    return ""


def build_resource_names_for_payload(
    group_payload: Dict[str, Any],
) -> Dict[str, str]:
    language_code = get_language() or settings.LANGUAGE_CODE
    default_language_code = settings.LANGUAGE_CODE

    all_operand_uuid_strings = _collect_uuid_strings_from_group_payload(group_payload)
    if not all_operand_uuid_strings:
        return {}

    resource_instance_rows = arches_models.ResourceInstance.objects.filter(
        pk__in=set(all_operand_uuid_strings)
    ).values("resourceinstanceid", "name", "descriptors")

    resource_names_by_id: Dict[str, str] = {}
    for row in resource_instance_rows.iterator():
        resource_instance_id = str(row["resourceinstanceid"])
        resolved_display_name = _resolve_resource_display_name(
            row["descriptors"],
            row["name"],
            language_code,
            default_language_code,
        )
        if resolved_display_name:
            resource_names_by_id[resource_instance_id] = resolved_display_name

    return resource_names_by_id
