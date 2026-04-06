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


class ReferenceAdvancedSearchFacetIntegrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reference_list_id = str(uuid.uuid4())

        cls.reference_a = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": cls.reference_list_id,
            "labels": [
                {
                    "id": str(uuid.uuid4()),
                    "value": "ref-a",
                    "language_id": "en",
                    "valuetype_id": "prefLabel",
                    "list_item_id": str(uuid.uuid4()),
                }
            ],
        }
        cls.reference_b = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": cls.reference_list_id,
            "labels": [
                {
                    "id": str(uuid.uuid4()),
                    "value": "ref-b",
                    "language_id": "en",
                    "valuetype_id": "prefLabel",
                    "list_item_id": str(uuid.uuid4()),
                }
            ],
        }
        cls.reference_c = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": cls.reference_list_id,
            "labels": [
                {
                    "id": str(uuid.uuid4()),
                    "value": "ref-c",
                    "language_id": "en",
                    "valuetype_id": "prefLabel",
                    "list_item_id": str(uuid.uuid4()),
                }
            ],
        }
        cls.reference_child = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": cls.reference_list_id,
            "labels": [
                {
                    "id": str(uuid.uuid4()),
                    "value": "ref-child",
                    "language_id": "en",
                    "valuetype_id": "prefLabel",
                    "list_item_id": str(uuid.uuid4()),
                }
            ],
        }
        cls.reference_parent = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": cls.reference_list_id,
            "labels": [
                {
                    "id": str(uuid.uuid4()),
                    "value": "ref-parent",
                    "language_id": "en",
                    "valuetype_id": "prefLabel",
                    "list_item_id": str(uuid.uuid4()),
                }
            ],
        }
        cls.reference_other = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": cls.reference_list_id,
            "labels": [
                {
                    "id": str(uuid.uuid4()),
                    "value": "ref-other",
                    "language_id": "en",
                    "valuetype_id": "prefLabel",
                    "list_item_id": str(uuid.uuid4()),
                }
            ],
        }

        any_suffix = uuid.uuid4().hex[:8]
        cls.any_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_any_{any_suffix}",
            isresource=True,
        )
        cls.any_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.any_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{any_suffix}",
            alias=f"value_{any_suffix}",
            datatype="reference",
            graph=cls.any_graph,
            nodegroup=cls.any_nodegroup,
            istopnode=True,
            config={"controlledList": cls.reference_list_id, "multiValue": True},
        )

        cls.any_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.any_graph,
        )
        cls.any_match_resource.save()
        cls.any_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.any_graph,
        )
        cls.any_other_resource.save()

        cls.any_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.any_nodegroup,
            resourceinstance=cls.any_match_resource,
            data={str(cls.any_reference_node.nodeid): [cls.reference_a]},
            provisionaledits=None,
        )
        cls.any_match_tile.save()
        cls.any_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.any_nodegroup,
            resourceinstance=cls.any_other_resource,
            data={str(cls.any_reference_node.nodeid): [cls.reference_c]},
            provisionaledits=None,
        )
        cls.any_other_tile.save()

        all_suffix = uuid.uuid4().hex[:8]
        cls.all_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_all_{all_suffix}",
            isresource=True,
        )
        cls.all_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.all_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{all_suffix}",
            alias=f"value_{all_suffix}",
            datatype="reference",
            graph=cls.all_graph,
            nodegroup=cls.all_nodegroup,
            istopnode=True,
            config={"controlledList": cls.reference_list_id, "multiValue": True},
        )

        cls.all_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.all_graph,
        )
        cls.all_match_resource.save()
        cls.all_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.all_graph,
        )
        cls.all_other_resource.save()

        cls.all_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.all_nodegroup,
            resourceinstance=cls.all_match_resource,
            data={
                str(cls.all_reference_node.nodeid): [
                    cls.reference_a,
                    cls.reference_b,
                ]
            },
            provisionaledits=None,
        )
        cls.all_match_tile.save()
        cls.all_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.all_nodegroup,
            resourceinstance=cls.all_other_resource,
            data={str(cls.all_reference_node.nodeid): [cls.reference_a]},
            provisionaledits=None,
        )
        cls.all_other_tile.save()

        only_suffix = uuid.uuid4().hex[:8]
        cls.only_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_only_{only_suffix}",
            isresource=True,
        )
        cls.only_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.only_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{only_suffix}",
            alias=f"value_{only_suffix}",
            datatype="reference",
            graph=cls.only_graph,
            nodegroup=cls.only_nodegroup,
            istopnode=True,
            config={"controlledList": cls.reference_list_id, "multiValue": True},
        )

        cls.only_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.only_graph,
        )
        cls.only_match_resource.save()
        cls.only_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.only_graph,
        )
        cls.only_other_resource.save()

        cls.only_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.only_nodegroup,
            resourceinstance=cls.only_match_resource,
            data={
                str(cls.only_reference_node.nodeid): [
                    cls.reference_a,
                    cls.reference_b,
                ]
            },
            provisionaledits=None,
        )
        cls.only_match_tile.save()
        cls.only_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.only_nodegroup,
            resourceinstance=cls.only_other_resource,
            data={
                str(cls.only_reference_node.nodeid): [
                    cls.reference_a,
                    cls.reference_b,
                    cls.reference_c,
                ]
            },
            provisionaledits=None,
        )
        cls.only_other_tile.save()

        none_suffix = uuid.uuid4().hex[:8]
        cls.none_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_none_{none_suffix}",
            isresource=True,
        )
        cls.none_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.none_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{none_suffix}",
            alias=f"value_{none_suffix}",
            datatype="reference",
            graph=cls.none_graph,
            nodegroup=cls.none_nodegroup,
            istopnode=True,
            config={"controlledList": cls.reference_list_id, "multiValue": True},
        )

        cls.none_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.none_graph,
        )
        cls.none_match_resource.save()
        cls.none_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.none_graph,
        )
        cls.none_other_resource.save()

        cls.none_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.none_nodegroup,
            resourceinstance=cls.none_match_resource,
            data={str(cls.none_reference_node.nodeid): [cls.reference_c]},
            provisionaledits=None,
        )
        cls.none_match_tile.save()
        cls.none_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.none_nodegroup,
            resourceinstance=cls.none_other_resource,
            data={str(cls.none_reference_node.nodeid): [cls.reference_a]},
            provisionaledits=None,
        )
        cls.none_other_tile.save()

        descendant_suffix = uuid.uuid4().hex[:8]
        cls.descendant_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_descendant_{descendant_suffix}",
            isresource=True,
        )
        cls.descendant_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.descendant_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{descendant_suffix}",
            alias=f"value_{descendant_suffix}",
            datatype="reference",
            graph=cls.descendant_graph,
            nodegroup=cls.descendant_nodegroup,
            istopnode=True,
            config={"controlledList": cls.reference_list_id, "multiValue": True},
        )

        cls.descendant_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.descendant_graph,
        )
        cls.descendant_match_resource.save()
        cls.descendant_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.descendant_graph,
        )
        cls.descendant_other_resource.save()

        cls.descendant_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.descendant_nodegroup,
            resourceinstance=cls.descendant_match_resource,
            data={str(cls.descendant_reference_node.nodeid): [cls.reference_child]},
            provisionaledits=None,
        )
        cls.descendant_match_tile.save()
        cls.descendant_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.descendant_nodegroup,
            resourceinstance=cls.descendant_other_resource,
            data={str(cls.descendant_reference_node.nodeid): [cls.reference_other]},
            provisionaledits=None,
        )
        cls.descendant_other_tile.save()

        ancestor_suffix = uuid.uuid4().hex[:8]
        cls.ancestor_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_ancestor_{ancestor_suffix}",
            isresource=True,
        )
        cls.ancestor_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.ancestor_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{ancestor_suffix}",
            alias=f"value_{ancestor_suffix}",
            datatype="reference",
            graph=cls.ancestor_graph,
            nodegroup=cls.ancestor_nodegroup,
            istopnode=True,
            config={"controlledList": cls.reference_list_id, "multiValue": True},
        )

        cls.ancestor_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.ancestor_graph,
        )
        cls.ancestor_match_resource.save()
        cls.ancestor_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.ancestor_graph,
        )
        cls.ancestor_other_resource.save()

        cls.ancestor_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.ancestor_nodegroup,
            resourceinstance=cls.ancestor_match_resource,
            data={str(cls.ancestor_reference_node.nodeid): [cls.reference_parent]},
            provisionaledits=None,
        )
        cls.ancestor_match_tile.save()
        cls.ancestor_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.ancestor_nodegroup,
            resourceinstance=cls.ancestor_other_resource,
            data={str(cls.ancestor_reference_node.nodeid): [cls.reference_other]},
            provisionaledits=None,
        )
        cls.ancestor_other_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        cls.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_presence_{presence_suffix}",
            isresource=True,
        )
        cls.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.presence_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="reference",
            graph=cls.presence_graph,
            nodegroup=cls.presence_nodegroup,
            istopnode=True,
            config={"controlledList": cls.reference_list_id, "multiValue": True},
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
            data={str(cls.presence_reference_node.nodeid): [cls.reference_a]},
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

    def test_references_any_matches_when_any_requested_reference_is_present(self):
        """This checks that the references any facet returns only the resource that contains at least one requested reference label."""
        payload = {
            "graph_slug": self.any_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.any_graph.slug,
                        "node_alias": self.any_reference_node.alias,
                        "search_models": [],
                    },
                    "operator": "REFERENCES_ANY",
                    "operands": [{"type": "LITERAL", "value": ["ref-a", "ref-b"]}],
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

        self.assertEqual(result, {self.any_match_resource.resourceinstanceid})

    def test_references_all_matches_when_all_requested_references_are_present(self):
        """This checks that the references all facet returns only the resource that contains every requested reference label."""
        payload = {
            "graph_slug": self.all_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.all_graph.slug,
                        "node_alias": self.all_reference_node.alias,
                        "search_models": [],
                    },
                    "operator": "REFERENCES_ALL",
                    "operands": [{"type": "LITERAL", "value": ["ref-a", "ref-b"]}],
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

        self.assertEqual(result, {self.all_match_resource.resourceinstanceid})

    def test_references_only_matches_when_no_extra_references_are_present(self):
        """This checks that the references only facet returns only the resource whose indexed labels exactly match the requested set."""
        payload = {
            "graph_slug": self.only_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.only_graph.slug,
                        "node_alias": self.only_reference_node.alias,
                        "search_models": [],
                    },
                    "operator": "REFERENCES_ONLY",
                    "operands": [{"type": "LITERAL", "value": ["ref-a", "ref-b"]}],
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

        self.assertEqual(result, {self.only_match_resource.resourceinstanceid})

    def test_references_none_of_matches_when_requested_references_are_absent(self):
        """This checks that the references none of facet returns only the resource that omits every forbidden reference label."""
        payload = {
            "graph_slug": self.none_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.none_graph.slug,
                        "node_alias": self.none_reference_node.alias,
                        "search_models": [],
                    },
                    "operator": "REFERENCES_NONE_OF",
                    "operands": [{"type": "LITERAL", "value": ["ref-a", "ref-b"]}],
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

        self.assertEqual(result, {self.none_match_resource.resourceinstanceid})

    def test_descendant_of_matches_the_requested_descendant_token(self):
        """This checks that the descendant of facet returns only the resource whose indexed reference label matches the requested descendant token."""
        payload = {
            "graph_slug": self.descendant_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.descendant_graph.slug,
                        "node_alias": self.descendant_reference_node.alias,
                        "search_models": [],
                    },
                    "operator": "DESCENDANT_OF",
                    "operands": [{"type": "LITERAL", "value": ["ref-child"]}],
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

        self.assertEqual(result, {self.descendant_match_resource.resourceinstanceid})

    def test_ancestor_of_matches_the_requested_ancestor_token(self):
        """This checks that the ancestor of facet returns only the resource whose indexed reference label matches the requested ancestor token."""
        payload = {
            "graph_slug": self.ancestor_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.ancestor_graph.slug,
                        "node_alias": self.ancestor_reference_node.alias,
                        "search_models": [],
                    },
                    "operator": "ANCESTOR_OF",
                    "operands": [{"type": "LITERAL", "value": ["ref-parent"]}],
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

        self.assertEqual(result, {self.ancestor_match_resource.resourceinstanceid})

    def test_has_no_value_matches_the_resource_without_a_reference_row(self):
        """This checks that the has no value facet returns only the resource whose reference tile indexed no value at all."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.presence_graph.slug,
                        "node_alias": self.presence_reference_node.alias,
                        "search_models": [],
                    },
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

    def test_has_any_value_matches_the_resource_with_a_reference_row(self):
        """This checks that the has any value facet returns only the resource whose reference tile indexed a real value."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.presence_graph.slug,
                        "node_alias": self.presence_reference_node.alias,
                        "search_models": [],
                    },
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
