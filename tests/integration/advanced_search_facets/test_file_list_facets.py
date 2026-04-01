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


class FileListAdvancedSearchFacetIntegrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        size_suffix = uuid.uuid4().hex[:8]
        cls.size_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_file_list_size_{size_suffix}",
            isresource=True,
        )
        cls.size_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.size_file_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{size_suffix}",
            alias=f"value_{size_suffix}",
            datatype="file-list",
            graph=cls.size_graph,
            nodegroup=cls.size_nodegroup,
            istopnode=True,
        )
        cls.larger_size_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.size_graph,
        )
        cls.larger_size_resource.save()
        cls.smaller_size_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.size_graph,
        )
        cls.smaller_size_resource.save()
        cls.larger_size_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.size_nodegroup,
            resourceinstance=cls.larger_size_resource,
            data={str(cls.size_file_list_node.nodeid): [{"name": "11"}]},
            provisionaledits=None,
        )
        cls.larger_size_tile.save()
        cls.smaller_size_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.size_nodegroup,
            resourceinstance=cls.smaller_size_resource,
            data={str(cls.size_file_list_node.nodeid): [{"name": "2"}]},
            provisionaledits=None,
        )
        cls.smaller_size_tile.save()

        count_suffix = uuid.uuid4().hex[:8]
        cls.count_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_file_list_count_{count_suffix}",
            isresource=True,
        )
        cls.count_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.count_file_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{count_suffix}",
            alias=f"value_{count_suffix}",
            datatype="file-list",
            graph=cls.count_graph,
            nodegroup=cls.count_nodegroup,
            istopnode=True,
        )
        cls.larger_count_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.count_graph,
        )
        cls.larger_count_resource.save()
        cls.smaller_count_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.count_graph,
        )
        cls.smaller_count_resource.save()
        cls.larger_count_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.count_nodegroup,
            resourceinstance=cls.larger_count_resource,
            data={str(cls.count_file_list_node.nodeid): [{"name": "10"}]},
            provisionaledits=None,
        )
        cls.larger_count_tile.save()
        cls.smaller_count_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.count_nodegroup,
            resourceinstance=cls.smaller_count_resource,
            data={str(cls.count_file_list_node.nodeid): [{"name": "2"}]},
            provisionaledits=None,
        )
        cls.smaller_count_tile.save()

        name_suffix = uuid.uuid4().hex[:8]
        cls.name_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_file_list_name_{name_suffix}",
            isresource=True,
        )
        cls.name_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.name_file_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{name_suffix}",
            alias=f"value_{name_suffix}",
            datatype="file-list",
            graph=cls.name_graph,
            nodegroup=cls.name_nodegroup,
            istopnode=True,
        )
        cls.invoice_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.name_graph,
        )
        cls.invoice_resource.save()
        cls.notes_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.name_graph,
        )
        cls.notes_resource.save()
        cls.invoice_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.name_nodegroup,
            resourceinstance=cls.invoice_resource,
            data={str(cls.name_file_list_node.nodeid): [{"name": "invoice_2024.pdf"}]},
            provisionaledits=None,
        )
        cls.invoice_tile.save()
        cls.notes_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.name_nodegroup,
            resourceinstance=cls.notes_resource,
            data={str(cls.name_file_list_node.nodeid): [{"name": "notes.txt"}]},
            provisionaledits=None,
        )
        cls.notes_tile.save()

        extension_suffix = uuid.uuid4().hex[:8]
        cls.extension_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_file_list_extension_{extension_suffix}",
            isresource=True,
        )
        cls.extension_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.extension_file_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{extension_suffix}",
            alias=f"value_{extension_suffix}",
            datatype="file-list",
            graph=cls.extension_graph,
            nodegroup=cls.extension_nodegroup,
            istopnode=True,
        )
        cls.pdf_extension_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.extension_graph,
        )
        cls.pdf_extension_resource.save()
        cls.txt_extension_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.extension_graph,
        )
        cls.txt_extension_resource.save()
        cls.pdf_extension_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.extension_nodegroup,
            resourceinstance=cls.pdf_extension_resource,
            data={str(cls.extension_file_list_node.nodeid): [{"name": "pdf"}]},
            provisionaledits=None,
        )
        cls.pdf_extension_tile.save()
        cls.txt_extension_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.extension_nodegroup,
            resourceinstance=cls.txt_extension_resource,
            data={str(cls.extension_file_list_node.nodeid): [{"name": "txt"}]},
            provisionaledits=None,
        )
        cls.txt_extension_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        cls.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_file_list_presence_{presence_suffix}",
            isresource=True,
        )
        cls.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.presence_file_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="file-list",
            graph=cls.presence_graph,
            nodegroup=cls.presence_nodegroup,
            istopnode=True,
        )
        cls.resource_with_file = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_with_file.save()
        cls.resource_without_file = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_without_file.save()
        cls.tile_with_file = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_with_file,
            data={
                str(cls.presence_file_list_node.nodeid): [{"name": "invoice_2024.pdf"}]
            },
            provisionaledits=None,
        )
        cls.tile_with_file.save()
        cls.tile_without_file = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_without_file,
            data={},
            provisionaledits=None,
        )
        cls.tile_without_file.save()

        call_command("db_index", "reindex_database")

    # def test_file_size_greater_than_prefers_the_larger_indexed_value(self):
    #     """This checks that the file size greater than facet returns only the resource whose indexed file-list value sits above the requested threshold."""
    #     payload = {
    #         "graph_slug": cls.size_graph.slug,
    #         "scope": "RESOURCE",
    #         "logic": "AND",
    #         "clauses": [
    #             {
    #                 "type": "LITERAL",
    #                 "quantifier": "ANY",
    #                 "subject": [[cls.size_graph.slug, cls.size_file_list_node.alias]],
    #                 "operator": "FILE_SIZE_GREATER_THAN",
    #                 "operands": [{"type": "LITERAL", "value": 10}],
    #             }
    #         ],
    #         "groups": [],
    #         "aggregations": [],
    #         "relationship": None,
    #     }
    #
    #     result = set(
    #         AdvancedSearchQueryCompiler(payload)
    #         .compile()
    #         .values_list("resourceinstanceid", flat=True)
    #     )
    #
    #     cls.assertEqual(result, {cls.larger_size_resource.resourceinstanceid})
    #
    # def test_file_size_less_than_prefers_the_smaller_indexed_value(self):
    #     """This checks that the file size less than facet returns only the resource whose indexed file-list value sits below the requested threshold."""
    #     payload = {
    #         "graph_slug": cls.size_graph.slug,
    #         "scope": "RESOURCE",
    #         "logic": "AND",
    #         "clauses": [
    #             {
    #                 "type": "LITERAL",
    #                 "quantifier": "ANY",
    #                 "subject": [[cls.size_graph.slug, cls.size_file_list_node.alias]],
    #                 "operator": "FILE_SIZE_LESS_THAN",
    #                 "operands": [{"type": "LITERAL", "value": 10}],
    #             }
    #         ],
    #         "groups": [],
    #         "aggregations": [],
    #         "relationship": None,
    #     }
    #
    #     result = set(
    #         AdvancedSearchQueryCompiler(payload)
    #         .compile()
    #         .values_list("resourceinstanceid", flat=True)
    #     )
    #
    #     cls.assertEqual(result, {cls.smaller_size_resource.resourceinstanceid})
    #
    # def test_file_size_between_prefers_the_value_inside_the_requested_band(self):
    #     """This checks that the file size between facet returns only the resource whose indexed file-list value lands inside the requested band."""
    #     payload = {
    #         "graph_slug": cls.size_graph.slug,
    #         "scope": "RESOURCE",
    #         "logic": "AND",
    #         "clauses": [
    #             {
    #                 "type": "LITERAL",
    #                 "quantifier": "ANY",
    #                 "subject": [[cls.size_graph.slug, cls.size_file_list_node.alias]],
    #                 "operator": "FILE_SIZE_BETWEEN",
    #                 "operands": [
    #                     {"type": "LITERAL", "value": 10},
    #                     {"type": "LITERAL", "value": 30},
    #                 ],
    #             }
    #         ],
    #         "groups": [],
    #         "aggregations": [],
    #         "relationship": None,
    #     }
    #
    #     result = set(
    #         AdvancedSearchQueryCompiler(payload)
    #         .compile()
    #         .values_list("resourceinstanceid", flat=True)
    #     )
    #
    #     cls.assertEqual(result, {cls.larger_size_resource.resourceinstanceid})
    #
    # def test_file_count_greater_than_prefers_the_larger_indexed_value(self):
    #     """This checks that the file count greater than facet returns only the resource whose indexed file-list value sits above the requested threshold."""
    #     payload = {
    #         "graph_slug": cls.count_graph.slug,
    #         "scope": "RESOURCE",
    #         "logic": "AND",
    #         "clauses": [
    #             {
    #                 "type": "LITERAL",
    #                 "quantifier": "ANY",
    #                 "subject": [[cls.count_graph.slug, cls.count_file_list_node.alias]],
    #                 "operator": "FILE_COUNT_GREATER_THAN",
    #                 "operands": [{"type": "LITERAL", "value": 9}],
    #             }
    #         ],
    #         "groups": [],
    #         "aggregations": [],
    #         "relationship": None,
    #     }
    #
    #     result = set(
    #         AdvancedSearchQueryCompiler(payload)
    #         .compile()
    #         .values_list("resourceinstanceid", flat=True)
    #     )
    #
    #     cls.assertEqual(result, {cls.larger_count_resource.resourceinstanceid})
    #
    # def test_file_count_less_than_prefers_the_smaller_indexed_value(self):
    #     """This checks that the file count less than facet returns only the resource whose indexed file-list value sits below the requested threshold."""
    #     payload = {
    #         "graph_slug": cls.count_graph.slug,
    #         "scope": "RESOURCE",
    #         "logic": "AND",
    #         "clauses": [
    #             {
    #                 "type": "LITERAL",
    #                 "quantifier": "ANY",
    #                 "subject": [[cls.count_graph.slug, cls.count_file_list_node.alias]],
    #                 "operator": "FILE_COUNT_LESS_THAN",
    #                 "operands": [{"type": "LITERAL", "value": 9}],
    #             }
    #         ],
    #         "groups": [],
    #         "aggregations": [],
    #         "relationship": None,
    #     }
    #
    #     result = set(
    #         AdvancedSearchQueryCompiler(payload)
    #         .compile()
    #         .values_list("resourceinstanceid", flat=True)
    #     )
    #
    #     cls.assertEqual(result, {cls.smaller_count_resource.resourceinstanceid})
    def test_file_name_like_matches_the_requested_filename_text(self):
        """This checks that the file name like facet returns only the resource whose indexed file name contains the requested text."""
        payload = {
            "graph_slug": self.name_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.name_graph.slug, self.name_file_list_node.alias]],
                    "operator": "FILE_NAME_LIKE",
                    "operands": [{"type": "LITERAL", "value": "invoice"}],
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

        self.assertEqual(result, {self.invoice_resource.resourceinstanceid})

    def test_file_extension_equals_matches_the_requested_extension_value(self):
        """This checks that the file extension facet returns only the resource whose indexed file-list value exactly matches the requested extension text."""
        payload = {
            "graph_slug": self.extension_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.extension_graph.slug, self.extension_file_list_node.alias]
                    ],
                    "operator": "FILE_EXTENSION_EQUALS",
                    "operands": [{"type": "LITERAL", "value": "pdf"}],
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

        self.assertEqual(result, {self.pdf_extension_resource.resourceinstanceid})

    def test_has_no_value_matches_the_resource_without_a_file_list_row(self):
        """This checks that the has no value facet returns only the resource whose file-list tile indexed no value at all."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.presence_graph.slug, self.presence_file_list_node.alias]
                    ],
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

        self.assertEqual(result, {self.resource_without_file.resourceinstanceid})

    def test_has_any_value_matches_the_resource_with_a_file_list_row(self):
        """This checks that the has any value facet returns only the resource whose file-list tile indexed a real value."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.presence_graph.slug, self.presence_file_list_node.alias]
                    ],
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

        self.assertEqual(result, {self.resource_with_file.resourceinstanceid})
