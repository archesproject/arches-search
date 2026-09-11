from typing import Any, Dict, List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db.models import F, QuerySet
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Lower
from django.utils.translation import get_language, gettext as _

from arches_search.utils.advanced_search.constants import (
    SUBJECT_TYPE_NODE,
    SUBJECT_TYPE_RESOURCE_FIELD,
)
from arches_search.utils.resource_field_search.labels import label_expression
from arches_search.utils.resource_field_search.field_registry import (
    ResourceInstanceFieldRegistry,
    get_resource_instance_fields,
)

SORT_TYPE_PRIMARY_NAME = "primary_name"
SORT_TYPE_CREATED_TIME = "created_time"
# The same tokens a clause subject and an additional_data entry use.
SORT_TYPE_RESOURCE_FIELD = SUBJECT_TYPE_RESOURCE_FIELD
SORT_TYPE_NODE = SUBJECT_TYPE_NODE
DIRECTION_ASC = "asc"
DIRECTION_DESC = "desc"

ALLOWED_DIRECTIONS = {DIRECTION_ASC, DIRECTION_DESC}
ALLOWED_SORT_TYPES = {
    SORT_TYPE_PRIMARY_NAME,
    SORT_TYPE_CREATED_TIME,
    SORT_TYPE_RESOURCE_FIELD,
    SORT_TYPE_NODE,
}

# Applied when the payload names no sort. Empty means no user-visible ordering;
# the id tie-break still runs.
DEFAULT_SORT: List[Dict[str, Any]] = []

Ordering = Any


def _ordering(field: F, spec: Dict[str, Any], nulls_last: Optional[bool] = None):
    # nulls_last must be True or None; Django rejects False.
    if spec.get("direction", DIRECTION_ASC) == DIRECTION_ASC:
        return field.asc(nulls_last=nulls_last)
    return field.desc(nulls_last=nulls_last)


class SortResolver:
    """
    Applies sort specs to a ResourceInstance queryset.

    A spec is {"type": ..., "direction": "asc"|"desc"} plus whatever the type
    needs: "field" for RESOURCE_FIELD, "graph_slug"/"node_alias" for NODE.

    A NODE sort reads an annotation the caller must already have applied (see
    search.additional_data) and passed as node_column_annotations. A node the
    requester cannot read is skipped rather than reported.

    A tie-break on resourceinstanceid is always appended, so paging is stable.
    """

    def __init__(self, sort_specs: Optional[List[Dict[str, Any]]] = None) -> None:
        if sort_specs is None:
            sort_specs = DEFAULT_SORT
        self._resource_field_registry: Optional[ResourceInstanceFieldRegistry] = None
        self._validate(sort_specs)
        self.sort_specs = sort_specs

    @property
    def resource_field_registry(self) -> ResourceInstanceFieldRegistry:
        """Built on first use: it costs a query, and most searches never sort by one."""
        if self._resource_field_registry is None:
            self._resource_field_registry = get_resource_instance_fields()
        return self._resource_field_registry

    def apply(
        self,
        queryset: QuerySet,
        node_column_annotations: Optional[Dict[Any, str]] = None,
    ) -> QuerySet:
        node_column_annotations = node_column_annotations or {}
        order_expressions: List[Ordering] = []

        for index, spec in enumerate(self.sort_specs):
            sort_type = spec["type"]
            if sort_type == SORT_TYPE_PRIMARY_NAME:
                queryset, ordering = self._primary_name(queryset, spec, index)
            elif sort_type == SORT_TYPE_CREATED_TIME:
                queryset, ordering = self._created_time(queryset, spec)
            elif sort_type == SORT_TYPE_RESOURCE_FIELD:
                queryset, ordering = self._resource_field(queryset, spec, index)
            else:
                queryset, ordering = self._node_value(
                    queryset, spec, node_column_annotations
                )

            if ordering is not None:
                order_expressions.append(ordering)

        order_expressions.append(F("resourceinstanceid").asc())
        return queryset.order_by(*order_expressions)

    def _primary_name(
        self, queryset: QuerySet, spec: Dict[str, Any], index: int
    ) -> Tuple[QuerySet, Ordering]:
        annotation = f"_sort_primary_name_{index}"
        queryset = queryset.annotate(
            **{
                annotation: Lower(
                    KeyTextTransform(
                        "name", KeyTextTransform(get_language() or "en", "descriptors")
                    )
                )
            }
        )
        return queryset, _ordering(F(annotation), spec)

    def _created_time(
        self, queryset: QuerySet, spec: Dict[str, Any]
    ) -> Tuple[QuerySet, Ordering]:
        return queryset, _ordering(F("createdtime"), spec)

    def _resource_field(
        self, queryset: QuerySet, spec: Dict[str, Any], index: int
    ) -> Tuple[QuerySet, Ordering]:
        descriptor = self.resource_field_registry.get(spec["field"])

        # Order a foreign key by the related record's label, not its raw id.
        # Lower() lives here, not in label_expression: projection wants the
        # label as stored.
        label = label_expression(descriptor)
        if label is None:
            sort_field = F(descriptor.orm_path)
        else:
            annotation = f"_sort_resource_field_{index}"
            queryset = queryset.annotate(**{annotation: Lower(label)})
            sort_field = F(annotation)

        # A nullable column would otherwise lead on DESC in Postgres.
        return queryset, _ordering(sort_field, spec, nulls_last=True)

    def _node_value(
        self,
        queryset: QuerySet,
        spec: Dict[str, Any],
        node_column_annotations: Dict[Any, str],
    ) -> Tuple[QuerySet, Ordering]:
        annotation = node_column_annotations.get(
            (spec["graph_slug"], spec["node_alias"])
        )
        if annotation is None:
            # Unresolved or unreadable, kept indistinguishable from "no such
            # node" the way additional_data omits such columns.
            return queryset, None
        return queryset, _ordering(F(annotation), spec, nulls_last=True)

    def _validate(self, sort_specs: Any) -> None:
        if not isinstance(sort_specs, list):
            raise ValidationError(_("sort must be a list of sort specs."))

        for index, spec in enumerate(sort_specs):
            if not isinstance(spec, dict):
                raise ValidationError(
                    _("sort[%(i)s] must be an object.") % {"i": index}
                )

            sort_type = spec.get("type")
            if sort_type not in ALLOWED_SORT_TYPES:
                raise ValidationError(
                    _("sort[%(i)s] has unsupported type %(type)s.")
                    % {"i": index, "type": sort_type}
                )

            if sort_type == SORT_TYPE_RESOURCE_FIELD:
                field_name = spec.get("field")
                if (
                    not isinstance(field_name, str)
                    or self.resource_field_registry.get(field_name) is None
                ):
                    raise ValidationError(
                        _("sort[%(i)s] has unsupported field %(field)s.")
                        % {"i": index, "field": field_name}
                    )

            if sort_type == SORT_TYPE_NODE:
                for key in ("graph_slug", "node_alias"):
                    if not isinstance(spec.get(key), str) or not spec[key]:
                        raise ValidationError(
                            _("sort[%(i)s] requires a non-empty %(key)s.")
                            % {"i": index, "key": key}
                        )

            if spec.get("direction", DIRECTION_ASC) not in ALLOWED_DIRECTIONS:
                raise ValidationError(
                    _("sort[%(i)s] direction must be one of asc, desc.") % {"i": index}
                )
