import uuid

from django.core.management import call_command
from django.test import TestCase

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    TileModel,
)
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)


class NonLocalizedStringAdvancedSearchFacetIntegrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        text_suffix = uuid.uuid4().hex[:8]
        cls.text_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_non_localized_string_text_{text_suffix}",
            isresource=True,
        )
        cls.text_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.text_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{text_suffix}",
            alias=f"value_{text_suffix}",
            datatype="non-localized-string",
            graph=cls.text_graph,
            nodegroup=cls.text_nodegroup,
            istopnode=True,
        )

        cls.needle_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.text_graph,
        )
        cls.needle_resource.save()
        cls.plain_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.text_graph,
        )
        cls.plain_resource.save()

        cls.needle_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.text_nodegroup,
            resourceinstance=cls.needle_resource,
            data={str(cls.text_node.nodeid): "prefix needle suffix"},
            provisionaledits=None,
        )
        cls.needle_tile.save()
        cls.plain_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.text_nodegroup,
            resourceinstance=cls.plain_resource,
            data={str(cls.text_node.nodeid): "plain text"},
            provisionaledits=None,
        )
        cls.plain_tile.save()

        prefix_suffix = uuid.uuid4().hex[:8]
        cls.prefix_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_non_localized_string_prefix_{prefix_suffix}",
            isresource=True,
        )
        cls.prefix_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.prefix_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{prefix_suffix}",
            alias=f"value_{prefix_suffix}",
            datatype="non-localized-string",
            graph=cls.prefix_graph,
            nodegroup=cls.prefix_nodegroup,
            istopnode=True,
        )

        cls.prefix_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.prefix_graph,
        )
        cls.prefix_match_resource.save()
        cls.prefix_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.prefix_graph,
        )
        cls.prefix_other_resource.save()

        cls.prefix_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.prefix_nodegroup,
            resourceinstance=cls.prefix_match_resource,
            data={str(cls.prefix_node.nodeid): "needle suffix"},
            provisionaledits=None,
        )
        cls.prefix_match_tile.save()
        cls.prefix_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.prefix_nodegroup,
            resourceinstance=cls.prefix_other_resource,
            data={str(cls.prefix_node.nodeid): "prefix needle"},
            provisionaledits=None,
        )
        cls.prefix_other_tile.save()

        suffix_suffix = uuid.uuid4().hex[:8]
        cls.suffix_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_non_localized_string_suffix_{suffix_suffix}",
            isresource=True,
        )
        cls.suffix_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.suffix_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{suffix_suffix}",
            alias=f"value_{suffix_suffix}",
            datatype="non-localized-string",
            graph=cls.suffix_graph,
            nodegroup=cls.suffix_nodegroup,
            istopnode=True,
        )

        cls.suffix_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.suffix_graph,
        )
        cls.suffix_match_resource.save()
        cls.suffix_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.suffix_graph,
        )
        cls.suffix_other_resource.save()

        cls.suffix_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.suffix_nodegroup,
            resourceinstance=cls.suffix_match_resource,
            data={str(cls.suffix_node.nodeid): "prefix needle"},
            provisionaledits=None,
        )
        cls.suffix_match_tile.save()
        cls.suffix_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.suffix_nodegroup,
            resourceinstance=cls.suffix_other_resource,
            data={str(cls.suffix_node.nodeid): "needle prefix"},
            provisionaledits=None,
        )
        cls.suffix_other_tile.save()

        equality_suffix = uuid.uuid4().hex[:8]
        cls.equality_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_non_localized_string_equality_{equality_suffix}",
            isresource=True,
        )
        cls.equality_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.equality_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{equality_suffix}",
            alias=f"value_{equality_suffix}",
            datatype="non-localized-string",
            graph=cls.equality_graph,
            nodegroup=cls.equality_nodegroup,
            istopnode=True,
        )

        cls.equal_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.equality_graph,
        )
        cls.equal_resource.save()
        cls.other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.equality_graph,
        )
        cls.other_resource.save()

        cls.equal_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.equality_nodegroup,
            resourceinstance=cls.equal_resource,
            data={str(cls.equality_node.nodeid): "needle"},
            provisionaledits=None,
        )
        cls.equal_tile.save()
        cls.other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.equality_nodegroup,
            resourceinstance=cls.other_resource,
            data={str(cls.equality_node.nodeid): "other"},
            provisionaledits=None,
        )
        cls.other_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        cls.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_non_localized_string_presence_{presence_suffix}",
            isresource=True,
        )
        cls.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.presence_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="non-localized-string",
            graph=cls.presence_graph,
            nodegroup=cls.presence_nodegroup,
            istopnode=True,
        )

        cls.resource_with_value = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_with_value.save()
        cls.resource_without_value = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_without_value.save()

        cls.tile_with_value = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_with_value,
            data={str(cls.presence_node.nodeid): "needle"},
            provisionaledits=None,
        )
        cls.tile_with_value.save()
        cls.tile_without_value = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_without_value,
            data={},
            provisionaledits=None,
        )
        cls.tile_without_value.save()

        call_command("db_index", "reindex_database")

    def test_like_matches_a_substring(self):
        """This checks that the like facet returns only the resource whose indexed text contains the requested substring."""
        payload = {
            "graph_slug": self.text_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.text_graph.slug, self.text_node.alias]],
                    "operator": "LIKE",
                    "operands": [{"type": "LITERAL", "value": "needle"}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.needle_resource.resourceinstanceid})

    def test_not_like_excludes_a_substring(self):
        """This checks that the not like facet returns only the resource whose indexed text does not contain the requested substring."""
        payload = {
            "graph_slug": self.text_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.text_graph.slug, self.text_node.alias]],
                    "operator": "NOT_LIKE",
                    "operands": [{"type": "LITERAL", "value": "needle"}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.plain_resource.resourceinstanceid})

    def test_starts_with_matches_the_requested_prefix(self):
        """This checks that the starts with facet returns only the resource whose indexed text begins with the requested prefix."""
        payload = {
            "graph_slug": self.prefix_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.prefix_graph.slug, self.prefix_node.alias]],
                    "operator": "STARTS_WITH",
                    "operands": [{"type": "LITERAL", "value": "needle"}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.prefix_match_resource.resourceinstanceid})

    def test_ends_with_matches_the_requested_suffix(self):
        """This checks that the ends with facet returns only the resource whose indexed text ends with the requested suffix."""
        payload = {
            "graph_slug": self.suffix_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.suffix_graph.slug, self.suffix_node.alias]],
                    "operator": "ENDS_WITH",
                    "operands": [{"type": "LITERAL", "value": "needle"}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.suffix_match_resource.resourceinstanceid})

    def test_equals_matches_the_same_text(self):
        """This checks that the equals facet returns only the resource whose indexed text matches exactly."""
        payload = {
            "graph_slug": self.equality_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.equality_graph.slug, self.equality_node.alias]],
                    "operator": "EQUALS",
                    "operands": [{"type": "LITERAL", "value": "needle"}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.equal_resource.resourceinstanceid})

    def test_not_equals_excludes_the_same_text(self):
        """This checks that the not equals facet returns only the resource whose indexed text is different from the requested value."""
        payload = {
            "graph_slug": self.equality_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.equality_graph.slug, self.equality_node.alias]],
                    "operator": "NOT_EQUALS",
                    "operands": [{"type": "LITERAL", "value": "needle"}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.other_resource.resourceinstanceid})

    def test_has_no_value_matches_the_resource_without_a_text_row(self):
        """This checks that the has no value facet returns only the resource whose non-localized string tile indexed no value at all."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.presence_graph.slug, self.presence_node.alias]],
                    "operator": "HAS_NO_VALUE",
                    "operands": [],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.resource_without_value.resourceinstanceid})

    def test_has_any_value_matches_the_resource_with_a_text_row(self):
        """This checks that the has any value facet returns only the resource whose non-localized string tile indexed a real value."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.presence_graph.slug, self.presence_node.alias]],
                    "operator": "HAS_ANY_VALUE",
                    "operands": [],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

        self.assertEqual(result, {self.resource_with_value.resourceinstanceid})
