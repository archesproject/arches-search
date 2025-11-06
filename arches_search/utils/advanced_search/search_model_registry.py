from typing import Any, Dict, Set, Optional
from django.db.models import UUIDField, QuerySet
from django.utils.translation import gettext as _
from arches_search.models.models import DDatatypeXAdvancedSearchModel


class SearchModelRegistry:
    def __init__(self) -> None:
        self._datatype_to_model_class: Dict[str, Any] = {}
        self._relationship_datatype_names: Set[str] = set()

        for mapping in DDatatypeXAdvancedSearchModel.objects.select_related(
            "datatype", "content_type"
        ):
            model_class = getattr(mapping, "model_class", None)
            datatype_name = mapping.datatype.datatype
            self._datatype_to_model_class[datatype_name] = model_class

            if self._value_field_is_uuid(model_class):
                self._relationship_datatype_names.add(datatype_name)

    def get_model_for_datatype(self, datatype_name: str) -> Any:
        model_class = self._datatype_to_model_class.get(datatype_name)

        if model_class is None:
            raise ValueError(
                _("No search model mapped for datatype '%(datatype)s'")
                % {"datatype": datatype_name}
            )

        return model_class

    def _value_field_is_uuid(self, model_class: Any) -> bool:
        model_meta = getattr(model_class, "_meta", None)

        if not model_meta:
            return False

        try:
            value_field = model_meta.get_field("value")
        except Exception:
            return False

        return isinstance(value_field, UUIDField)
