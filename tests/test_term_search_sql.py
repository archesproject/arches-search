"""SQL-shape checks for term search; these compile queries without hitting the DB."""

import uuid

from django.db import connection
from django.test import SimpleTestCase

from arches_search.utils.readable_nodes import ReadableNodes
from arches_search.utils.term_search.matching import get_related_resources_by_text

# python manage.py test tests.test_term_search_sql --settings="tests.test_settings"


class TermSearchSqlTests(SimpleTestCase):
    def compile_sql(self, terms, max_hops):
        queryset = get_related_resources_by_text(
            terms, uuid.uuid4(), ReadableNodes(None), max_hops=max_hops
        )
        return queryset.query.get_compiler(connection=connection).as_sql()

    def test_term_subquery_is_materialized_once_per_term(self):
        sql, _ = self.compile_sql(["beef"], max_hops=2)
        self.assertEqual(sql.count('FROM "arches_search_terms"'), 1)
        self.assertEqual(sql.count("AS MATERIALIZED"), 3)

    def test_hops_are_combined_with_union(self):
        sql, _ = self.compile_sql(["beef"], max_hops=2)
        self.assertIn(" UNION ", sql)

    def test_no_hops_has_no_relationship_tables(self):
        sql, _ = self.compile_sql(["beef"], max_hops=0)
        self.assertNotIn("resource_x_resource", sql)

    def test_each_term_is_expanded_independently(self):
        sql, _ = self.compile_sql(["beef", "pork"], max_hops=1)
        self.assertEqual(sql.count('FROM "arches_search_terms"'), 2)

    def test_substring_match_escapes_like_wildcards(self):
        sql, params = self.compile_sql(["50%_off"], max_hops=0)
        self.assertIn("ILIKE", sql)
        self.assertIn("%50\\%\\_off%", params)
