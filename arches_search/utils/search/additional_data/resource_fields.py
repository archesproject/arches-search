"""
Projecting a resource's own columns onto search results.

The raw columns are already on a result row -- a search returns ResourceInstance
objects -- but two things are not: a foreign key's label, and any field reached
through a relation (principaluser__username). Both are annotated before
pagination, so they arrive with the page rather than costing a query per row.
"""

import hashlib
from typing import Any, Dict, Iterable, List, Optional

from django.core.exceptions import ValidationError
from django.db.models import F, QuerySet
from django.utils.translation import gettext as _

from arches_search.utils.resource_field_search.field_registry import (
    ResourceInstanceField,
    get_resource_instance_fields,
)
from arches_search.utils.resource_field_search.labels import label_expression

# Namespaced so these cannot collide with a node annotation, a sort annotation,
# or a real column.
ANNOTATION_PREFIX = "_arches_search_resource_field_"


def field_names(entries: Optional[List[Dict[str, Any]]]) -> List[str]:
    """The field names given by RESOURCE_FIELD entries, deduplicated."""
    if not entries:
        return []
    seen: List[str] = []
    for entry in entries:
        if entry["field"] not in seen:
            seen.append(entry["field"])
    return seen


def resolve(names: Iterable[str], registry=None) -> Dict[str, ResourceInstanceField]:
    """
    Look field names up in the registry.

    An unknown field is reported rather than dropped -- the opposite of a node,
    which is silently omitted. The registry is public (the metadata endpoint
    serves it), so silence here would hide a client's mistake without protecting
    anything, and a clause naming the same bad field already raises.
    """
    names = list(names)
    if not names:
        return {}

    registry = registry or get_resource_instance_fields()

    resolved: Dict[str, ResourceInstanceField] = {}
    for name in names:
        descriptor = registry.get(name)
        if descriptor is None:
            raise ValidationError(
                _("additional_data names an unqueryable resource field: %(field)s.")
                % {"field": name}
            )
        resolved[name] = descriptor
    return resolved


def annotation_name_for(field_name: str, part: str) -> str:
    """Deterministic, so the same field requested twice resolves to one alias."""
    digest = hashlib.sha1(f"{field_name}\x1f{part}".encode("utf-8")).hexdigest()[:16]
    return f"{ANNOTATION_PREFIX}{digest}"


def annotate(
    queryset: QuerySet, descriptors: Dict[str, ResourceInstanceField]
) -> tuple:
    """
    Annotate each field's value, and its label where it has one.

    The value is annotated even when it is already a column on the row, because
    a field reached through a relation is not -- one path for both keeps the
    read side from having to tell them apart.
    """
    annotations: Dict[str, Any] = {}
    annotation_names: Dict[str, Dict[str, Optional[str]]] = {}

    for field_name, descriptor in descriptors.items():
        value_annotation = annotation_name_for(field_name, "value")
        annotations[value_annotation] = F(descriptor.orm_path)

        label_annotation = None
        expression = label_expression(descriptor)
        if expression is not None:
            label_annotation = annotation_name_for(field_name, "label")
            annotations[label_annotation] = expression

        annotation_names[field_name] = {
            "value": value_annotation,
            "label": label_annotation,
        }

    if annotations:
        queryset = queryset.annotate(**annotations)
    return queryset, annotation_names


def format_values(
    resources,
    descriptors: Dict[str, ResourceInstanceField],
    annotation_names: Dict[str, Dict[str, Optional[str]]],
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Build {resourceinstanceid: {field: {"value": ..., "label": ...}}}.

    Both keys are always present. A field with no related record to name -- a
    date, a legacy id -- carries a null label rather than a different shape, so
    a client never has to branch.
    """
    if not descriptors:
        return {}

    values_by_resource: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for resource in resources:
        fields: Dict[str, Dict[str, Any]] = {}
        for field_name in descriptors:
            names = annotation_names[field_name]
            label_annotation = names["label"]
            fields[field_name] = {
                "value": getattr(resource, names["value"], None),
                "label": (
                    getattr(resource, label_annotation, None)
                    if label_annotation
                    else None
                ),
            }
        values_by_resource[str(resource.pk)] = fields

    return values_by_resource
