from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.search_aggregation import apply_json_aggregations


class AdvancedSearchAPI(APIBase):
    def post(self, request):

        def run_case(case_name, payload, expected_count=None):
            results_queryset = AdvancedSearchQueryCompiler(payload).compile()
            resource_ids = list(
                results_queryset.values_list("resourceinstanceid", flat=True)
            )
            actual_count = len(resource_ids)
            matches_expected = (
                None if expected_count is None else (actual_count == expected_count)
            )
            return {
                "name": case_name,
                "payload": payload,
                "resource_ids": resource_ids,
                "count": actual_count,
                "expected_count": expected_count,
                "matches_expected": matches_expected,
            }

        if True:

            test_cases = [
                {
                    "name": "DOG — everything (baseline)",
                    "payload": {
                        "graph_slug": "dog",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                    "expected_count": 2,
                },
                {
                    "name": "PERSON — age > 18",
                    "payload": {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "GREATER_THAN",
                                "operands": [{"type": "LITERAL", "value": 18}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                    "expected_count": 2,
                },
                {
                    "name": "PERSON — RESOURCE constraint failure multiple tiles",
                    "payload": {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "first_name"]],
                                "operator": "LIKE",
                                "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                            },
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "last_name"]],
                                "operator": "LIKE",
                                "operands": [{"type": "LITERAL", "value": "FOO"}],
                            },
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                    "expected_count": 0,
                },
                {
                    "name": "PERSON — RESOURCE constraint success multiple tiles",
                    "payload": {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "first_name"]],
                                "operator": "LIKE",
                                "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                            },
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "last_name"]],
                                "operator": "LIKE",
                                "operands": [{"type": "LITERAL", "value": "REAL"}],
                            },
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                    "expected_count": 1,
                },
                {
                    "name": "PERSON — TILE constraint failure (baseline)",
                    "payload": {
                        "graph_slug": "person",
                        "scope": "TILE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "first_name"]],
                                "operator": "LIKE",
                                "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                            },
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "last_name"]],
                                "operator": "LIKE",
                                "operands": [{"type": "LITERAL", "value": "REAL"}],
                            },
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                    "expected_count": 0,
                },
                {
                    "name": "PERSON — TILE constraint success (baseline)",
                    "payload": {
                        "graph_slug": "person",
                        "scope": "TILE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "first_name"]],
                                "operator": "LIKE",
                                "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                            },
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "last_name"]],
                                "operator": "LIKE",
                                "operands": [{"type": "LITERAL", "value": "MOTHER"}],
                            },
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                    "expected_count": 1,
                },
                {
                    "name": "PERSON — fingernail_length <= 50",
                    "payload": {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "fingernail_length"]],
                                "operator": "LESS_THAN_OR_EQUALS",
                                "operands": [{"type": "LITERAL", "value": 50}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                    "expected_count": 2,
                },
                {
                    "name": "PERSON — no age",
                    "payload": {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "HAS_NO_VALUE",
                                "operands": [],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                    "expected_count": 1,
                },
                {
                    "name": "PERSON — no age OR fingernail_length <= 25 OR fingernail_length > 50",
                    "payload": {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "OR",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "HAS_NO_VALUE",
                                "operands": [],
                            },
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "fingernail_length"]],
                                "operator": "LESS_THAN_OR_EQUALS",
                                "operands": [{"type": "LITERAL", "value": 25}],
                            },
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "fingernail_length"]],
                                "operator": "GREATER_THAN",
                                "operands": [{"type": "LITERAL", "value": 50}],
                            },
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                    "expected_count": 3,
                },
                {
                    "name": "PERSON — no age AND fingernail_length <= 22 OR fingernail_length > 50",
                    "payload": {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "OR",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "fingernail_length"]],
                                "operator": "GREATER_THAN",
                                "operands": [{"type": "LITERAL", "value": 50}],
                            }
                        ],
                        "groups": [
                            {
                                "graph_slug": "person",
                                "scope": "RESOURCE",
                                "logic": "AND",
                                "clauses": [
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": [["person", "age"]],
                                        "operator": "HAS_NO_VALUE",
                                        "operands": [],
                                    },
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": [["person", "fingernail_length"]],
                                        "operator": "EQUALS",
                                        "operands": [{"type": "LITERAL", "value": 10}],
                                    },
                                ],
                                "groups": [],
                                "aggregations": [],
                                "relationship": None,
                            },
                        ],
                        "aggregations": [],
                        "relationship": None,
                    },
                    "expected_count": 2,
                },
                # {
                #     "name": "PERSON — HAS_NO_VALUE friends",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_NO_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 1,
                # },
                # {
                #     "name": "PERSON — is some dog's favorite_person",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["dog", "favorite_person"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PERSON — dogs' tail_length >= person's fingernail_length (via favorite_person inverse leg)",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["dog", "tail_length"]],
                #                 "operator": "GREATER_THAN_OR_EQUALS",
                #                 "operands": [
                #                     {
                #                         "type": "PATH",
                #                         "value": [["person", "fingernail_length"]],
                #                     }
                #                 ],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PERSON — dogs' tail_length = person's fingernail_length (via favorite_person inverse leg)",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["dog", "tail_length"]],
                #                 "operator": "EQUALS",
                #                 "operands": [
                #                     {
                #                         "type": "PATH",
                #                         "value": [["person", "fingernail_length"]],
                #                     }
                #                 ],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 1,
                # },
                # {
                #     "name": "PERSON — dogs' tail_length < person's fingernail_length (via favorite_person inverse leg)",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["dog", "tail_length"]],
                #                 "operator": "LESS_THAN",
                #                 "operands": [
                #                     {
                #                         "type": "PATH",
                #                         "value": [["person", "fingernail_length"]],
                #                     }
                #                 ],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 0,
                # },
                # {
                #     "name": "FRIENDS  — ALL friends are < 18",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "LESS_THAN",
                #                         "operands": [{"type": "LITERAL", "value": 18}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 0,
                # },
                # {
                #     "name": "FRIENDS — ALL friends are > 18",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "GREATER_THAN",
                #                         "operands": [{"type": "LITERAL", "value": 18}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "FRIENDS — ANY friends are 22",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "EQUALS",
                #                         "operands": [{"type": "LITERAL", "value": 22}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 1,
                # },
                # {
                #     "name": "PEOPLE - ALL friends have ANY pet dogs that have a tail_length > 10",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [
                #                     {
                #                         "graph_slug": "dog",
                #                         "scope": "RESOURCE",
                #                         "logic": "AND",
                #                         "clauses": [
                #                             {
                #                                 "type": "LITERAL",
                #                                 "quantifier": "ANY",
                #                                 "subject": [["dog", "tail_length"]],
                #                                 "operator": "GREATER_THAN",
                #                                 "operands": [
                #                                     {"type": "LITERAL", "value": 10}
                #                                 ],
                #                             }
                #                         ],
                #                         "groups": [],
                #                         "aggregations": [],
                #                         "relationship": None,
                #                     }
                #                 ],
                #                 "aggregations": [],
                #                 "relationship": {
                #                     "path": [["person", "pets"]],
                #                     "is_inverse": False,
                #                     "traversal_quantifiers": ["ANY"],
                #                 },
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 1,
                # },
                # {
                #     "name": "PEOPLE - ALL friends have ANY pet dogs that have a tail_length < 10",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [
                #                     {
                #                         "graph_slug": "dog",
                #                         "scope": "RESOURCE",
                #                         "logic": "AND",
                #                         "clauses": [
                #                             {
                #                                 "type": "LITERAL",
                #                                 "quantifier": "ANY",
                #                                 "subject": [["dog", "tail_length"]],
                #                                 "operator": "LESS_THAN",
                #                                 "operands": [
                #                                     {"type": "LITERAL", "value": 10}
                #                                 ],
                #                             }
                #                         ],
                #                         "groups": [],
                #                         "aggregations": [],
                #                         "relationship": None,
                #                     }
                #                 ],
                #                 "aggregations": [],
                #                 "relationship": {
                #                     "path": [["person", "pets"]],
                #                     "is_inverse": False,
                #                     "traversal_quantifiers": ["ANY"],
                #                 },
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 0,
                # },
                # {
                #     "name": "PEOPLE - ANY friends that have ANY pet dogs that have a tail_length > 25",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [
                #                     {
                #                         "graph_slug": "dog",
                #                         "scope": "RESOURCE",
                #                         "logic": "AND",
                #                         "clauses": [
                #                             {
                #                                 "type": "LITERAL",
                #                                 "quantifier": "ANY",
                #                                 "subject": [["dog", "tail_length"]],
                #                                 "operator": "GREATER_THAN",
                #                                 "operands": [
                #                                     {"type": "LITERAL", "value": 25}
                #                                 ],
                #                             }
                #                         ],
                #                         "groups": [],
                #                         "aggregations": [],
                #                         "relationship": None,
                #                     }
                #                 ],
                #                 "aggregations": [],
                #                 "relationship": {
                #                     "path": [["person", "pets"]],
                #                     "is_inverse": False,
                #                     "traversal_quantifiers": ["ANY"],
                #                 },
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PEOPLE - ANY friends who have NO pet dogs that have a tail_length = 999",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [
                #                     {
                #                         "graph_slug": "dog",
                #                         "scope": "RESOURCE",
                #                         "logic": "AND",
                #                         "clauses": [
                #                             {
                #                                 "type": "LITERAL",
                #                                 "quantifier": "ANY",
                #                                 "subject": [["dog", "tail_length"]],
                #                                 "operator": "EQUALS",
                #                                 "operands": [
                #                                     {"type": "LITERAL", "value": 999}
                #                                 ],
                #                             }
                #                         ],
                #                         "groups": [],
                #                         "aggregations": [],
                #                         "relationship": None,
                #                     }
                #                 ],
                #                 "aggregations": [],
                #                 "relationship": {
                #                     "path": [["person", "pets"]],
                #                     "is_inverse": False,
                #                     "traversal_quantifiers": ["NONE"],
                #                 },
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 0,
                # },
                # {
                #     "name": "PEOPLE - ANY friends who have NO pet dogs that have a tail_length = 25",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [
                #                     {
                #                         "graph_slug": "dog",
                #                         "scope": "RESOURCE",
                #                         "logic": "AND",
                #                         "clauses": [
                #                             {
                #                                 "type": "LITERAL",
                #                                 "quantifier": "ANY",
                #                                 "subject": [["dog", "tail_length"]],
                #                                 "operator": "EQUALS",
                #                                 "operands": [
                #                                     {"type": "LITERAL", "value": 25}
                #                                 ],
                #                             }
                #                         ],
                #                         "groups": [],
                #                         "aggregations": [],
                #                         "relationship": None,
                #                     }
                #                 ],
                #                 "aggregations": [],
                #                 "relationship": {
                #                     "path": [["person", "pets"]],
                #                     "is_inverse": False,
                #                     "traversal_quantifiers": ["NONE"],
                #                 },
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PERSON — ANY friends (no inner filters) ≈ HAS_ANY_VALUE friends",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PERSON — NONE friends (no inner filters) ≈ HAS_NO_VALUE friends",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["NONE"],
                #         },
                #     },
                #     "expected_count": 1,
                # },
                # {
                #     "name": "PERSON — ALL friends (no inner filters) => must have ≥1 friend",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PERSON — relationship ANY (2-hop): ANY friends' pets have tail_length > 10",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["dog", "tail_length"]],
                #                         "operator": "GREATER_THAN",
                #                         "operands": [{"type": "LITERAL", "value": 10}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"], ["person", "pets"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PERSON — inverse friends: is someone else’s friend (ANY, no inner filters)",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PERSON — relationship ANY (favorite_person forward leg)",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PERSON — relationship NONE (favorite_person inverse leg)",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["NONE"],
                #         },
                #     },
                #     "expected_count": 1,  # assuming only 2 of 3 people are some dog's favorite_person
                # },
                # {
                #     "name": "PERSON — TILE constraint OR success",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "TILE",
                #         "logic": "OR",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "first_name"]],
                #                 "operator": "LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                #             },
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "last_name"]],
                #                 "operator": "LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "MOTHER"}],
                #             },
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 1,
                # },
                # {
                #     "name": "PERSON — RESOURCE wrong-graph subject should yield 0",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["dog", "tail_length"]],
                #                 "operator": "GREATER_THAN",
                #                 "operands": [{"type": "LITERAL", "value": 0}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 0,
                # },
                # {
                #     "name": "PERSON — fingernail_length = 10 (boundary equality)",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "fingernail_length"]],
                #                 "operator": "EQUALS",
                #                 "operands": [{"type": "LITERAL", "value": 10}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 1,
                # },
                # {
                #     "name": "PERSON — TILE nested AND inside TILE (co-occurrence still enforced)",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "TILE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "first_name"]],
                #                 "operator": "LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "TILE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "last_name"]],
                #                         "operator": "LIKE",
                #                         "operands": [
                #                             {"type": "LITERAL", "value": "MOTHER"}
                #                         ],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 1,
                # },
                # {
                #     "name": "PERSON — friends (ALL) AND top-level literal on anchor",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "fingernail_length"]],
                #                 "operator": "LESS_THAN_OR_EQUALS",
                #                 "operands": [{"type": "LITERAL", "value": 50}],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "GREATER_THAN",
                #                         "operands": [{"type": "LITERAL", "value": 18}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PERSON — HAS_ANY_VALUE pets",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "pets"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 2,  # B, C
                # },
                # {
                #     "name": "PERSON — HAS_NO_VALUE pets",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "pets"]],
                #                 "operator": "HAS_NO_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 1,  # A
                # },
                # {
                #     "name": "PERSON — mother HAS_NO_VALUE",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "mother"]],
                #                 "operator": "HAS_NO_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 2,  # B, C
                # },
                # {
                #     "name": "PERSON — mother HAS_ANY_VALUE",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "mother"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 1,  # A
                # },
                # {
                #     "name": "PERSON — TILE AND success (same alias tile)",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "TILE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "first_name"]],
                #                 "operator": "LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                #             },
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "last_name"]],
                #                 "operator": "LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "MOTHER"}],
                #             },
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 1,  # B (same alias tile)
                # },
                # {
                #     "name": "PERSON — ANY friends age > 23",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "GREATER_THAN",
                #                         "operands": [{"type": "LITERAL", "value": 23}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,  # A (friend C=24), B (friend C=24)
                # },
                # {
                #     "name": "PERSON — ANY friends age > 100",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "friends"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "GREATER_THAN",
                #                         "operands": [{"type": "LITERAL", "value": 100}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 0,
                # },
                # {
                #     "name": "PERSON — NONE friends age >= 30",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "GREATER_THAN_OR_EQUALS",
                #                         "operands": [{"type": "LITERAL", "value": 30}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["NONE"],
                #         },
                #     },
                #     "expected_count": 2,  # A, B (C has 0 friends ⇒ non-vacuous NONE = false)
                # },
                # {
                #     "name": "PERSON — ALL friends age >= 24",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "GREATER_THAN_OR_EQUALS",
                #                         "operands": [{"type": "LITERAL", "value": 24}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 1,  # A (friend C=24); B fails; C has 0 friends ⇒ ALL requires ≥1
                # },
                # {
                #     "name": "PERSON — ALL friends have ANY pets",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "pets"]],
                #                         "operator": "HAS_ANY_VALUE",
                #                         "operands": [],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 1,  # Only A (C has pets); B fails; C has 0 friends
                # },
                # {
                #     "name": "PERSON — ALL friends have NO pets",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "pets"]],
                #                         "operator": "HAS_NO_VALUE",
                #                         "operands": [],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 0,  # A's friend C has pets; B has friend C with pets; C has 0 friends
                # },
                # {
                #     "name": "PERSON — ANY friends have NO pets",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "pets"]],
                #                         "operator": "HAS_NO_VALUE",
                #                         "operands": [],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 1,  # B (friend A has no pets)
                # },
                # {
                #     "name": "PERSON — ANY friends who are some dog's favorite_person",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": {
                #                     "path": [["dog", "favorite_person"]],
                #                     "is_inverse": True,
                #                     "traversal_quantifiers": ["ANY"],
                #                 },
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,  # A (friend C favored by Dog B), B (friend A favored by Dog A)
                # },
                # {
                #     "name": "PERSON — (age > 23) OR (is some dog's favorite_person)",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "OR",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "age"]],
                #                 "operator": "GREATER_THAN",
                #                 "operands": [{"type": "LITERAL", "value": 23}],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "RELATED",
                #                         "quantifier": "ANY",
                #                         "subject": [["dog", "favorite_person"]],
                #                         "operator": "HAS_ANY_VALUE",
                #                         "operands": [],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": {
                #                     "path": [["dog", "favorite_person"]],
                #                     "is_inverse": True,
                #                     "traversal_quantifiers": ["ANY"],
                #                 },
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 2,  # A, C
                # },
                # {
                #     "name": "PERSON — inverse favorite_person ANY, dog's tail_length < 100",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["dog", "favorite_person"]],
                #                 "operator": "HAS_ANY_VALUE",
                #                 "operands": [],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["dog", "tail_length"]],
                #                         "operator": "LESS_THAN",
                #                         "operands": [{"type": "LITERAL", "value": 100}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 1,  # A
                # },
                # {
                #     "name": "PERSON — ALL inverse favorite_person: dogs' tail_length >= person's fingernail_length",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "RELATED",
                #                 "quantifier": "ANY",
                #                 "subject": [["dog", "tail_length"]],
                #                 "operator": "GREATER_THAN_OR_EQUALS",
                #                 "operands": [
                #                     {
                #                         "type": "PATH",
                #                         "value": [["person", "fingernail_length"]],
                #                     }
                #                 ],
                #             }
                #         ],
                #         "groups": [
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 2,  # A(25>=25), C(999>=55); B has no liking dogs ⇒ fails ALL
                # },
                # {
                #     "name": "DOG — tail_length >= 900",
                #     "payload": {
                #         "graph_slug": "dog",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["dog", "tail_length"]],
                #                 "operator": "GREATER_THAN_OR_EQUALS",
                #                 "operands": [{"type": "LITERAL", "value": 900}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 1,  # Dog B
                # },
                # {
                #     "name": "DOG — favorite_person age > 23",
                #     "payload": {
                #         "graph_slug": "dog",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "GREATER_THAN",
                #                         "operands": [{"type": "LITERAL", "value": 23}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 1,  # Dog B (C=24)
                # },
                # {
                #     "name": "DOG — favorite_person HAS_NO_VALUE friends",
                #     "payload": {
                #         "graph_slug": "dog",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "friends"]],
                #                         "operator": "HAS_NO_VALUE",
                #                         "operands": [],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 1,  # Dog B (favorite C has no friends)
                # },
                # {
                #     "name": "DOG — ANY owners via pets (inverse)",
                #     "payload": {
                #         "graph_slug": "dog",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "pets"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,  # Both dogs are someone's pet
                # },
                # {
                #     "name": "DOG — NONE owners via pets (inverse)",
                #     "payload": {
                #         "graph_slug": "dog",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "pets"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["NONE"],
                #         },
                #     },
                #     "expected_count": 0,
                # },
                # {
                #     "name": "DOG — ALL owners age > 20 (via pets inverse)",
                #     "payload": {
                #         "graph_slug": "dog",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "GREATER_THAN",
                #                         "operands": [{"type": "LITERAL", "value": 20}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "pets"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ALL"],
                #         },
                #     },
                #     "expected_count": 1,  # Dog B (owner C=24). Dog A owner B age=null ⇒ fails.
                # },
                # {
                #     "name": "DOG — owner's ANY friend age == 22",
                #     "payload": {
                #         "graph_slug": "dog",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [],
                #                 "groups": [
                #                     {
                #                         "graph_slug": "person",
                #                         "scope": "RESOURCE",
                #                         "logic": "AND",
                #                         "clauses": [
                #                             {
                #                                 "type": "LITERAL",
                #                                 "quantifier": "ANY",
                #                                 "subject": [["person", "age"]],
                #                                 "operator": "EQUALS",
                #                                 "operands": [
                #                                     {"type": "LITERAL", "value": 22}
                #                                 ],
                #                             }
                #                         ],
                #                         "groups": [],
                #                         "aggregations": [],
                #                         "relationship": None,
                #                     }
                #                 ],
                #                 "aggregations": [],
                #                 "relationship": {
                #                     "path": [["person", "friends"]],
                #                     "is_inverse": False,
                #                     "traversal_quantifiers": ["ANY"],
                #                 },
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "pets"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 1,  # Dog A via owner B → friend A(22)
                # },
                # {
                #     "name": "PERSON — TILE LIKE exact punctuation",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "TILE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "last_name"]],
                #                 "operator": "LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "FRIEND!"}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 1,  # C
                # },
                # {
                #     "name": "PERSON — conflicting numeric constraints at RESOURCE scope",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "fingernail_length"]],
                #                 "operator": "GREATER_THAN",
                #                 "operands": [{"type": "LITERAL", "value": 50}],
                #             },
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "fingernail_length"]],
                #                 "operator": "LESS_THAN_OR_EQUALS",
                #                 "operands": [{"type": "LITERAL", "value": 50}],
                #             },
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 0,
                # },
                # {
                #     "name": "PERSON — fingernail_length <= 10 OR >= 999",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "OR",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "fingernail_length"]],
                #                 "operator": "LESS_THAN_OR_EQUALS",
                #                 "operands": [{"type": "LITERAL", "value": 10}],
                #             },
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "fingernail_length"]],
                #                 "operator": "GREATER_THAN_OR_EQUALS",
                #                 "operands": [{"type": "LITERAL", "value": 999}],
                #             },
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 1,  # B
                # },
                # {
                #     "name": "PERSON — ANY friends with HAS_NO_VALUE age",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "HAS_NO_VALUE",
                #                         "operands": [],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 0,  # A's friend C has age; B's friends A/C have age; C has no friends
                # },
                # {
                #     "name": "PERSON — NONE friends with HAS_NO_VALUE age",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "person",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["person", "age"]],
                #                         "operator": "HAS_NO_VALUE",
                #                         "operands": [],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             }
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["person", "friends"]],
                #             "is_inverse": False,
                #             "traversal_quantifiers": ["NONE"],
                #         },
                #     },
                #     "expected_count": 2,  # A, B (C has 0 friends ⇒ non-vacuous NONE = false)
                # },
                # # ----- new_test_cases -----
                # {
                #     "name": "PERSON — ALL TILE NOT LIKE on first_name",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "TILE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ALL",
                #                 "subject": [["person", "first_name"]],
                #                 "operator": "NOT_LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 2,  # assuming 1 'INCOGNITO' and 2 others
                # },
                # {
                #     "name": "PERSON — ANY TILE NOT LIKE on first_name",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "TILE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "first_name"]],
                #                 "operator": "NOT_LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 3,  # assuming 1 'INCOGNITO' and 2 others
                # },
                # {
                #     "name": "PERSON — NO TILE LIKE on first_name",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "TILE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "NONE",
                #                 "subject": [["person", "first_name"]],
                #                 "operator": "LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 2,  # assuming 1 'INCOGNITO' and 2 others
                # },
                # {
                #     "name": "PERSON — ALL TILE NOT LIKE on first_name",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ALL",
                #                 "subject": [["person", "first_name"]],
                #                 "operator": "NOT_LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 2,  # assuming 1 'INCOGNITO' and 2 others
                # },
                # {
                #     "name": "PERSON — ANY TILE NOT LIKE on first_name",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "ANY",
                #                 "subject": [["person", "first_name"]],
                #                 "operator": "NOT_LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 3,  # assuming 1 'INCOGNITO' and 2 others
                # },
                # {
                #     "name": "PERSON — NO TILE LIKE on first_name",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "quantifier": "NONE",
                #                 "subject": [["person", "first_name"]],
                #                 "operator": "LIKE",
                #                 "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 2,  # assuming 1 'INCOGNITO' and 2 others
                # },
                # {
                #     "name": "PERSON — NOT LIKE on name at RESOURCE scope",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "AND",
                #         "clauses": [
                #             {
                #                 "type": "LITERAL",
                #                 "subject": [["person", "first_name"]],
                #                 "operator": "NOT_LIKE",
                #                 "quantifier": "ALL",
                #                 "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                #             }
                #         ],
                #         "groups": [],
                #         "aggregations": [],
                #         "relationship": None,
                #     },
                #     "expected_count": 2,
                # },
                # {
                #     "name": "PERSON — favorite_person inverse ANY, dog's tail_length == 25 OR 999",
                #     "payload": {
                #         "graph_slug": "person",
                #         "scope": "RESOURCE",
                #         "logic": "OR",
                #         "clauses": [],
                #         "groups": [
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["dog", "tail_length"]],
                #                         "operator": "EQUALS",
                #                         "operands": [{"type": "LITERAL", "value": 25}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             },
                #             {
                #                 "graph_slug": "dog",
                #                 "scope": "RESOURCE",
                #                 "logic": "AND",
                #                 "clauses": [
                #                     {
                #                         "type": "LITERAL",
                #                         "quantifier": "ANY",
                #                         "subject": [["dog", "tail_length"]],
                #                         "operator": "EQUALS",
                #                         "operands": [{"type": "LITERAL", "value": 999}],
                #                     }
                #                 ],
                #                 "groups": [],
                #                 "aggregations": [],
                #                 "relationship": None,
                #             },
                #         ],
                #         "aggregations": [],
                #         "relationship": {
                #             "path": [["dog", "favorite_person"]],
                #             "is_inverse": True,
                #             "traversal_quantifiers": ["ANY"],
                #         },
                #     },
                #     "expected_count": 2,
                # },
            ]

            case_results = [
                run_case(tc["name"], tc["payload"], tc.get("expected_count"))
                for tc in test_cases
            ]
            return JSONResponse({"cases": case_results, "aggregations": {}})
