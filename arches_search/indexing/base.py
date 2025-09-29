from arches.app.datatypes.datatypes import BaseDataType


class BaseIndexing:
    def __init__(self):
        self.datatype: BaseDataType = None

    def index(self, tile, node):
        pass
