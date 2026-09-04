"""
Data projected onto search results, beyond a resource's own serialization.

An entry takes the same two shapes a clause subject does, and uses the same
tokens, so one vocabulary covers filtering and projection alike:

    { "type": "NODE", "graph_slug": "person", "node_alias": "height" }
    { "type": "RESOURCE_FIELD", "field": "resource_instance_lifecycle_state" }

They are resolved together and read back split by kind, because the two name
spaces can collide -- a node aliased "principaluser" and the field of the same
name would otherwise fight over one key.

    additional_data.py  what a search asked to project, resolved and formatted
    node_values.py      tile values, annotated through correlated subqueries
    resource_fields.py  the resource's own columns, with labels for relations
"""
