"""
A resource field's human-readable form.

A foreign key stores an id; a reader wants the related record's name. The
registry records where that name lives (label_orm_path) and how it is stored, so
both ordering and projection resolve it the same way.
"""

from typing import Any, Optional

from django.db.models import F
from django.db.models.fields.json import KeyTextTransform
from django.utils.translation import get_language

from arches_search.utils.resource_field_search.field_registry import (
    ResourceInstanceField,
)


def label_expression(descriptor: ResourceInstanceField) -> Optional[Any]:
    """
    An ORM expression for the field's label, or None when it has none.

    Deliberately un-cased: sorting wraps this in Lower() so ordering ignores
    case, while projection needs the label as stored -- "Draft", not "draft".
    """
    if descriptor.label_is_i18n_json:
        # Stored as {language: value}, so the active language picks the string.
        return KeyTextTransform(get_language() or "en", descriptor.label_orm_path)
    if descriptor.label_is_text:
        return F(descriptor.label_orm_path)
    return None
