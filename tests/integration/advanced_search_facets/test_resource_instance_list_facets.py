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


class ResourceInstanceListAdvancedSearchFacetIntegrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        target_suffix = uuid.uuid4().hex[:8]
        cls.target_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_resource_instance_list_targets_{target_suffix}",
            isresource=True,
        )

        cls.reference_a_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.target_graph,
        )
        cls.reference_a_resource.save()
        cls.reference_b_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.target_graph,
        )
        cls.reference_b_resource.save()
        cls.reference_c_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.target_graph,
        )
        cls.reference_c_resource.save()

        cls.link_to_a = {
            "resourceId": str(cls.reference_a_resource.resourceinstanceid),
            "ontologyProperty": "",
            "inverseOntologyProperty": "",
            "resourceXresourceId": str(uuid.uuid4()),
        }
        cls.link_to_b = {
            "resourceId": str(cls.reference_b_resource.resourceinstanceid),
            "ontologyProperty": "",
            "inverseOntologyProperty": "",
            "resourceXresourceId": str(uuid.uuid4()),
        }
        cls.link_to_c = {
            "resourceId": str(cls.reference_c_resource.resourceinstanceid),
            "ontologyProperty": "",
            "inverseOntologyProperty": "",
            "resourceXresourceId": str(uuid.uuid4()),
        }

        any_suffix = uuid.uuid4().hex[:8]
        cls.any_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_resource_instance_list_any_{any_suffix}",
            isresource=True,
        )
        cls.any_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.any_resource_instance_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{any_suffix}",
            alias=f"value_{any_suffix}",
            datatype="resource-instance-list",
            graph=cls.any_graph,
            nodegroup=cls.any_nodegroup,
            istopnode=True,
            config={},
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
            data={str(cls.any_resource_instance_list_node.nodeid): [cls.link_to_a]},
            provisionaledits=None,
        )
        cls.any_match_tile.save()
        cls.any_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.any_nodegroup,
            resourceinstance=cls.any_other_resource,
            data={str(cls.any_resource_instance_list_node.nodeid): [cls.link_to_c]},
            provisionaledits=None,
        )
        cls.any_other_tile.save()

        all_suffix = uuid.uuid4().hex[:8]
        cls.all_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_resource_instance_list_all_{all_suffix}",
            isresource=True,
        )
        cls.all_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.all_resource_instance_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{all_suffix}",
            alias=f"value_{all_suffix}",
            datatype="resource-instance-list",
            graph=cls.all_graph,
            nodegroup=cls.all_nodegroup,
            istopnode=True,
            config={},
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
                str(cls.all_resource_instance_list_node.nodeid): [
                    cls.link_to_a,
                    cls.link_to_b,
                ]
            },
            provisionaledits=None,
        )
        cls.all_match_tile.save()
        cls.all_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.all_nodegroup,
            resourceinstance=cls.all_other_resource,
            data={str(cls.all_resource_instance_list_node.nodeid): [cls.link_to_a]},
            provisionaledits=None,
        )
        cls.all_other_tile.save()

        only_suffix = uuid.uuid4().hex[:8]
        cls.only_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_resource_instance_list_only_{only_suffix}",
            isresource=True,
        )
        cls.only_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.only_resource_instance_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{only_suffix}",
            alias=f"value_{only_suffix}",
            datatype="resource-instance-list",
            graph=cls.only_graph,
            nodegroup=cls.only_nodegroup,
            istopnode=True,
            config={},
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
                str(cls.only_resource_instance_list_node.nodeid): [
                    cls.link_to_a,
                    cls.link_to_b,
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
                str(cls.only_resource_instance_list_node.nodeid): [
                    cls.link_to_a,
                    cls.link_to_b,
                    cls.link_to_c,
                ]
            },
            provisionaledits=None,
        )
        cls.only_other_tile.save()

        none_suffix = uuid.uuid4().hex[:8]
        cls.none_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_resource_instance_list_none_{none_suffix}",
            isresource=True,
        )
        cls.none_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.none_resource_instance_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{none_suffix}",
            alias=f"value_{none_suffix}",
            datatype="resource-instance-list",
            graph=cls.none_graph,
            nodegroup=cls.none_nodegroup,
            istopnode=True,
            config={},
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
            data={str(cls.none_resource_instance_list_node.nodeid): [cls.link_to_c]},
            provisionaledits=None,
        )
        cls.none_match_tile.save()
        cls.none_other_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.none_nodegroup,
            resourceinstance=cls.none_other_resource,
            data={str(cls.none_resource_instance_list_node.nodeid): [cls.link_to_a]},
            provisionaledits=None,
        )
        cls.none_other_tile.save()

        count_suffix = uuid.uuid4().hex[:8]
        cls.count_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_resource_instance_list_count_{count_suffix}",
            isresource=True,
        )
        cls.count_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.count_resource_instance_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{count_suffix}",
            alias=f"value_{count_suffix}",
            datatype="resource-instance-list",
            graph=cls.count_graph,
            nodegroup=cls.count_nodegroup,
            istopnode=True,
            config={},
        )

        cls.count_more_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.count_graph,
        )
        cls.count_more_resource.save()
        cls.count_fewer_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.count_graph,
        )
        cls.count_fewer_resource.save()

        cls.count_more_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.count_nodegroup,
            resourceinstance=cls.count_more_resource,
            data={
                str(cls.count_resource_instance_list_node.nodeid): [
                    cls.link_to_a,
                    cls.link_to_b,
                ]
            },
            provisionaledits=None,
        )
        cls.count_more_tile.save()
        cls.count_fewer_tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.count_nodegroup,
            resourceinstance=cls.count_fewer_resource,
            data={str(cls.count_resource_instance_list_node.nodeid): [cls.link_to_a]},
            provisionaledits=None,
        )
        cls.count_fewer_tile.save()

        presence_suffix = uuid.uuid4().hex[:8]
        cls.presence_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=f"facet_resource_instance_list_presence_{presence_suffix}",
            isresource=True,
        )
        cls.presence_nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.presence_resource_instance_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"value_{presence_suffix}",
            alias=f"value_{presence_suffix}",
            datatype="resource-instance-list",
            graph=cls.presence_graph,
            nodegroup=cls.presence_nodegroup,
            istopnode=True,
            config={},
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
            data={
                str(cls.presence_resource_instance_list_node.nodeid): [cls.link_to_a]
            },
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

    def test_references_any_matches_when_any_requested_uuid_is_present(self):
        """This checks that the references any facet returns only the resource that points at at least one requested resource id."""
        payload = {
            "graph_slug": self.any_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [
                            self.any_graph.slug,
                            self.any_resource_instance_list_node.alias,
                        ]
                    ],
                    "operator": "REFERENCES_ANY",
                    "operands": [
                        {
                            "type": "LITERAL",
                            "value": [
                                str(self.reference_a_resource.resourceinstanceid),
                                str(self.reference_b_resource.resourceinstanceid),
                            ],
                        }
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

        self.assertEqual(result, {self.any_match_resource.resourceinstanceid})

    def test_references_all_matches_when_all_requested_uuids_are_present(self):
        """This checks that the references all facet returns only the resource that points at every requested resource id."""
        payload = {
            "graph_slug": self.all_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [
                            self.all_graph.slug,
                            self.all_resource_instance_list_node.alias,
                        ]
                    ],
                    "operator": "REFERENCES_ALL",
                    "operands": [
                        {
                            "type": "LITERAL",
                            "value": [
                                str(self.reference_a_resource.resourceinstanceid),
                                str(self.reference_b_resource.resourceinstanceid),
                            ],
                        }
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

        self.assertEqual(result, {self.all_match_resource.resourceinstanceid})

    def test_references_only_matches_when_no_extra_uuids_are_present(self):
        """This checks that the references only facet returns only the resource whose linked resource ids exactly match the requested set."""
        payload = {
            "graph_slug": self.only_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [
                            self.only_graph.slug,
                            self.only_resource_instance_list_node.alias,
                        ]
                    ],
                    "operator": "REFERENCES_ONLY",
                    "operands": [
                        {
                            "type": "LITERAL",
                            "value": [
                                str(self.reference_a_resource.resourceinstanceid),
                                str(self.reference_b_resource.resourceinstanceid),
                            ],
                        }
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

        self.assertEqual(result, {self.only_match_resource.resourceinstanceid})

    def test_references_none_of_matches_when_requested_uuids_are_absent(self):
        """This checks that the references none of facet returns only the resource that omits every forbidden resource id."""
        payload = {
            "graph_slug": self.none_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [
                            self.none_graph.slug,
                            self.none_resource_instance_list_node.alias,
                        ]
                    ],
                    "operator": "REFERENCES_NONE_OF",
                    "operands": [
                        {
                            "type": "LITERAL",
                            "value": [
                                str(self.reference_a_resource.resourceinstanceid),
                                str(self.reference_b_resource.resourceinstanceid),
                            ],
                        }
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

        self.assertEqual(result, {self.none_match_resource.resourceinstanceid})

    def test_count_greater_than_matches_the_row_with_more_uuid_values(self):
        """This checks that the count greater than facet returns only the resource whose linked resource count exceeds the requested threshold."""
        payload = {
            "graph_slug": self.count_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [
                            self.count_graph.slug,
                            self.count_resource_instance_list_node.alias,
                        ]
                    ],
                    "operator": "COUNT_GREATER_THAN",
                    "operands": [{"type": "LITERAL", "value": 1}],
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

        self.assertEqual(result, {self.count_more_resource.resourceinstanceid})

    def test_count_less_than_matches_the_row_with_fewer_uuid_values(self):
        """This checks that the count less than facet returns only the resource whose linked resource count falls below the requested threshold."""
        payload = {
            "graph_slug": self.count_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [
                            self.count_graph.slug,
                            self.count_resource_instance_list_node.alias,
                        ]
                    ],
                    "operator": "COUNT_LESS_THAN",
                    "operands": [{"type": "LITERAL", "value": 2}],
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

        self.assertEqual(result, {self.count_fewer_resource.resourceinstanceid})

    def test_has_no_value_matches_the_resource_without_a_uuid_row(self):
        """This checks that the has no value facet returns only the resource whose resource-instance-list tile indexed no linked resources at all."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [
                            self.presence_graph.slug,
                            self.presence_resource_instance_list_node.alias,
                        ]
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

    def test_has_any_value_matches_the_resource_with_a_uuid_row(self):
        """This checks that the has any value facet returns only the resource whose resource-instance-list tile indexed linked resources."""
        payload = {
            "graph_slug": self.presence_graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [
                            self.presence_graph.slug,
                            self.presence_resource_instance_list_node.alias,
                        ]
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
