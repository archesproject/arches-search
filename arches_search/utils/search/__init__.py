"""
Search as a callable, independent of any HTTP endpoint.

    from arches_search.utils.search import SearchRequest, execute_search

    response = execute_search(SearchRequest.from_body(body), user)

Callers wanting only the matching queryset -- an export, a map tile -- can use
SearchCompiler directly and skip the projection and pagination above it.

    payload.py     what a search is asked for, and what it returns
    validation.py  the shape of those keys, checked before anything compiles
    compiler.py    payload -> matching resources, one graph at a time
    additional_data/ values carried on each row: node values and
                   resource fields, keyed the way clause subjects are
    sorting.py     ordering, including by a projected column
    aggregation.py grouped counts and metrics over the whole result set
    execution.py   all of the above, in order
"""

from arches_search.utils.search.compiler import SearchCompiler
from arches_search.utils.search.execution import execute_search
from arches_search.utils.search.payload import (
    SearchPayload,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from arches_search.utils.search.validation import (
    validate_advanced_search_queries,
    validate_paging,
    validate_search_payload,
    validate_term_search,
)

__all__ = [
    "SearchCompiler",
    "SearchPayload",
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    "execute_search",
    "validate_advanced_search_queries",
    "validate_paging",
    "validate_search_payload",
    "validate_term_search",
]
