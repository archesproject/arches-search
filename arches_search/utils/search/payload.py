"""
What a search is asked for, and what it returns.

SearchPayload is the filtering half -- which resource models, the term search,
and the per-graph advanced search payloads. SearchRequest adds the presentation
half: the columns, ordering, aggregations and page a caller wants back.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from django.db.models import QuerySet

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20


@dataclass(frozen=True)
class SearchPayload:
    # Which resource models to search. A graph named here with no matching
    # advanced_search_queries entry is returned unfiltered.
    graph_slugs: Optional[List[str]]
    # Terms matched against every indexed text value on a resource, optionally
    # expanded across relationships. This is the only filter that reaches
    # outside the graph being searched; everything else is a clause.
    term_search: Optional[Dict[str, Any]]
    # One advanced search payload per graph being filtered. Each entry names the
    # resource model it returns in its own graph_slug.
    advanced_search_queries: Optional[List[Dict[str, Any]]]

    @classmethod
    def from_body(cls, body: Dict[str, Any]) -> "SearchPayload":
        return cls(
            graph_slugs=body.get("graph_slugs") or None,
            term_search=body.get("term_search"),
            advanced_search_queries=body.get("advanced_search_queries"),
        )


@dataclass(frozen=True)
class SearchResult:
    """
    What the compiler found, before any projection or paging.

    The two counts differ on purpose. all_resource_count spans every active
    graph, so a client can show what selecting another resource model would
    get; scoped_count covers only the graphs named in graph_slugs, which is
    what `results` contains and what pagination is measured against.
    """

    results: QuerySet
    resource_type_counts: List[Dict[str, Any]]
    all_resource_count: int
    scoped_count: int


@dataclass(frozen=True)
class SearchRequest:
    """
    A whole search, filtering and presentation together.

    Built straight from a request body by the API, or constructed directly by
    anything running in-process that wants the same results without a round trip
    through HTTP.
    """

    payload: SearchPayload
    additional_data: Optional[List[Dict[str, str]]] = None
    sort: Optional[List[Dict[str, Any]]] = None
    aggregations: Optional[List[Dict[str, Any]]] = None
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE

    @classmethod
    def from_body(cls, body: Dict[str, Any]) -> "SearchRequest":
        return cls(
            payload=SearchPayload.from_body(body),
            additional_data=body.get("additional_data"),
            sort=body.get("sort"),
            aggregations=body.get("aggregations"),
            page=body.get("page", DEFAULT_PAGE),
            page_size=body.get("page_size", DEFAULT_PAGE_SIZE),
        )


@dataclass(frozen=True)
class SearchResponse:
    """One page of results, with the counts a facet panel needs."""

    resources: List[Dict[str, Any]]
    pagination: Dict[str, Any]
    resource_type_counts: List[Dict[str, Any]]
    all_resource_count: int
    aggregations: Dict[str, Any] = field(default_factory=dict)

    def serialize(self) -> Dict[str, Any]:
        return {
            "resources": self.resources,
            "pagination": self.pagination,
            "aggregations": self.aggregations,
            "resource_type_counts": self.resource_type_counts,
            "all_resource_count": self.all_resource_count,
        }
