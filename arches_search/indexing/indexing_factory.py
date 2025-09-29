import importlib
import inspect
import sys
from arches_search.indexing.base import BaseIndexing
from pathlib import Path


class IndexingFactory:
    registry: dict[str, BaseIndexing] = {}

    def __init__(self):
        modules = (Path(__file__).parent / "indexers").glob("*.py")
        for module in modules:
            if module.name == "__init__.py":
                continue
            module_name = "arches_search.indexing.indexers.{}".format(module.stem)
            spec = importlib.util.spec_from_file_location(module_name, str(module))
            py_module = importlib.util.module_from_spec(spec)

            sys.modules[module_name] = py_module
            spec.loader.exec_module(py_module)

            for name in dir(py_module):
                obj = getattr(py_module, name)
                if inspect.isclass(obj) and obj.__module__ == module_name:
                    indexer = obj()
                    self.registry[indexer.datatype.datatype_name] = indexer

    def get_indexing_class(self, datatype: str) -> BaseIndexing:
        return self.registry.get(datatype, BaseIndexing())
