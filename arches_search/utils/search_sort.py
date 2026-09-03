from typing import Any, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db.models import F, QuerySet
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Lower
from django.utils.translation import get_language, gettext as _

from arches_search.utils.resource_field_search.field_registry import (
    get_resource_instance_fields,
)

SORT_TYPE_PRIMARY_NAME = "primary_name"
SORT_TYPE_CREATED_TIME = "created_time"
SORT_TYPE_RESOURCE_FIELD = "resource_field"
SORT_TYPE_EXTRA_COLUMN = "extra_column"
DIRECTION_ASC = "asc"
DIRECTION_DESC = "desc"

ALLOWED_DIRECTIONS = {DIRECTION_ASC, DIRECTION_DESC}
ALLOWED_SORT_TYPES = {
    SORT_TYPE_PRIMARY_NAME,
    SORT_TYPE_CREATED_TIME,
    SORT_TYPE_RESOURCE_FIELD,
    SORT_TYPE_EXTRA_COLUMN,
}

# Applied when no sort is supplied in the payload. Empty = no user-visible
# ordering (the id tie-break still runs for stable pagination). Populate with
# sort specs — e.g. [{"type": SORT_TYPE_PRIMARY_NAME, "direction": DIRECTION_ASC}]
# — to preset an ordering without requiring the user to pick one.
DEFAULT_SORT: List[Dict[str, Any]] = []


class SortResolver:
    """
    Applies a list of sort specs to a ResourceInstance queryset.

    Each spec is a dict: {"type": "<sort_type>", "direction": "asc"|"desc", ...}.
    Extra keys may be used by specific sort types (e.g. node sorts in the future).

    Registered sort types:
      - "primary_name": sort by descriptors[active-language].name
        (case-insensitive). Numbers and symbols fall wherever Postgres places
        them in standard text ordering.
      - "created_time": sort by ResourceInstance.createdtime (the resource's
        actual creation timestamp — there is no "last modified" field to
        sort by instead).
      - "resource_field": sort by any field ResourceInstanceFieldRegistry exposes, named
        by an extra "field" key. Foreign keys order by the related record's
        label (e.g. a lifecycle state's name) rather than by its opaque primary
        key, and nulls always sort last regardless of direction.
      - "extra_column": sort by a node (tile) value, named by extra
        "graph_slug"/"node_alias" keys. Requires the caller to have annotated
        the value onto the queryset first (see utils.extra_columns) and to pass
        the resulting names as node_column_annotations; a column the requester
        may not read is silently skipped rather than reported.

    The resolver always appends a stable tie-break on resourceinstanceid so
    paginated results are deterministic.
    """

    def __init__(self, sort_specs: Optional[List[Dict[str, Any]]] = None) -> None:
        if sort_specs is None:
            sort_specs = DEFAULT_SORT
        self._validate(sort_specs)
        self.sort_specs = sort_specs

    def apply(
        self,
        queryset: QuerySet,
        node_column_annotations: Optional[Dict[Any, str]] = None,
    ) -> QuerySet:
        order_expressions: List[Any] = []
        node_column_annotations = node_column_annotations or {}

        for index, spec in enumerate(self.sort_specs):
            if spec["type"] == SORT_TYPE_PRIMARY_NAME:
                queryset, ordering = self._apply_primary_name(queryset, spec, index)
                order_expressions.append(ordering)
            elif spec["type"] == SORT_TYPE_CREATED_TIME:
                order_expressions.append(self._apply_created_time(spec))
            elif spec["type"] == SORT_TYPE_RESOURCE_FIELD:
                queryset, ordering = self._apply_resource_field(queryset, spec, index)
                order_expressions.append(ordering)
            elif spec["type"] == SORT_TYPE_EXTRA_COLUMN:
                ordering = self._apply_extra_column(spec, node_column_annotations)
                if ordering is not None:
                    order_expressions.append(ordering)

        order_expressions.append(F("resourceinstanceid").asc())
        return queryset.order_by(*order_expressions)

    @staticmethod
    def _apply_primary_name(queryset: QuerySet, spec: Dict[str, Any], index: int):
        language = get_language() or "en"
        name_annotation = f"_sort_primary_name_{index}"

        queryset = queryset.annotate(
            **{
                name_annotation: Lower(
                    KeyTextTransform("name", KeyTextTransform(language, "descriptors"))
                )
            }
        )

        direction = spec.get("direction", DIRECTION_ASC)
        name_field = F(name_annotation)
        ordering = name_field.asc() if direction == DIRECTION_ASC else name_field.desc()
        return queryset, ordering

    @staticmethod
    def _apply_created_time(spec: Dict[str, Any]):
        direction = spec.get("direction", DIRECTION_ASC)
        created_time_field = F("createdtime")
        return (
            created_time_field.asc()
            if direction == DIRECTION_ASC
            else created_time_field.desc()
        )

    @staticmethod
    def _apply_resource_field(queryset: QuerySet, spec: Dict[str, Any], index: int):
        descriptor = get_resource_instance_fields().get(spec["field"])
        direction = spec.get("direction", DIRECTION_ASC)

        if descriptor.label_orm_path and (
            descriptor.label_is_i18n_json or descriptor.label_is_text
        ):
            # Ordering by a foreign key's raw id is meaningless to a reader, so
            # sort by the related record's label instead.
            if descriptor.label_is_i18n_json:
                language = get_language() or "en"
                label_expression = Lower(
                    KeyTextTransform(language, descriptor.label_orm_path)
                )
            else:
                label_expression = Lower(descriptor.label_orm_path)

            label_annotation = f"_sort_resource_field_{index}"
            queryset = queryset.annotate(**{label_annotation: label_expression})
            sort_field = F(label_annotation)
        else:
            sort_field = F(descriptor.orm_path)

        # Nullable columns (principaluser, for one) otherwise lead on DESC in
        # Postgres, which reads as a bug to anyone scanning the first page.
        ordering = (
            sort_field.asc(nulls_last=True)
            if direction == DIRECTION_ASC
            else sort_field.desc(nulls_last=True)
        )
        return queryset, ordering

    @staticmethod
    def _apply_extra_column(
        spec: Dict[str, Any], node_column_annotations: Dict[Any, str]
    ):
        annotation_name = node_column_annotations.get(
            (spec["graph_slug"], spec["node_alias"])
        )
        if annotation_name is None:
            # The node did not resolve or is not readable by this user. Skipping
            # keeps that indistinguishable from "no such node", matching how
            # extra_columns omits rather than reports such columns.
            return None

        direction = spec.get("direction", DIRECTION_ASC)
        sort_field = F(annotation_name)
        return (
            sort_field.asc(nulls_last=True)
            if direction == DIRECTION_ASC
            else sort_field.desc(nulls_last=True)
        )

    @staticmethod
    def _validate(sort_specs: Any) -> None:
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
                    or get_resource_instance_fields().get(field_name) is None
                ):
                    raise ValidationError(
                        _("sort[%(i)s] has unsupported field %(field)s.")
                        % {"i": index, "field": field_name}
                    )

            if sort_type == SORT_TYPE_EXTRA_COLUMN:
                for key in ("graph_slug", "node_alias"):
                    if not isinstance(spec.get(key), str) or not spec[key]:
                        raise ValidationError(
                            _("sort[%(i)s] requires a non-empty %(key)s.")
                            % {"i": index, "key": key}
                        )

            direction = spec.get("direction", DIRECTION_ASC)
            if direction not in ALLOWED_DIRECTIONS:
                raise ValidationError(
                    _("sort[%(i)s] direction must be one of asc, desc.") % {"i": index}
                )
