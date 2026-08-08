import uuid

from django.test import TestCase

from arches.app.models.models import GraphModel, Node, NodeGroup

from arches_search.utils.query_narrator import QueryNarrator


class QueryNarratorTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        photograph_suffix = uuid.uuid4().hex[:8]
        person_suffix = uuid.uuid4().hex[:8]

        cls.PHOTOGRAPH_SLUG = f"narrator_photo_{photograph_suffix}"
        cls.PERSON_SLUG = f"narrator_person_{person_suffix}"

        cls.photograph_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=cls.PHOTOGRAPH_SLUG,
            name="Photograph",
            isresource=True,
        )
        cls.person_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=cls.PERSON_SLUG,
            name="Person",
            isresource=True,
        )
        cls.title_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.title_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="title",
            alias="title",
            datatype="string",
            graph=cls.photograph_graph,
            nodegroup=cls.title_nodegroup,
            istopnode=True,
        )

    def _group(
        self, graph_slug=None, logic="AND", clauses=None, groups=None, relationship=None
    ):
        return {
            "graph_slug": (
                graph_slug if graph_slug is not None else self.PHOTOGRAPH_SLUG
            ),
            "logic": logic,
            "clauses": clauses or [],
            "groups": groups or [],
            "relationship": relationship,
            "aggregations": [],
            "scope": "RESOURCE",
        }

    def _clause(self, node_alias, operator, *values, graph_slug=None):
        graph_slug = graph_slug or self.PHOTOGRAPH_SLUG
        return {
            "subject": {
                "type": "NODE",
                "graph_slug": graph_slug,
                "node_alias": node_alias,
                "search_models": [],
            },
            "operator": operator,
            "operands": [{"type": "LITERAL", "value": value} for value in values],
        }

    def _relationship_payload(
        self, quantifier="ANY", is_inverse=False, inner_clauses=None
    ):
        if inner_clauses is None:
            inner_clauses = [
                self._clause("name", "LIKE", "Alice", graph_slug=self.PERSON_SLUG)
            ]
        person_group = self._group(graph_slug=self.PERSON_SLUG, clauses=inner_clauses)
        relationship_group = self._group(
            groups=[person_group],
            relationship={
                "path": {
                    "type": "NODE",
                    "graph_slug": self.PHOTOGRAPH_SLUG,
                    "node_alias": "depicts",
                },
                "is_inverse": is_inverse,
                "traversal_quantifier": quantifier,
            },
        )
        return self._group(groups=[relationship_group])

    def test_empty_payload_returns_empty_string(self):
        self.assertEqual(QueryNarrator({}).narrate(), "")

    def test_no_graph_slug_returns_empty_string(self):
        payload = {"clauses": [], "groups": [], "relationship": None}
        self.assertEqual(QueryNarrator(payload).narrate(), "")

    def test_unknown_slug_falls_back_to_raw_slug_as_label(self):
        payload = self._group(graph_slug="no_such_slug")
        self.assertEqual(
            QueryNarrator(payload).narrate(), 'All "no_such_slug" records.'
        )

    def test_no_clauses_returns_all_records_sentence(self):
        self.assertEqual(
            QueryNarrator(self._group()).narrate(),
            'All "Photograph" records.',
        )

    def test_single_string_operand_no_joining(self):
        payload = self._group(clauses=[self._clause("status", "LIKE", "active")])
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "status" is like "active"',
        )

    def test_single_clause_with_two_numeric_operands_joined_with_and(self):
        payload = self._group(
            clauses=[self._clause("date_taken", "BETWEEN", 1900, 1999)]
        )
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "date_taken" is between 1900 and 1999',
        )

    def test_two_and_clauses_render_without_or_prefix(self):
        payload = self._group(
            logic="AND",
            clauses=[
                self._clause("field_a", "LIKE", "foo"),
                self._clause("field_b", "LIKE", "bar"),
            ],
        )
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "field_a" is like "foo"\n• "field_b" is like "bar"',
        )

    def test_two_or_clauses_second_clause_gets_or_prefix(self):
        payload = self._group(
            logic="OR",
            clauses=[
                self._clause("field_a", "LIKE", "foo"),
                self._clause("field_b", "LIKE", "bar"),
            ],
        )
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "field_a" is like "foo"\n• OR: "field_b" is like "bar"',
        )

    def test_three_or_clauses_all_after_first_get_or_prefix(self):
        payload = self._group(
            logic="OR",
            clauses=[
                self._clause("field_a", "LIKE", "foo"),
                self._clause("field_b", "LIKE", "bar"),
                self._clause("field_c", "LIKE", "baz"),
            ],
        )
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            (
                'All "Photograph" records where:\n'
                '• "field_a" is like "foo"\n'
                '• OR: "field_b" is like "bar"\n'
                '• OR: "field_c" is like "baz"'
            ),
        )

    def test_three_string_operands_joined_with_oxford_comma(self):
        payload = self._group(clauses=[self._clause("tags", "LIKE", "a", "b", "c")])
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "tags" is like "a", "b", and "c"',
        )

    def test_is_true_operator_renders_without_value(self):
        payload = self._group(clauses=[self._clause("verified", "IS_TRUE")])
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "verified" is true',
        )

    def test_is_false_operator_renders_without_value(self):
        payload = self._group(clauses=[self._clause("verified", "IS_FALSE")])
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "verified" is false',
        )

    def test_boolean_operand_value_renders_as_word_not_integer(self):
        payload = self._group(clauses=[self._clause("active", "LIKE", True)])
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "active" is like true',
        )

    def test_display_value_used_over_value(self):
        clause = {
            "subject": {
                "type": "NODE",
                "graph_slug": self.PHOTOGRAPH_SLUG,
                "node_alias": "color",
                "search_models": [],
            },
            "operator": "LIKE",
            "operands": [
                {"type": "LITERAL", "value": "abc123", "display_value": "Red"}
            ],
        }
        self.assertEqual(
            QueryNarrator(self._group(clauses=[clause])).narrate(),
            'All "Photograph" records where:\n• "color" is like "Red"',
        )

    def test_localized_string_operand_appends_language_code_in_parens(self):
        payload = self._group(
            clauses=[self._clause("title", "LIKE", {"en": "Eiffel Tower"})]
        )
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "title" is like "Eiffel Tower" (en)',
        )

    def test_path_operand_renders_field_in_graph(self):
        clause = {
            "subject": {
                "type": "NODE",
                "graph_slug": self.PHOTOGRAPH_SLUG,
                "node_alias": "subject",
                "search_models": [],
            },
            "operator": "LIKE",
            "operands": [{"type": "PATH", "value": [[self.PERSON_SLUG, "name"]]}],
        }
        self.assertEqual(
            QueryNarrator(self._group(clauses=[clause])).narrate(),
            'All "Photograph" records where:\n• "subject" is like the "name" field in "Person"',
        )

    def test_relationship_any_quantifier(self):
        self.assertEqual(
            QueryNarrator(self._relationship_payload("ANY")).narrate(),
            (
                'All "Photograph" records where:\n'
                '• with at least one linked "Person" (via "depicts"):\n'
                '    • "name" is like "Alice"'
            ),
        )

    def test_relationship_none_quantifier(self):
        self.assertEqual(
            QueryNarrator(self._relationship_payload("NONE")).narrate(),
            (
                'All "Photograph" records where:\n'
                '• with no linked "Person" records (via "depicts"):\n'
                '    • "name" is like "Alice"'
            ),
        )

    def test_relationship_all_quantifier(self):
        self.assertEqual(
            QueryNarrator(self._relationship_payload("ALL")).narrate(),
            (
                'All "Photograph" records where:\n'
                '• where all linked "Person" records (via "depicts") match:\n'
                '    • "name" is like "Alice"'
            ),
        )

    def test_relationship_without_inner_conditions_has_no_colon(self):
        self.assertEqual(
            QueryNarrator(
                self._relationship_payload("ANY", inner_clauses=[])
            ).narrate(),
            (
                'All "Photograph" records where:\n'
                '• with at least one linked "Person" (via "depicts")'
            ),
        )

    def test_inverse_relationship_any_quantifier(self):
        self.assertEqual(
            QueryNarrator(self._relationship_payload("ANY", is_inverse=True)).narrate(),
            (
                'All "Photograph" records where:\n'
                '• referenced by at least one "Person" (via "depicts"):\n'
                '    • "name" is like "Alice"'
            ),
        )

    def test_inverse_relationship_none_quantifier(self):
        self.assertEqual(
            QueryNarrator(
                self._relationship_payload("NONE", is_inverse=True)
            ).narrate(),
            (
                'All "Photograph" records where:\n'
                '• not referenced by any "Person" (via "depicts"):\n'
                '    • "name" is like "Alice"'
            ),
        )

    def test_inverse_relationship_all_quantifier(self):
        self.assertEqual(
            QueryNarrator(self._relationship_payload("ALL", is_inverse=True)).narrate(),
            (
                'All "Photograph" records where:\n'
                '• referenced by all "Person" records (via "depicts"):\n'
                '    • "name" is like "Alice"'
            ),
        )

    def test_or_prefix_on_relationship_block_when_prior_clauses_exist(self):
        person_group = self._group(
            graph_slug=self.PERSON_SLUG,
            clauses=[
                self._clause("name", "LIKE", "Alice", graph_slug=self.PERSON_SLUG)
            ],
        )
        relationship_group = self._group(
            logic="OR",
            clauses=[self._clause("title", "LIKE", "sunset")],
            groups=[person_group],
            relationship={
                "path": {
                    "type": "NODE",
                    "graph_slug": self.PHOTOGRAPH_SLUG,
                    "node_alias": "depicts",
                },
                "is_inverse": False,
                "traversal_quantifier": "ANY",
            },
        )
        self.assertEqual(
            QueryNarrator(self._group(groups=[relationship_group])).narrate(),
            (
                'All "Photograph" records where:\n'
                '• "title" is like "sunset"\n'
                '• OR: with at least one linked "Person" (via "depicts"):\n'
                '    • "name" is like "Alice"'
            ),
        )

    def test_multi_segment_path_operand_uses_terminal_segment(self):
        clause = {
            "subject": {
                "type": "NODE",
                "graph_slug": self.PHOTOGRAPH_SLUG,
                "node_alias": "subject",
                "search_models": [],
            },
            "operator": "LIKE",
            "operands": [
                {
                    "type": "PATH",
                    "value": [
                        [self.PHOTOGRAPH_SLUG, "depicts"],
                        [self.PERSON_SLUG, "name"],
                    ],
                }
            ],
        }
        self.assertEqual(
            QueryNarrator(self._group(clauses=[clause])).narrate(),
            'All "Photograph" records where:\n• "subject" is like the "name" field in "Person"',
        )
