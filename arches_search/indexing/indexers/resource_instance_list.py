from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType

from arches_search.indexing.indexers.resource_instance import ResourceInstanceIndexing


class ResourceInstanceListIndexing(ResourceInstanceIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance(
            "resource-instance-list"
        )
