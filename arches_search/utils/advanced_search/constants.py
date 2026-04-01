# Group / clause structure
LOGIC_AND = "AND"
LOGIC_OR = "OR"

SCOPE_RESOURCE = "RESOURCE"
SCOPE_TILE = "TILE"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"

# Quantifiers used in clauses and relationship traversals
QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

# Internal context used by GroupCompiler to distinguish the anchor side from
# the child side when compiling nested groups that contain no relationship.
CONTEXT_ANCHOR = "ANCHOR"
CONTEXT_CHILD = "CHILD"
