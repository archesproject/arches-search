"""
ResourceInstance's own columns, as a queryable surface.

Which fields exist is derived from the model rather than listed anywhere, and
each is mapped to an operator vocabulary by its Django field class -- so a
column added to core becomes filterable, sortable and groupable with no change
here.

One registry feeds four consumers, which is what keeps them from drifting apart:

    field_registry.py  the registry itself
    resolver.py        field + operator + operands -> a Q, for clause filtering
    grouping.py        field -> a group-by expression, for aggregation
    metadata.py        the vocabulary, for a client building a filter UI
"""
