# advanced_search.py (excerpt with compiler wiring unchanged except for prints kept)
from typing import Any, Dict, List, Optional, Tuple, Sequence
from django.db.models import Q, Exists, OuterRef
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
        self.path_navigator.attach_clause_compiler_for_fastpath(self.clause_compiler)
        self.group_compiler = GroupCompiler(self.clause_compiler, self.path_navigator)

    def compile(self) -> Tuple[Q, List[Exists]]:
        graph_slug = self.payload_query.get("graph_slug")
        print("[ADV][TOP] compile() graph_slug=%s", graph_slug)

        if not self._graph_slug_exists(graph_slug):
            raise ValueError("Graph slug does not exist")

        compiled_q, compiled_exists_list = self.group_compiler.compile(
            group_payload=self.payload_query,
            anchor_graph_slug=graph_slug,
        )

        if not compiled_exists_list:
            relationship_context = (self.payload_query or {}).get("relationship")
            if self._looks_like_zero_arity_related_leg_shape(
                self.payload_query, relationship_context
            ):
                leg_path = relationship_context.get("path")
                is_inverse_relationship = bool(relationship_context.get("is_inverse"))
                compiled_exists_list.append(
                    self._leg_exists_for_path(leg_path, is_inverse_relationship)
                )
                print("[ADV][TOP] patched leg EXISTS via zero-arity RELATED shape")

        print("[ADV][TOP] compiled Q: %r", compiled_q)
        print("[ADV][TOP] compiled exists filters count=%s", len(compiled_exists_list))
        return compiled_q, compiled_exists_list

    def build_resources_queryset(self):
        graph_slug = self.payload_query.get("graph_slug")
        print("[ADV][TOP] build_resources_queryset() graph_slug=%s", graph_slug)

        compiled_q, exists_filters = self.compile()

        graph_id = self._get_graph_id_for_slug(graph_slug)
        print("[ADV][TOP] graph_id=%s", graph_id)

        base = arches_models.ResourceInstance.objects.only("resourceinstanceid").filter(
            graph=graph_id
        )
        try:
            print("[ADV][TOP] base queryset SQL:", str(base.query))
        except Exception as exc:
            print("[ADV][TOP] base queryset SQL <unavailable>:", exc)

        for index, exists_expr in enumerate(exists_filters):
            try:
                print(
                    f"[ADV][TOP] applying EXISTS[{index}] SQL:",
                    str(base.filter(exists_expr).query),
                )
            except Exception as exc:
                print(f"[ADV][TOP] applying EXISTS[{index}] SQL <unavailable>:", exc)
            base = base.filter(exists_expr)

        if compiled_q:
            try:
                print("[ADV][TOP] applying Q SQL:", str(base.filter(compiled_q).query))
            except Exception as exc:
                print("[ADV][TOP] applying Q SQL <unavailable>:", exc)
            base = base.filter(compiled_q)

        print("[ADV][TOP] payload_query:", self.payload_query)

        try:
            print("[ADV][TOP] FINAL SQL:", str(base.query))
        except Exception as exc:
            print("[ADV][TOP] FINAL SQL <unavailable>:", exc)

        return base.values("resourceinstanceid")

    def _graph_slug_exists(self, graph_slug: Optional[str]) -> bool:
        if not graph_slug:
            return False
        return arches_models.GraphModel.objects.filter(slug=graph_slug).exists()

    def _get_graph_id_for_slug(self, graph_slug: str):
        row = (
            arches_models.GraphModel.objects.filter(slug=graph_slug)
            .only("graphid")
            .values_list("graphid", flat=True)
            .first()
        )
        if not row:
            raise ValueError(f"Graph id for slug '{graph_slug}' not found.")
        return row

    def _looks_like_zero_arity_related_leg_shape(
        self,
        group_payload: Dict[str, Any],
        relationship_context: Optional[Dict[str, Any]],
    ) -> bool:
        if not relationship_context:
            return False
        leg_path = relationship_context.get("path")
        if not leg_path:
            return False

        for clause_payload in group_payload.get("clauses") or []:
            if clause_payload.get("type") != "RELATED":
                continue
            subject_path = clause_payload.get("subject")
            operands_empty = not (clause_payload.get("operands") or [])
            if operands_empty and subject_path == leg_path:
                return True
        return False

    def _leg_exists_for_path(
        self,
        path_segments: Sequence[Tuple[str, str]],
        is_inverse_relationship: bool,
    ) -> Exists:
        datatype_name, _terminal_graph_slug, pair_raw = (
            self.path_navigator.build_path_queryset(path_segments)
        )
        if (datatype_name or "").lower() not in [
            "resource-instance",
            "resource-instance-list",
        ]:
            raise ValueError("Relationship leg must end on a resource-instance node")
        if is_inverse_relationship:
            correlated = pair_raw.filter(value=OuterRef("resourceinstanceid"))
        else:
            correlated = pair_raw.filter(
                resourceinstanceid=OuterRef("resourceinstanceid")
            )
        return Exists(correlated)
