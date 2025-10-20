from typing import Any, Dict, Set

from django.db.models import UUIDField

from arches_search.models.models import DDatatypeXAdvancedSearchModel


class SearchModelRegistry:
    def __init__(self) -> None:
        self._datatype_to_model_class: Dict[str, Any] = {}
        self._relationship_datatypes: Set[str] = set()

        for (
            ddatatype_x_advanced_search_model
        ) in DDatatypeXAdvancedSearchModel.objects.select_related(
            "datatype", "content_type"
        ):
            model_class = getattr(
                ddatatype_x_advanced_search_model, "model_class", None
            )
            datatype_name = ddatatype_x_advanced_search_model.datatype.datatype
            self._datatype_to_model_class[datatype_name] = model_class

            if self._model_value_field_is_uuid(model_class):
                self._relationship_datatypes.add(datatype_name)

    def get_model_for_datatype(self, datatype_name: str) -> Any:
        model_class = self._datatype_to_model_class.get(datatype_name)

        if model_class is None:
            raise ValueError(f"No search model mapped for datatype '{datatype_name}'")

        return model_class

    def is_relationship_datatype(self, datatype_name: str) -> bool:
        return datatype_name in self._relationship_datatypes

    def _model_value_field_is_uuid(self, model_class: Any) -> bool:
        meta = getattr(model_class, "_meta", None)

        if not meta:
            return False

        try:
            value_field = meta.get_field("value")
        except Exception:
            return False

        if isinstance(value_field, UUIDField):
            return True

        return False
