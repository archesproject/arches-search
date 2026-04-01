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
        cls.modified_2024_01_10 = 1704844800000
        cls.modified_2024_01_15 = 1705276800000
        cls.modified_2024_01_20 = 1705708800000
        cls.modified_2024_01_31 = 1706659200000

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
        cls.larger_size_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.size_graph,
        )
        cls.smaller_size_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.size_graph,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.size_nodegroup,
            resourceinstance=cls.larger_size_resource,
            data={
                str(cls.size_file_list_node.nodeid): [
                    {
                        "name": "large_invoice.pdf",
                        "size": 11,
                        "lastModified": cls.modified_2024_01_20,
                    }
                ]
            },
            provisionaledits=None,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.size_nodegroup,
            resourceinstance=cls.smaller_size_resource,
            data={
                str(cls.size_file_list_node.nodeid): [
                    {
                        "name": "small_note.txt",
                        "size": 2,
                        "lastModified": cls.modified_2024_01_10,
                    }
                ]
            },
            provisionaledits=None,
        )

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
        cls.invoice_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.name_graph,
        )
        cls.notes_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.name_graph,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.name_nodegroup,
            resourceinstance=cls.invoice_resource,
            data={
                str(cls.name_file_list_node.nodeid): [
                    {"name": "invoice_2024.pdf", "size": 11}
                ]
            },
            provisionaledits=None,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.name_nodegroup,
            resourceinstance=cls.notes_resource,
            data={str(cls.name_file_list_node.nodeid): [{"name": "notes.txt"}]},
            provisionaledits=None,
        )

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
        cls.pdf_extension_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.extension_graph,
        )
        cls.txt_extension_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.extension_graph,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.extension_nodegroup,
            resourceinstance=cls.pdf_extension_resource,
            data={
                str(cls.extension_file_list_node.nodeid): [
                    {"name": "annual_report.pdf"}
                ]
            },
            provisionaledits=None,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.extension_nodegroup,
            resourceinstance=cls.txt_extension_resource,
            data={
                str(cls.extension_file_list_node.nodeid): [
                    {"name": "meeting_notes.txt"}
                ]
            },
            provisionaledits=None,
        )

        modified_suffix = uuid.uuid4().hex[:8]
        cls.modified_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_file_list_modified_{modified_suffix}",
            isresource=True,
        )
        cls.modified_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.modified_file_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{modified_suffix}",
            alias=f"value_{modified_suffix}",
            datatype="file-list",
            graph=cls.modified_graph,
            nodegroup=cls.modified_nodegroup,
            istopnode=True,
        )
        cls.earlier_modified_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.modified_graph,
        )
        cls.later_modified_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.modified_graph,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.modified_nodegroup,
            resourceinstance=cls.earlier_modified_resource,
            data={
                str(cls.modified_file_list_node.nodeid): [
                    {
                        "name": "field_photo.jpg",
                        "size": 20,
                        "lastModified": cls.modified_2024_01_15,
                    }
                ]
            },
            provisionaledits=None,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.modified_nodegroup,
            resourceinstance=cls.later_modified_resource,
            data={
                str(cls.modified_file_list_node.nodeid): [
                    {
                        "name": "scan.tif",
                        "size": 22,
                        "lastModified": cls.modified_2024_01_31,
                    }
                ]
            },
            provisionaledits=None,
        )

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
        cls.resource_with_file = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        cls.resource_without_file = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.presence_graph,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_with_file,
            data={
                str(cls.presence_file_list_node.nodeid): [
                    {
                        "name": "invoice_2024.pdf",
                        "lastModified": cls.modified_2024_01_20,
                    }
                ]
            },
            provisionaledits=None,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.presence_nodegroup,
            resourceinstance=cls.resource_without_file,
            data={},
            provisionaledits=None,
        )

        call_command("db_index", "reindex_database")

    def test_file_size_greater_than_prefers_the_larger_indexed_value(self):
        payload = {
            "graph_slug": self.size_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.size_graph.slug, self.size_file_list_node.alias]],
                    "operator": "FILE_SIZE_GREATER_THAN",
                    "operands": [{"type": "LITERAL", "value": 10}],
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

        self.assertEqual(result, {self.larger_size_resource.resourceinstanceid})

    def test_file_size_less_than_prefers_the_smaller_indexed_value(self):
        payload = {
            "graph_slug": self.size_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.size_graph.slug, self.size_file_list_node.alias]],
                    "operator": "FILE_SIZE_LESS_THAN",
                    "operands": [{"type": "LITERAL", "value": 10}],
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

        self.assertEqual(result, {self.smaller_size_resource.resourceinstanceid})

    def test_file_size_between_prefers_the_value_inside_the_requested_band(self):
        payload = {
            "graph_slug": self.size_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[self.size_graph.slug, self.size_file_list_node.alias]],
                    "operator": "FILE_SIZE_BETWEEN",
                    "operands": [
                        {"type": "LITERAL", "value": 10},
                        {"type": "LITERAL", "value": 30},
                    ],
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

        self.assertEqual(result, {self.larger_size_resource.resourceinstanceid})

    def test_file_name_like_matches_the_requested_filename_text(self):
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

    def test_file_modified_before_matches_the_earlier_file(self):
        payload = {
            "graph_slug": self.modified_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.modified_graph.slug, self.modified_file_list_node.alias]
                    ],
                    "operator": "FILE_MODIFIED_BEFORE",
                    "operands": [
                        {"type": "LITERAL", "value": self.modified_2024_01_20}
                    ],
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

        self.assertEqual(result, {self.earlier_modified_resource.resourceinstanceid})

    def test_file_modified_after_matches_the_later_file(self):
        payload = {
            "graph_slug": self.modified_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.modified_graph.slug, self.modified_file_list_node.alias]
                    ],
                    "operator": "FILE_MODIFIED_AFTER",
                    "operands": [
                        {"type": "LITERAL", "value": self.modified_2024_01_20}
                    ],
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

        self.assertEqual(result, {self.later_modified_resource.resourceinstanceid})

    def test_file_modified_between_matches_the_in_range_file(self):
        payload = {
            "graph_slug": self.modified_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [self.modified_graph.slug, self.modified_file_list_node.alias]
                    ],
                    "operator": "FILE_MODIFIED_BETWEEN",
                    "operands": [
                        {"type": "LITERAL", "value": self.modified_2024_01_10},
                        {"type": "LITERAL", "value": self.modified_2024_01_20},
                    ],
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

        self.assertEqual(result, {self.earlier_modified_resource.resourceinstanceid})

    def test_has_no_value_matches_the_resource_without_a_file_list_row(self):
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
