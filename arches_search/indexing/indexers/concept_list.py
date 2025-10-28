from arches.app.datatypes.datatypes import DataTypeFactory, BaseDataType
from arches.app.models.models import Language

from arches_search.indexing.indexers.concept import ConceptIndexing


class ConceptListIndexing(ConceptIndexing):
    def __init__(self):
        super().__init__()
        self.datatype: BaseDataType = DataTypeFactory().get_instance("concept-list")
        self.languages: dict[str, Language] = {}
