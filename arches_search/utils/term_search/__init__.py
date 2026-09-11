"""
Term matching, and expansion across relationships.

Terms are matched against every indexed text value on a resource -- no node is
named -- and then walked back to the graph being searched across at most two
relationship hops.

That traversal is anonymous: it follows any relationship, in either direction,
ignoring ontology properties. It is deliberately not an advanced search clause,
whose `relationship` is the opposite -- a named node path, an explicit direction,
and a quantifier. Do not read the two as variations of one another.

    matching.py                what a term matches
    relationship_expansion.py  how a match reaches a neighbouring resource
    suggestions.py             term lookup behind the typeahead endpoint
"""
