from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models.models import Value

from arches_search.utils.advanced_search.constants import OPERAND_TYPE_LITERAL
from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)


class ConceptOperandNormalizer(BaseOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("concept")

    def normalize_value(self, operand_item):
        raw_value = operand_item.get("value")
        if operand_item.get("type", "").upper() != OPERAND_TYPE_LITERAL:
            return raw_value

        value_ids = raw_value if isinstance(raw_value, list) else [raw_value]
        concept_ids_by_value_id = {
            str(value_id): str(concept_id)
            for value_id, concept_id in Value.objects.filter(
                valueid__in=value_ids
            ).values_list("valueid", "concept_id")
        }
        return [
            concept_ids_by_value_id.get(str(value_id), value_id)
            for value_id in value_ids
        ]
