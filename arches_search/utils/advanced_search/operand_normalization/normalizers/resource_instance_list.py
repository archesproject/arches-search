from arches.app.datatypes.datatypes import DataTypeFactory

from arches_search.utils.advanced_search.operand_normalization.normalizers.resource_instance import (
    ResourceInstanceOperandNormalizer,
)


class ResourceInstanceListOperandNormalizer(ResourceInstanceOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("resource-instance-list")
