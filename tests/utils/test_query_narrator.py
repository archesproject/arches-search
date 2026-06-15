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
        # title_node with datatype="string" is required for the localized-string branch,
        # which only activates when the subject's resolved datatype is "string".
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

    # --- Helpers ---

    def _group(
        self, graph_slug=None, logic="AND", clauses=None, groups=None, relationship=None
    ):
        """Build a complete group payload. All required keys always present."""
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
        """Build a NODE clause with positional values as LITERAL operands."""
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

    def _relationship_payload(self, quantifier="ANY", is_inverse=False):
        """
        Root payload with a relationship subgroup linking Photograph → Person via "depicts".
        The linked Person group has a single clause: name LIKE "Alice".
        """
        person_group = self._group(
            graph_slug=self.PERSON_SLUG,
            clauses=[
                self._clause("name", "LIKE", "Alice", graph_slug=self.PERSON_SLUG)
            ],
        )
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

    # --- Empty / missing payload ---

    def test_empty_payload_returns_empty_string(self):
        self.assertEqual(QueryNarrator({}).narrate(), "")

    def test_no_graph_slug_returns_empty_string(self):
        payload = {"clauses": [], "groups": [], "relationship": None}
        self.assertEqual(QueryNarrator(payload).narrate(), "")

    # --- Graph slug label ---

    def test_unknown_slug_falls_back_to_raw_slug_as_label(self):
        payload = self._group(graph_slug="no_such_slug")
        self.assertEqual(
            QueryNarrator(payload).narrate(), 'All "no_such_slug" records.'
        )

    # --- No clauses ---

    def test_no_clauses_returns_all_records_sentence(self):
        self.assertEqual(
            QueryNarrator(self._group()).narrate(),
            'All "Photograph" records.',
        )

    # --- Clause rendering ---

    def test_single_clause_with_two_numeric_operands_joined_with_and(self):
        # Integers render as str(n) without quotes; two values use "X and Y"
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
                self._clause("field_a", "EQ", "foo"),
                self._clause("field_b", "EQ", "bar"),
            ],
        )
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "field_a" EQ "foo"\n• "field_b" EQ "bar"',
        )

    def test_two_or_clauses_second_clause_gets_or_prefix(self):
        payload = self._group(
            logic="OR",
            clauses=[
                self._clause("field_a", "EQ", "foo"),
                self._clause("field_b", "EQ", "bar"),
            ],
        )
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "field_a" EQ "foo"\n• OR: "field_b" EQ "bar"',
        )

    # --- Value list joining ---

    def test_three_string_operands_joined_with_oxford_comma(self):
        payload = self._group(clauses=[self._clause("tags", "IN", "a", "b", "c")])
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "tags" IN "a", "b", and "c"',
        )

    # --- Operand types ---

    def test_boolean_true_renders_as_true(self):
        payload = self._group(clauses=[self._clause("verified", "IS", True)])
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "verified" IS true',
        )

    def test_boolean_false_renders_as_false(self):
        payload = self._group(clauses=[self._clause("verified", "IS", False)])
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "verified" IS false',
        )

    def test_localized_string_operand_appends_language_code_in_parens(self):
        # Requires title_node.datatype == "string" to activate the {lang: text} branch.
        # Without the node in DB the datatype would be "" and the dict would be quoted raw.
        payload = self._group(
            clauses=[self._clause("title", "LIKE", {"en": "Eiffel Tower"})]
        )
        self.assertEqual(
            QueryNarrator(payload).narrate(),
            'All "Photograph" records where:\n• "title" is like "Eiffel Tower" (en)',
        )

    # --- Relationships ---

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

    def test_inverse_relationship_any_quantifier(self):
        self.assertEqual(
            QueryNarrator(self._relationship_payload("ANY", is_inverse=True)).narrate(),
            (
                'All "Photograph" records where:\n'
                '• referenced by at least one "Person" (via "depicts"):\n'
                '    • "name" is like "Alice"'
            ),
        )
