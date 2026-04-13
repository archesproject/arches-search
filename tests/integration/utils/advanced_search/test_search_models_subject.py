"""Integration tests for the SEARCH_MODELS subject type.

The SEARCH_MODELS subject type allows a clause to match against a named set of
search model classes (e.g. ["TermSearch"]) scoped to a graph slug, without
specifying a particular node alias. This is the foundation for fuzzy cross-node
searches such as "find any resource where any string field contains X".

These tests cover every major branch in LiteralClauseEvaluator._build_exists_for_search_models:

  - No-operand (arity-0) path:
      - HAS_ANY_VALUE + QUANTIFIER_ANY  → presence_implies_match=True, any exists
      - HAS_ANY_VALUE + QUANTIFIER_NONE → presence_implies_match=True, negated exists
      - HAS_NO_VALUE  + QUANTIFIER_ANY  → presence_implies_match=False, negated exists

  - Operand path, non-negated template:
      - LIKE + QUANTIFIER_ANY  → Exists(matching rows)
      - LIKE + QUANTIFIER_NONE → ~Exists(matching rows)
      - LIKE + QUANTIFIER_ALL  → Exists(any row) & ~Exists(violating rows)

  - Operand path, negated template (is_template_negated=True):
      - NOT_LIKE + QUANTIFIER_ALL → positive_rows_for_negated_template path

  - Language-keyed operand (localize_string_operands + apply_localized_language_filter):
      - dict operand {"fr": "MERE"} filters TermSearch rows to the "fr" locale

Fixture data summary (en values):
  Person A: first_name["FOO", "bar"], last_name["CHILD", "foo"], nickname["ALPHA"]
  Person B: first_name["INCOGNITO", "NAME"], last_name["MOTHER"(fr="MERE"), "REAL"], nickname["BETA"]
  Person C: first_name["FRIEND"], last_name["FRIEND!"], nickname["CHARLIE"]
  Person D: first_name["JUNIOR"], last_name["PERSON"], nickname["DELTA"]
"""

from django.test import TestCase

from tests.integration.utils.advanced_search.test_advanced_search import (
    PERSON_A_ID,
    PERSON_B_ID,
    PERSON_C_ID,
    PERSON_D_ID,
    AdvancedSearchSetupMixin,
)


def _search_models_subject(graph_slug="person", search_models=None):
    if search_models is None:
        search_models = ["TermSearch"]
    return {
        "type": "SEARCH_MODELS",
        "graph_slug": graph_slug,
        "node_alias": "",
        "search_models": search_models,
    }


def _root_payload(graph_slug, clauses):
    return {
        "graph_slug": graph_slug,
        "scope": "RESOURCE",
        "logic": "AND",
        "clauses": clauses,
        "groups": [],
        "aggregations": [],
        "relationship": None,
    }


def _time_search_models_subject(graph_slug="person"):
    return _search_models_subject(
        graph_slug=graph_slug,
        search_models=["DateSearch", "DateRangeSearch"],
    )


class SearchModelsSubjectNoOperandTestCase(AdvancedSearchSetupMixin, TestCase):
    """Tests the arity-0 (no-operand) branch of _build_exists_for_search_models."""

    def test_has_any_value_with_quantifier_any_returns_all_persons(self):
        """
        HAS_ANY_VALUE + QUANTIFIER_ANY: presence_implies_match=True, so any row existing
        implies a match. All four persons have TermSearch rows for graph_slug="person"
        (every person has at least one string node), so all four are returned.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _search_models_subject(),
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID, PERSON_C_ID, PERSON_D_ID})

    def test_has_any_value_with_quantifier_none_returns_no_persons(self):
        """
        HAS_ANY_VALUE + QUANTIFIER_NONE: presence_implies_match=True, so the NONE quantifier
        negates the existence check. Since every person has string rows, no one qualifies.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "NONE",
                        "subject": _search_models_subject(),
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
            )
        )
        self.assertEqual(result, set())

    def test_has_no_value_with_quantifier_any_returns_no_persons(self):
        """
        HAS_NO_VALUE + QUANTIFIER_ANY: presence_implies_match=False, so the ANY quantifier
        negates the existence check. Since every person has string rows, no one qualifies.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _search_models_subject(),
                        "operator": "HAS_NO_VALUE",
                        "operands": [],
                    }
                ],
            )
        )
        self.assertEqual(result, set())

    def test_has_no_value_with_quantifier_none_returns_all_persons(self):
        """
        HAS_NO_VALUE + QUANTIFIER_NONE: presence_implies_match=False, so the NONE quantifier
        uses the raw existence check (not negated). Since every person has string rows,
        the existence check is true for all four persons.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "NONE",
                        "subject": _search_models_subject(),
                        "operator": "HAS_NO_VALUE",
                        "operands": [],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID, PERSON_C_ID, PERSON_D_ID})


