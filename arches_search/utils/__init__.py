"""
How these pieces fit together.

`search/` runs a search end to end. Everything beside it is something a search
can be asked to filter by:

    search/                 compile, project, order, paginate, aggregate.

    advanced_search/        the clause DSL. One payload per graph, carrying
                            clauses whose subjects address tile values (NODE,
                            SEARCH_MODELS) or resource columns (RESOURCE_FIELD).
    term_search/            matching terms anywhere on a resource, then
                            expanding across relationships. The only filter that
                            reaches outside the graph being searched, which is
                            why it is a payload key rather than a clause.
    resource_field_search/  which columns on ResourceInstance are queryable, and
                            how each becomes a predicate.

    extension_discovery.py  extensions declared by installed apps
    geo_utils.py            geometry helpers, shared with callers

Dependencies run one way: search -> {advanced_search, term_search,
resource_field_search}. Nothing under those reaches back into search.
"""
