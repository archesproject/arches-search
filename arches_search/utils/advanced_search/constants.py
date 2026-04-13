# Group / clause structure
LOGIC_AND = "AND"
LOGIC_OR = "OR"

SCOPE_RESOURCE = "RESOURCE"
SCOPE_TILE = "TILE"

CLAUSE_TYPE_LITERAL = "LITERAL"
CLAUSE_TYPE_RELATED = "RELATED"

SUBJECT_TYPE_NODE = "NODE"
SUBJECT_TYPE_SEARCH_MODELS = "SEARCH_MODELS"

# Operand payload types
OPERAND_TYPE_LITERAL = "LITERAL"
OPERAND_TYPE_PATH = "PATH"
OPERAND_TYPE_GEO_LITERAL = "GEO_LITERAL"

# Quantifiers used in clauses and relationship traversals
QUANTIFIER_ANY = "ANY"
QUANTIFIER_ALL = "ALL"
QUANTIFIER_NONE = "NONE"

# Aggregate predicate kinds
AGGREGATE_KIND_SET_SUPERSET = "set_superset"
AGGREGATE_KIND_SET_EQUAL = "set_equal"

# Datatypes that represent resource-to-resource links rather than scalar values.
TERMINAL_RESOURCE_DATATYPES = {"resource-instance", "resource-instance-list"}
