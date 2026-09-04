"""
The advanced search clause DSL.

advanced_search.py compiles one payload -- one graph's worth of clauses -- into
a queryset of that graph's resources. A whole search carries a list of them, one
per graph it filters; utils.search is what holds that list.

    advanced_search.py      AdvancedSearchQueryCompiler, the entry point
    payload_validator.py    a payload's shape, checked without the database
    clause_evaluation/      clauses into predicates, one path per subject type
    predicate_building/     a facet row's orm_template into a Q
    registries/             facets, search models, node datatypes
    operand_normalization/  coercing client values, per datatype
    path_navigator.py       traversal along named, directed node paths
"""