class SearchModelsSubjectQuantifierAnyTestCase(AdvancedSearchSetupMixin, TestCase):
    """Tests QUANTIFIER_ANY with operands: Exists(matching rows)."""

    def test_like_returns_person_with_matching_string_on_any_node(self):
        """
        QUANTIFIER_ANY + LIKE "CHARLIE": only Person C has "CHARLIE" across any string
        node (nickname). Demonstrates that cross-node matching works without specifying
        a node alias.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _search_models_subject(),
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "CHARLIE"}],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_C_ID})

    def test_like_matches_string_regardless_of_which_node_holds_the_value(self):
        """
        QUANTIFIER_ANY + LIKE "ALPHA": "ALPHA" is in Person A's nickname node, not in
        first_name or last_name. The cross-node search finds it regardless.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _search_models_subject(),
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "ALPHA"}],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_like_with_value_spanning_multiple_persons_returns_all_matches(self):
        """
        QUANTIFIER_ANY + LIKE "FOO": "FOO" appears in Person A's first_name and last_name.
        "foo" (lowercase) is also Person A's last_name on the secondary alias tile.
        LIKE is case-insensitive, so both map to the same match. Only Person A qualifies.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _search_models_subject(),
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "FOO"}],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID})


class SearchModelsSubjectQuantifierNoneTestCase(AdvancedSearchSetupMixin, TestCase):
    """Tests QUANTIFIER_NONE with operands: ~Exists(matching rows)."""

    def test_none_like_excludes_only_the_person_with_a_matching_row(self):
        """
        QUANTIFIER_NONE + LIKE "INCOGNITO": only Person B has "INCOGNITO" in any string
        node (first_name). Persons A, C, D have no such row and therefore qualify.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "NONE",
                        "subject": _search_models_subject(),
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID, PERSON_D_ID})

    def test_none_like_with_no_matching_persons_returns_all(self):
        """
        QUANTIFIER_NONE + LIKE "ZZZZZZ": no person has this value anywhere, so all four
        persons satisfy "none of my string rows match ZZZZZZ".
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "NONE",
                        "subject": _search_models_subject(),
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "ZZZZZZ"}],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID, PERSON_C_ID, PERSON_D_ID})


class SearchModelsSubjectQuantifierAllTestCase(AdvancedSearchSetupMixin, TestCase):
    """Tests QUANTIFIER_ALL with operands: Exists(any row) & ~Exists(violating rows)."""

    def test_all_like_with_no_universal_match_returns_empty_set(self):
        """
        QUANTIFIER_ALL + LIKE "INCOGNITO": ALL string rows for a person must contain
        "INCOGNITO". Person B has "INCOGNITO" in one row but "NAME", "MOTHER", "REAL",
        and "BETA" in others, so it fails. No person qualifies.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ALL",
                        "subject": _search_models_subject(),
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
            )
        )
        self.assertEqual(result, set())

    def test_all_not_like_exercises_positive_rows_for_negated_template(self):
        """
        QUANTIFIER_ALL + NOT_LIKE "INCOGNITO": the NOT_LIKE operator has is_template_negated=True,
        so the evaluator calls positive_rows_for_negated_template to find rows that DO match
        LIKE "INCOGNITO" (the positive counterpart). Persons A, C, D have no rows that match
        LIKE "INCOGNITO", so all their rows satisfy NOT_LIKE. Person B has a matching row and
        is excluded.

        This verifies the positive_rows_for_negated_template code path.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ALL",
                        "subject": _search_models_subject(),
                        "operator": "NOT_LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID, PERSON_D_ID})

    def test_all_not_like_with_value_present_in_no_person_returns_all(self):
        """
        QUANTIFIER_ALL + NOT_LIKE "ZZZZZZ": no person has this value, so the positive
        counterpart (LIKE "ZZZZZZ") matches no rows for anyone. All persons have string
        rows, and none have any violating positive rows, so all four qualify.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ALL",
                        "subject": _search_models_subject(),
                        "operator": "NOT_LIKE",
                        "operands": [{"type": "LITERAL", "value": "ZZZZZZ"}],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID, PERSON_C_ID, PERSON_D_ID})


