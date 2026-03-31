from typing import Any, Dict, List
from django.db.models import UUIDField
from django.utils.translation import gettext as _
from arches_search.models.models import AdvancedSearchFacet


class SearchModelRegistry:
    def __init__(self) -> None:
        self._datatype_to_model_classes: Dict[str, List[Any]] = {}
        self._datatype_to_unambiguous_model_class: Dict[str, Any] = {}
        self._datatype_to_value_model_class: Dict[str, Any] = {}
        self._datatype_to_relationship_model_class: Dict[str, Any] = {}

        facets_by_datatype: Dict[str, Dict[str, Any]] = {}

        for facet in AdvancedSearchFacet.objects.select_related(
            "datatype", "target_search_model"
        ):
            datatype_name = facet.datatype.datatype
            model_class = facet.target_model_class
            if model_class is None:
                continue

            facets_by_datatype.setdefault(datatype_name, {})[
                model_class._meta.label_lower
            ] = model_class

        for datatype_name, model_map in facets_by_datatype.items():
            model_classes = list(model_map.values())
            self._datatype_to_model_classes[datatype_name] = model_classes

            if len(model_classes) == 1:
                self._datatype_to_unambiguous_model_class[datatype_name] = (
                    model_classes[0]
                )

            value_models = [
                model_class
                for model_class in model_classes
                if self._model_has_field(model_class, "value")
            ]
            if len(value_models) == 1:
                self._datatype_to_value_model_class[datatype_name] = value_models[0]

            relationship_models = [
                model_class
                for model_class in value_models
                if self._value_field_is_uuid(model_class)
            ]
            if len(relationship_models) == 1:
                self._datatype_to_relationship_model_class[datatype_name] = (
                    relationship_models[0]
                )

    def get_model_for_datatype(self, datatype_name: str) -> Any:
        model_class = self._datatype_to_unambiguous_model_class.get(datatype_name)

        if model_class is None:
            raise ValueError(
                _(
                    "No unambiguous search model can be derived from facets for datatype '{datatype}'"
                ).format(datatype=datatype_name)
            )

        return model_class

    def get_all_models_for_datatype(self, datatype_name: str) -> List[Any]:
        model_classes = self._datatype_to_model_classes.get(datatype_name)

        if not model_classes:
            raise ValueError(
                _(
                    "No search models can be derived from facets for datatype '{datatype}'"
                ).format(datatype=datatype_name)
            )

        return model_classes

    def get_value_model_for_datatype(self, datatype_name: str) -> Any:
        model_class = self._datatype_to_value_model_class.get(datatype_name)

        if model_class is None:
            raise ValueError(
                _(
                    "No value-bearing search model can be derived from facets for datatype '{datatype}'"
                ).format(datatype=datatype_name)
            )

        return model_class

    def get_relationship_model_for_datatype(self, datatype_name: str) -> Any:
        model_class = self._datatype_to_relationship_model_class.get(datatype_name)

        if model_class is None:
            raise ValueError(
                _(
                    "No relationship search model can be derived from facets for datatype '{datatype}'"
                )
            )

        return model_class

    def _model_has_field(self, model_class: Any, field_name: str) -> bool:
        model_meta = getattr(model_class, "_meta", None)

        if not model_meta:
            return False

        try:
            model_meta.get_field(field_name)
        except Exception:
            return False

        return True

    def _value_field_is_uuid(self, model_class: Any) -> bool:
        model_meta = getattr(model_class, "_meta", None)

        if not model_meta:
            return False

        try:
            value_field = model_meta.get_field("value")
        except Exception:
            return False

        return isinstance(value_field, UUIDField)
