from arches_search.indexing.base import BaseIndexing
from arches_search.utils.extension_discovery import discover_extension_instances


class IndexingFactory:
    registry: dict[str, BaseIndexing] = {}
    _populated: bool = False

    def __init__(self):
        if IndexingFactory._populated:
            return
        IndexingFactory.registry = discover_extension_instances(
            "search_indexers",
            BaseIndexing,
            lambda indexer: indexer.datatype.datatype_name,
        )
        IndexingFactory._populated = True

    def get_indexing_class(self, datatype: str) -> BaseIndexing:
        return self.registry.get(datatype, BaseIndexing())

    def vocabulary_datatypes(self) -> list[str]:
        return [
            datatype_name
            for datatype_name, indexer in self.registry.items()
            if indexer.hierarchy_edges() is not None
        ]