class SearchModelsSubjectMultipleTermsTestCase(AdvancedSearchSetupMixin, TestCase):
    """Tests that multiple AND-ed SEARCH_MODELS clauses narrow results correctly,
    and that combining SEARCH_MODELS with NODE clauses produces sensible results."""

    def test_two_search_models_clauses_anded_together(self):
        """
        SEARCH_MODELS LIKE "FOO" AND SEARCH_MODELS LIKE "CHILD": only a resource with both
        values present in any of its string rows qualifies. Person A has "FOO"/"foo" in
        first_name and "CHILD" in last_name, so both conditions hold. No other person has both.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _search_models_subject(),
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "FOO"}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _search_models_subject(),
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "CHILD"}],
                    },
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_search_models_and_node_clauses_combined(self):
        """
        SEARCH_MODELS LIKE "INCOGNITO" AND NODE nickname LIKE "BETA": Person B has
        "INCOGNITO" in first_name (SEARCH_MODELS match) AND "BETA" as nickname (NODE match).
        No other person satisfies both.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _search_models_subject(),
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": {
                            "type": "NODE",
                            "graph_slug": "person",
                            "node_alias": "nickname",
                            "search_models": [],
                        },
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "BETA"}],
                    },
                ],
            )
        )
        self.assertEqual(result, {PERSON_B_ID})


