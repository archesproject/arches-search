from arches.app.datatypes.datatypes import DataTypeFactory

from arches_search.utils.advanced_search.operand_normalization.normalizers.concept import (
    ConceptOperandNormalizer,
)


class ConceptListOperandNormalizer(ConceptOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("concept-list")
