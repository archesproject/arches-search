from typing import Any, Dict, List, Tuple
from django.db.models import Q, Exists
from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.node_alias_datatype_registry import (
    NodeAliasDatatypeRegistry,
)
from arches_search.utils.advanced_search.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.advanced_search.facet_registry import FacetRegistry
from arches_search.utils.advanced_search.path_navigator import PathNavigator
from arches_search.utils.advanced_search.clause_compiler import ClauseCompiler
from arches_search.utils.advanced_search.group_compiler import GroupCompiler


class AdvancedSearchQueryCompiler:
    def __init__(self, payload_query: Dict[str, Any]) -> None:
        self.payload_query = payload_query
        self.facet_registry = FacetRegistry()
        self.search_model_registry = SearchModelRegistry()
        self.node_alias_registry = NodeAliasDatatypeRegistry(payload_query)
        self.path_navigator = PathNavigator(
            self.search_model_registry, self.node_alias_registry
        )
        self.clause_compiler = ClauseCompiler(
            self.search_model_registry, self.facet_registry, self.path_navigator
        )
        self.group_compiler = GroupCompiler(self.clause_compiler, self.path_navigator)

    def compile(self) -> Tuple[Q, List[Exists]]:
        anchor_graph_slug = self.payload_query.get("graph_slug")

        combined_predicate, existence_predicates = self.group_compiler.compile(
            group_payload=self.payload_query,
            anchor_graph_slug=anchor_graph_slug,
        )

        return combined_predicate, existence_predicates

    def build_queryset(self):
        anchor_graph_slug = self.payload_query.get("graph_slug")
        combined_predicate, existence_predicates = self.compile()

        queryset = arches_models.ResourceInstance.objects.only(
            "resourceinstanceid"
        ).filter(graph__slug=anchor_graph_slug)

        for existence_predicate in existence_predicates:
            queryset = queryset.filter(existence_predicate)

        if combined_predicate:
            queryset = queryset.filter(combined_predicate)

        if queryset.exists():
            print("[ADV][TOP] FINAL SQL:", str(queryset.query))

        return queryset
