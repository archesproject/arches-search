from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)
from arches_search.utils.extension_discovery import discover_extension_instances


class OperandNormalizerFactory:
    registry: dict[str, BaseOperandNormalizer] = {}
    _populated: bool = False

    def __init__(self):
        if OperandNormalizerFactory._populated:
            return
        OperandNormalizerFactory.registry = discover_extension_instances(
            "advanced_search_operand_normalizers",
            BaseOperandNormalizer,
            lambda normalizer: normalizer.datatype.datatype_name,
        )
        OperandNormalizerFactory._populated = True

    def get_normalizer(self, datatype_name: str) -> BaseOperandNormalizer:
        return self.registry.get(datatype_name, BaseOperandNormalizer())
