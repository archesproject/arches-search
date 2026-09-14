from typing import Any, Dict, Optional
from django.db.models import QuerySet
from django.utils.translation import gettext as _
from arches.app.models import models as arches_models

from arches_search.utils.advanced_search.registries.node_alias_datatype_registry import (
    NodeAliasDatatypeRegistry,
)
from arches_search.utils.advanced_search.registries.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.advanced_search.registries.facet_registry import FacetRegistry
from arches_search.utils.advanced_search.path_navigator import PathNavigator
from arches_search.utils.advanced_search.predicate_building.predicate_builder import (
    PredicateBuilder,
)
from arches_search.utils.advanced_search.clause_evaluation.literal_clause_evaluator import (
    LiteralClauseEvaluator,
)
from arches_search.utils.advanced_search.clause_evaluation.related_clause_evaluator import (
    RelatedClauseEvaluator,
)
from arches_search.utils.advanced_search.clause_evaluation.resource_field_clause_evaluator import (
    ResourceFieldClauseEvaluator,
)
from arches_search.utils.advanced_search.clause_evaluation.tile_scope_evaluator import (
    TileScopeEvaluator,
)
from arches_search.utils.advanced_search.clause_evaluation.clause_reducer import (
    ClauseReducer,
)
from arches_search.utils.advanced_search.clause_evaluation.group_compiler import (
    GroupCompiler,
)
from arches_search.utils.advanced_search.payload_validator import PayloadValidator
from arches_search.utils.readable_nodes import ReadableNodes


class AdvancedSearchQueryCompiler:
    """
    Compiles one graph's advanced search payload into a ResourceInstance queryset.

    Args:
        payload_query (dict): The advanced search payload for one graph.
        facet_registry (FacetRegistry, optional): The registry of facets. Created if
            not given.
        search_model_registry (SearchModelRegistry, optional): The registry of search
            index models. Created if not given.
        resource_field_registry (ResourceInstanceFieldRegistry, optional): The registry
            of queryable resource fields. Created if not given.
        user (User, optional): The user the search runs as. Used by IS_CURRENT_USER and
            to work out which nodes they can read.
        readable_nodes (ReadableNodes, optional): The nodes the user can read. Created
            from user if not given.
    """

    def __init__(
        self,
        payload_query: Dict[str, Any],
        facet_registry: Optional[FacetRegistry] = None,
        search_model_registry: Optional[SearchModelRegistry] = None,
        resource_field_registry=None,
        user=None,
        readable_nodes: Optional[ReadableNodes] = None,
    ) -> None:
        PayloadValidator().validate(payload_query)

        self.payload_query = payload_query

        self.facet_registry = (
            facet_registry if facet_registry is not None else FacetRegistry()
        )
        self.search_model_registry = (
            search_model_registry
            if search_model_registry is not None
            else SearchModelRegistry()
        )
        self.node_alias_registry = NodeAliasDatatypeRegistry(
            payload_query,
            readable_nodes=(
                readable_nodes if readable_nodes is not None else ReadableNodes(user)
            ),
        )
        self.path_navigator = PathNavigator(
            self.search_model_registry, self.node_alias_registry
        )

        self.predicate_builder = PredicateBuilder(
            self.facet_registry, self.path_navigator
        )

        self.literal_clause_evaluator = LiteralClauseEvaluator(
            self.search_model_registry,
            self.facet_registry,
            self.path_navigator,
            self.predicate_builder,
        )
        self.related_clause_evaluator = RelatedClauseEvaluator(
            self.search_model_registry,
            self.facet_registry,
            self.path_navigator,
            self.predicate_builder,
        )

        self.tile_scope_evaluator = TileScopeEvaluator(
            literal_clause_evaluator=self.literal_clause_evaluator,
        )

        self.resource_field_clause_evaluator = ResourceFieldClauseEvaluator(
            user=user,
            registry=resource_field_registry,
        )

        self.clause_reducer = ClauseReducer(
            literal_clause_evaluator=self.literal_clause_evaluator,
            related_clause_evaluator=self.related_clause_evaluator,
            tile_scope_evaluator=self.tile_scope_evaluator,
            resource_field_clause_evaluator=self.resource_field_clause_evaluator,
            facet_registry=self.facet_registry,
            path_navigator=self.path_navigator,
            node_alias_datatype_registry=self.node_alias_registry,
        )

        self.group_compiler = GroupCompiler(
            clause_reducer=self.clause_reducer,
            literal_clause_evaluator=self.literal_clause_evaluator,
            related_clause_evaluator=self.related_clause_evaluator,
            tile_scope_evaluator=self.tile_scope_evaluator,
            resource_field_clause_evaluator=self.resource_field_clause_evaluator,
            path_navigator=self.path_navigator,
        )

    def compile(self, pre_filter=None) -> QuerySet:
        """
        Compiles the provided search query into a Django queryset.
        :param pre_filter: An optional initial queryset to apply the compiled query on.
        :return: A Django queryset representing the compiled search query.
        """

        filter_predicate, existence_predicates = self.group_compiler.compile(
            group_payload=self.payload_query,
        )

        if pre_filter is not None:
            queryset = pre_filter
        else:
            anchor_graph_slug = self.payload_query["graph_slug"]
            anchor_graph_id = (
                arches_models.Graph.objects.filter(slug=anchor_graph_slug)
                .values_list("graphid", flat=True)
                .first()
            )
            if anchor_graph_id is None:
                raise ValueError(
                    _("Unknown graph slug: %(slug)s") % {"slug": anchor_graph_slug}
                )

            queryset = arches_models.ResourceInstance.objects.filter(
                graph_id=anchor_graph_id
            ).order_by()

        for existence_predicate in existence_predicates:
            queryset = queryset.filter(existence_predicate)

        if filter_predicate:
            queryset = queryset.filter(filter_predicate)

        return queryset
