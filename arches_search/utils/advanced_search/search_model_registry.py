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

    def rows_for(self, graph_slug: str, node_alias: str) -> Optional[QuerySet]:
        # Optional helper if you want Group/Clause to delegate here
        # Kept simple and explicit
        model_class = self.get_model_for_datatype_name_via_graph_alias(
            graph_slug, node_alias
        )
        if model_class is None:
            return None
        return model_class.objects.filter(
            graph_slug=graph_slug, node_alias=node_alias
        ).order_by()

    def get_model_for_datatype_name_via_graph_alias(
        self, graph_slug: str, node_alias: str
    ) -> Optional[Any]:
        # This function assumes the caller has already resolved datatype if needed elsewhere.
        # Provided for symmetry; unused by default.
        return None

    def is_relationship_datatype(self, datatype_name: str) -> bool:
        return datatype_name in self._relationship_datatype_names

    def _value_field_is_uuid(self, model_class: Any) -> bool:
        model_meta = getattr(model_class, "_meta", None)
        if not model_meta:
            return False
        try:
            value_field = model_meta.get_field("value")
        except Exception:
            return False
        return isinstance(value_field, UUIDField)
