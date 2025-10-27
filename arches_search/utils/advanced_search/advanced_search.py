from functools import lru_cache
from typing import Any, Dict, Tuple, Union

from django.db.models import Exists, Q, QuerySet, F

from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.advanced_search.facet_registry import FacetRegistry
from arches_search.utils.advanced_search.node_alias_datatype_registry import (
    NodeAliasDatatypeRegistry,
)
from arches_search.utils.advanced_search.path_navigator import PathNavigator
from arches_search.utils.advanced_search.clause_compiler import ClauseCompiler
from arches_search.utils.advanced_search.group_compiler import GroupCompiler

from django.utils.translation import gettext as _


class AdvancedSearchQueryCompiler:
    @lru_cache(maxsize=128)
    def get_graph_id_for_slug(self, graph_slug: str):
        return (
            arches_models.GraphModel.objects.only("graphid")
            .get(slug=graph_slug)
            .graphid
        )

    def __init__(self, payload_query: Dict[str, Any]) -> None:
        self.graph_slug = payload_query.get("graph_slug")
        self.payload_query = payload_query

        self.search_model_registry = SearchModelRegistry()
        self.facet_registry = FacetRegistry()
        self.node_alias_datatype_registry = NodeAliasDatatypeRegistry(
            payload_query=self.payload_query
        )

        self.path_navigator = PathNavigator(
            self.search_model_registry, self.node_alias_datatype_registry
        )
        self.clause_compiler = ClauseCompiler(
            self.search_model_registry,
            self.facet_registry,
            self.path_navigator,
        )
        self.group_compiler = GroupCompiler(
            self.clause_compiler, get_graph_id_for_slug=self.get_graph_id_for_slug
        )

    def compile(self) -> Tuple[str, Union[Q, Exists]]:
        if not arches_models.GraphModel.objects.filter(slug=self.graph_slug).exists():
            raise ValueError(_("Invalid graph slug."))

        return self.group_compiler.compile(self.payload_query, parent_graph_slug=None)

    def build_resources_queryset(self) -> QuerySet:
        compiled_advanced_search_query = self.compile()
        graph_id = self.get_graph_id_for_slug(self.graph_slug)

        base_queryset = (
            arches_models.ResourceInstance.objects.filter(graph_id=graph_id)
            .only("resourceinstanceid")
            .annotate(
                anchor_resourceinstanceid=F("resourceinstanceid"),
                parent_resourceinstanceid=F("resourceinstanceid"),
            )
        )

        if (
            isinstance(compiled_advanced_search_query, Q)
            and not compiled_advanced_search_query.children
        ):
            return base_queryset

        return base_queryset.filter(compiled_advanced_search_query).only(
            "resourceinstanceid"
        )
