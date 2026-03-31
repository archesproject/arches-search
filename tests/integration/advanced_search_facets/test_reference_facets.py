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
    def setUp(self):
        self.reference_list_id = str(uuid.uuid4())

        self.reference_a = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": self.reference_list_id,
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
        self.reference_b = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": self.reference_list_id,
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
        self.reference_c = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": self.reference_list_id,
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
        self.reference_child = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": self.reference_list_id,
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
        self.reference_parent = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": self.reference_list_id,
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
        self.reference_other = {
            "uri": f"urn:test:reference:{uuid.uuid4()}",
            "list_id": self.reference_list_id,
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
        self.any_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_any_{any_suffix}",
            isresource=True,
        )
        self.any_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.any_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{any_suffix}",
            alias=f"value_{any_suffix}",
            datatype="reference",
            graph=self.any_graph,
            nodegroup=self.any_nodegroup,
            istopnode=True,
            config={"controlledList": self.reference_list_id, "multiValue": True},
        )

        self.any_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.any_graph,
        )
        self.any_match_resource.save()
        self.any_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.any_graph,
        )
        self.any_other_resource.save()

        self.any_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.any_nodegroup,
            resourceinstance=self.any_match_resource,
            data={str(self.any_reference_node.nodeid): [self.reference_a]},
            provisionaledits=None,
        )
        self.any_match_tile.save()
        self.any_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.any_nodegroup,
            resourceinstance=self.any_other_resource,
            data={str(self.any_reference_node.nodeid): [self.reference_c]},
            provisionaledits=None,
        )
        self.any_other_tile.save()

        all_suffix = uuid.uuid4().hex[:8]
        self.all_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_all_{all_suffix}",
            isresource=True,
        )
        self.all_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.all_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{all_suffix}",
            alias=f"value_{all_suffix}",
            datatype="reference",
            graph=self.all_graph,
            nodegroup=self.all_nodegroup,
            istopnode=True,
            config={"controlledList": self.reference_list_id, "multiValue": True},
        )

        self.all_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.all_graph,
        )
        self.all_match_resource.save()
        self.all_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.all_graph,
        )
        self.all_other_resource.save()

        self.all_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.all_nodegroup,
            resourceinstance=self.all_match_resource,
            data={
                str(self.all_reference_node.nodeid): [
                    self.reference_a,
                    self.reference_b,
                ]
            },
            provisionaledits=None,
        )
        self.all_match_tile.save()
        self.all_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.all_nodegroup,
            resourceinstance=self.all_other_resource,
            data={str(self.all_reference_node.nodeid): [self.reference_a]},
            provisionaledits=None,
        )
        self.all_other_tile.save()

        only_suffix = uuid.uuid4().hex[:8]
        self.only_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_only_{only_suffix}",
            isresource=True,
        )
        self.only_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.only_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{only_suffix}",
            alias=f"value_{only_suffix}",
            datatype="reference",
            graph=self.only_graph,
            nodegroup=self.only_nodegroup,
            istopnode=True,
            config={"controlledList": self.reference_list_id, "multiValue": True},
        )

        self.only_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.only_graph,
        )
        self.only_match_resource.save()
        self.only_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.only_graph,
        )
        self.only_other_resource.save()

        self.only_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.only_nodegroup,
            resourceinstance=self.only_match_resource,
            data={
                str(self.only_reference_node.nodeid): [
                    self.reference_a,
                    self.reference_b,
                ]
            },
            provisionaledits=None,
        )
        self.only_match_tile.save()
        self.only_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.only_nodegroup,
            resourceinstance=self.only_other_resource,
            data={
                str(self.only_reference_node.nodeid): [
                    self.reference_a,
                    self.reference_b,
                    self.reference_c,
                ]
            },
            provisionaledits=None,
        )
        self.only_other_tile.save()

        none_suffix = uuid.uuid4().hex[:8]
        self.none_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_none_{none_suffix}",
            isresource=True,
        )
        self.none_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.none_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{none_suffix}",
            alias=f"value_{none_suffix}",
            datatype="reference",
            graph=self.none_graph,
            nodegroup=self.none_nodegroup,
            istopnode=True,
            config={"controlledList": self.reference_list_id, "multiValue": True},
        )

        self.none_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.none_graph,
        )
        self.none_match_resource.save()
        self.none_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.none_graph,
        )
        self.none_other_resource.save()

        self.none_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.none_nodegroup,
            resourceinstance=self.none_match_resource,
            data={str(self.none_reference_node.nodeid): [self.reference_c]},
            provisionaledits=None,
        )
        self.none_match_tile.save()
        self.none_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.none_nodegroup,
            resourceinstance=self.none_other_resource,
            data={str(self.none_reference_node.nodeid): [self.reference_a]},
            provisionaledits=None,
        )
        self.none_other_tile.save()

        descendant_suffix = uuid.uuid4().hex[:8]
        self.descendant_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_descendant_{descendant_suffix}",
            isresource=True,
        )
        self.descendant_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.descendant_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{descendant_suffix}",
            alias=f"value_{descendant_suffix}",
            datatype="reference",
            graph=self.descendant_graph,
            nodegroup=self.descendant_nodegroup,
            istopnode=True,
            config={"controlledList": self.reference_list_id, "multiValue": True},
        )

        self.descendant_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.descendant_graph,
        )
        self.descendant_match_resource.save()
        self.descendant_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.descendant_graph,
        )
        self.descendant_other_resource.save()

        self.descendant_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.descendant_nodegroup,
            resourceinstance=self.descendant_match_resource,
            data={str(self.descendant_reference_node.nodeid): [self.reference_child]},
            provisionaledits=None,
        )
        self.descendant_match_tile.save()
        self.descendant_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.descendant_nodegroup,
            resourceinstance=self.descendant_other_resource,
            data={str(self.descendant_reference_node.nodeid): [self.reference_other]},
            provisionaledits=None,
        )
        self.descendant_other_tile.save()

        ancestor_suffix = uuid.uuid4().hex[:8]
        self.ancestor_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_ancestor_{ancestor_suffix}",
            isresource=True,
        )
        self.ancestor_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.ancestor_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{ancestor_suffix}",
            alias=f"value_{ancestor_suffix}",
            datatype="reference",
            graph=self.ancestor_graph,
            nodegroup=self.ancestor_nodegroup,
            istopnode=True,
            config={"controlledList": self.reference_list_id, "multiValue": True},
        )

        self.ancestor_match_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.ancestor_graph,
        )
        self.ancestor_match_resource.save()
        self.ancestor_other_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.ancestor_graph,
        )
        self.ancestor_other_resource.save()

        self.ancestor_match_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.ancestor_nodegroup,
            resourceinstance=self.ancestor_match_resource,
            data={str(self.ancestor_reference_node.nodeid): [self.reference_parent]},
            provisionaledits=None,
        )
        self.ancestor_match_tile.save()
        self.ancestor_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.ancestor_nodegroup,
            resourceinstance=self.ancestor_other_resource,
            data={str(self.ancestor_reference_node.nodeid): [self.reference_other]},
            provisionaledits=None,
        )
        self.ancestor_other_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        self.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_reference_presence_{presence_suffix}",
            isresource=True,
        )
        self.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        self.presence_reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="reference",
            graph=self.presence_graph,
            nodegroup=self.presence_nodegroup,
            istopnode=True,
            config={"controlledList": self.reference_list_id, "multiValue": True},
        )

        self.resource_with_value = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.presence_graph,
        )
        self.resource_with_value.save()
        self.resource_without_value = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.presence_graph,
        )
        self.resource_without_value.save()

        self.tile_with_value = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.presence_nodegroup,
            resourceinstance=self.resource_with_value,
            data={str(self.presence_reference_node.nodeid): [self.reference_a]},
            provisionaledits=None,
        )
        self.tile_with_value.save()
        self.tile_without_value = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=self.presence_nodegroup,
            resourceinstance=self.resource_without_value,
            data={},
            provisionaledits=None,
        )
        self.tile_without_value.save()

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
                    "subject": [[self.any_graph.slug, self.any_reference_node.alias]],
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
                    "subject": [[self.all_graph.slug, self.all_reference_node.alias]],
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
                    "subject": [[self.only_graph.slug, self.only_reference_node.alias]],
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
                    "subject": [[self.none_graph.slug, self.none_reference_node.alias]],
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
                    "subject": [
                        [
                            self.descendant_graph.slug,
                            self.descendant_reference_node.alias,
                        ]
                    ],
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
                    "subject": [
                        [self.ancestor_graph.slug, self.ancestor_reference_node.alias]
                    ],
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
                    "subject": [
                        [self.presence_graph.slug, self.presence_reference_node.alias]
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
                    "subject": [
                        [self.presence_graph.slug, self.presence_reference_node.alias]
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

        self.assertEqual(result, {self.resource_with_value.resourceinstanceid})
