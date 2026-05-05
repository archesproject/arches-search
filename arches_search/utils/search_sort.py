from typing import Any, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db.models import F, QuerySet
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Lower
from django.utils.translation import get_language, gettext as _


SORT_TYPE_PRIMARY_NAME = "primary_name"
DIRECTION_ASC = "asc"
DIRECTION_DESC = "desc"

ALLOWED_DIRECTIONS = {DIRECTION_ASC, DIRECTION_DESC}
ALLOWED_SORT_TYPES = {SORT_TYPE_PRIMARY_NAME}

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

    The resolver always appends a stable tie-break on resourceinstanceid so
    paginated results are deterministic.
    """

    def __init__(self, sort_specs: Optional[List[Dict[str, Any]]] = None) -> None:
        if sort_specs is None:
            sort_specs = DEFAULT_SORT
        self._validate(sort_specs)
        self.sort_specs = sort_specs

    def apply(self, queryset: QuerySet) -> QuerySet:
        order_expressions: List[Any] = []

        for index, spec in enumerate(self.sort_specs):
            if spec["type"] == SORT_TYPE_PRIMARY_NAME:
                queryset, ordering = self._apply_primary_name(queryset, spec, index)
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

            direction = spec.get("direction", DIRECTION_ASC)
            if direction not in ALLOWED_DIRECTIONS:
                raise ValidationError(
                    _("sort[%(i)s] direction must be one of asc, desc.") % {"i": index}
                )