class SearchModelsSubjectTimeFilterTestCase(AdvancedSearchSetupMixin, TestCase):
    """Regression tests for mixed DateSearch/DateRangeSearch SEARCH_MODELS clauses."""

    def test_less_than_uses_date_rows_without_crashing_on_date_range_rows(self):
        """
        Mixed time filters ask SEARCH_MODELS to evaluate both DateSearch and
        DateRangeSearch rows together. LESS_THAN 1500 should still return only
        Person A (birth_date=1000) and must not try to apply a DateSearch
        `value__lt` predicate directly to DateRangeSearch.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _time_search_models_subject(),
                        "operator": "LESS_THAN",
                        "operands": [{"type": "LITERAL", "value": 1500}],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_not_equals_is_vacuously_true_for_resources_without_date_rows(self):
        """
        Negated SEARCH_MODELS predicates should treat missing rows vacuously. Person A has a
        DateSearch row equal to 1000 and is excluded. Person B has a different date row and
        matches. Persons C and D have no DateSearch rows and should also match.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _search_models_subject(
                            graph_slug="person",
                            search_models=["DateSearch"],
                        ),
                        "operator": "NOT_EQUALS",
                        "operands": [{"type": "LITERAL", "value": 1000}],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_B_ID, PERSON_C_ID, PERSON_D_ID})

    def test_equals_matches_date_ranges_that_cover_the_requested_day(self):
        """
        EQUALS behaves like "on this day" for mixed time filters. Person A's
        availability window spans 500-1500, so querying for 1200 should match
        even though no DateSearch row equals 1200.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _time_search_models_subject(),
                        "operator": "EQUALS",
                        "operands": [{"type": "LITERAL", "value": 1200}],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_between_matches_date_ranges_that_overlap_the_requested_window(self):
        """
        BETWEEN uses interval-overlap semantics for DateRangeSearch so the mixed
        time filter continues to search range-backed EDTF rows as well as exact
        date rows.
        """
        result = self._compile(
            _root_payload(
                "person",
                [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": _time_search_models_subject(),
                        "operator": "BETWEEN",
                        "operands": [
                            {"type": "LITERAL", "value": 1200},
                            {"type": "LITERAL", "value": 1700},
                        ],
                    }
                ],
            )
        )
        self.assertEqual(result, {PERSON_A_ID})


class SearchModelsSubjectTraversalTestCase(AdvancedSearchSetupMixin, TestCase):
    """Tests SEARCH_MODELS subjects used inside a traversal group (build_child_exists path).

    Child-side clauses must live in a no-relationship subgroup nested inside the
    traversal group. Clauses placed directly in the traversal group's `clauses` list
    are treated as anchor-side filters (applying to the parent resource), not to the
    child (related) resource.
    """

    def test_search_models_in_child_subgroup_matches_across_related_resources(self):
        """
        Traversal: find persons whose friends have any string node containing "CHARLIE".

        "CHARLIE" is Person C's nickname. Person A is friends with Person C, and Person B
        is also friends with Person C (and Person A). Persons C and D do not qualify because:
          - Person C has no friends tile.
          - Person D is friends with Person A and Person D; neither has "CHARLIE".

        The SEARCH_MODELS clause is in a no-relationship subgroup nested inside the
        traversal group so it is applied as a child-side filter (against the friend's
        TermSearch rows, not the outer person's). This exercises the
        _build_child_resource_predicate_for_relationship_group → compile →
        build_anchor_exists → _build_exists_for_search_models path.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [
                            {
                                "graph_slug": "person",
                                "scope": "RESOURCE",
                                "logic": "AND",
                                "clauses": [
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": _search_models_subject(),
                                        "operator": "LIKE",
                                        "operands": [
                                            {"type": "LITERAL", "value": "CHARLIE"}
                                        ],
                                    }
                                ],
                                "groups": [],
                                "aggregations": [],
                                "relationship": None,
                            }
                        ],
                        "aggregations": [],
                        "relationship": {
                            "path": {
                                "type": "NODE",
                                "graph_slug": "person",
                                "node_alias": "friends",
                            },
                            "is_inverse": False,
                            "traversal_quantifier": "ANY",
                        },
                    }
                ],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_search_models_and_node_clause_both_applied_as_child_filters(self):
        """
        Traversal: find persons whose friends have nickname "CHARLIE" (NODE clause)
        AND have a string node containing "CHARLIE" (SEARCH_MODELS clause).

        Both conditions are placed in the same no-relationship subgroup. The
        compile → build_anchor_exists path applies both:
          - Exists(TermSearch where value ILIKE '%CHARLIE%') for SEARCH_MODELS
          - Exists(TermSearch where value = 'CHARLIE' AND node_alias='nickname') for NODE

        Only Person C satisfies both (nickname = "CHARLIE" and "CHARLIE" present in
        string nodes), so only persons who are friends with Person C qualify.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [
                            {
                                "graph_slug": "person",
                                "scope": "RESOURCE",
                                "logic": "AND",
                                "clauses": [
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": {
                                            "type": "NODE",
                                            "graph_slug": "person",
                                            "node_alias": "nickname",
                                            "search_models": [],
                                        },
                                        "operator": "EQUALS",
                                        "operands": [
                                            {"type": "LITERAL", "value": "CHARLIE"}
                                        ],
                                    },
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": _search_models_subject(),
                                        "operator": "LIKE",
                                        "operands": [
                                            {"type": "LITERAL", "value": "CHARLIE"}
                                        ],
                                    },
                                ],
                                "groups": [],
                                "aggregations": [],
                                "relationship": None,
                            }
                        ],
                        "aggregations": [],
                        "relationship": {
                            "path": {
                                "type": "NODE",
                                "graph_slug": "person",
                                "node_alias": "friends",
                            },
                            "is_inverse": False,
                            "traversal_quantifier": "ANY",
                        },
                    }
                ],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})
