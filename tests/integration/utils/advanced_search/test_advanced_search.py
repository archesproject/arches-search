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


PERSON_A_ID = uuid.UUID("d631f6e1-9da3-4236-93c8-7cda90a61536")
PERSON_B_ID = uuid.UUID("77eddfe7-289a-464b-ae2d-8a442f298d99")
PERSON_C_ID = uuid.UUID("60de0174-b81a-4efa-ba3b-83fbb1c5e075")
DOG_A_ID = uuid.UUID("b244d246-6aa1-40fc-a026-12c8fd592b4f")
DOG_B_ID = uuid.UUID("a35350c3-cb18-41e7-b979-c34225486579")


class AdvancedSearchTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_fixture_models()
        cls._create_person_a_resource_instance_and_tiles()
        cls._create_person_b_resource_instance_and_tiles()
        cls._create_person_c_resource_instance_and_tiles()
        cls._create_dog_a_resource_instance_and_tiles()
        cls._create_dog_b_resource_instance_and_tiles()
        cls._reindex_advanced_search_tables()

    @classmethod
    def _create_fixture_models(cls):
        cls._create_graph_models()
        cls._create_nodegroups()
        cls._create_graph_nodes()

    @classmethod
    def _create_graph_models(cls):
        cls.person_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="person",
            isresource=True,
        )
        cls.dog_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="dog",
            isresource=True,
        )

    @classmethod
    def _create_nodegroups(cls):
        cls.fingernail_length = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.age = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.alias = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="n",
        )
        cls.mother = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.friends = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.pets = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.tail_length = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        cls.favorite_person = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )

    @classmethod
    def _create_graph_nodes(cls):
        cls._create_person_graph_nodes()
        cls._create_dog_graph_nodes()

    @classmethod
    def _create_person_graph_nodes(cls):
        cls.fingernail_length_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="fingernail_length",
            alias="fingernail_length",
            datatype="number",
            graph=cls.person_graph,
            nodegroup=cls.fingernail_length,
            istopnode=True,
        )
        cls.age_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="age",
            alias="age",
            datatype="number",
            graph=cls.person_graph,
            nodegroup=cls.age,
            istopnode=True,
        )
        cls.first_name_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="first_name",
            alias="first_name",
            datatype="string",
            graph=cls.person_graph,
            nodegroup=cls.alias,
            istopnode=True,
        )
        cls.last_name_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="last_name",
            alias="last_name",
            datatype="string",
            graph=cls.person_graph,
            nodegroup=cls.alias,
            istopnode=False,
        )
        cls.mother_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="mother",
            alias="mother",
            datatype="resource-instance",
            graph=cls.person_graph,
            nodegroup=cls.mother,
            istopnode=True,
        )
        cls.friends_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="friends",
            alias="friends",
            datatype="resource-instance-list",
            graph=cls.person_graph,
            nodegroup=cls.friends,
            istopnode=True,
        )
        cls.pets_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="pets",
            alias="pets",
            datatype="resource-instance-list",
            graph=cls.person_graph,
            nodegroup=cls.pets,
            istopnode=True,
        )

    @classmethod
    def _create_dog_graph_nodes(cls):
        cls.tail_length_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="tail_length",
            alias="tail_length",
            datatype="number",
            graph=cls.dog_graph,
            nodegroup=cls.tail_length,
            istopnode=True,
        )
        cls.favorite_person_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="favorite_person",
            alias="favorite_person",
            datatype="resource-instance",
            graph=cls.dog_graph,
            nodegroup=cls.favorite_person,
            istopnode=True,
        )

    @classmethod
    def _create_person_a_resource_instance_and_tiles(cls):
        cls.person_a = ResourceInstance(
            resourceinstanceid=PERSON_A_ID,
            graph=cls.person_graph,
        )
        cls.person_a.save()

        person_a_fingernail_length_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.fingernail_length,
            resourceinstance=cls.person_a,
            data={str(cls.fingernail_length_node.nodeid): 25},
            provisionaledits=None,
        )
        person_a_fingernail_length_tile_model.save()

        person_a_age_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.age,
            resourceinstance=cls.person_a,
            data={str(cls.age_node.nodeid): 22},
            provisionaledits=None,
        )
        person_a_age_tile_model.save()

        person_a_primary_alias_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.alias,
            resourceinstance=cls.person_a,
            data={
                str(cls.first_name_node.nodeid): {
                    "en": {"value": "FOO", "direction": "ltr"}
                },
                str(cls.last_name_node.nodeid): {
                    "en": {"value": "CHILD", "direction": "ltr"}
                },
            },
            provisionaledits=None,
        )
        person_a_primary_alias_tile_model.save()

        person_a_secondary_alias_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.alias,
            resourceinstance=cls.person_a,
            data={
                str(cls.first_name_node.nodeid): {
                    "en": {"value": "bar", "direction": "ltr"}
                },
                str(cls.last_name_node.nodeid): {
                    "en": {"value": "foo", "direction": "ltr"}
                },
            },
            provisionaledits=None,
        )
        person_a_secondary_alias_tile_model.save()

        person_a_mother_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.mother,
            resourceinstance=cls.person_a,
            data={
                str(cls.mother_node.nodeid): [
                    {
                        "resourceId": str(PERSON_B_ID),
                        "ontologyProperty": "",
                        "inverseOntologyProperty": "",
                        "resourceXresourceId": str(uuid.uuid4()),
                    }
                ]
            },
            provisionaledits=None,
        )
        person_a_mother_tile_model.save()

        person_a_friends_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.friends,
            resourceinstance=cls.person_a,
            data={
                str(cls.friends_node.nodeid): [
                    {
                        "resourceId": str(PERSON_C_ID),
                        "ontologyProperty": "",
                        "inverseOntologyProperty": "",
                        "resourceXresourceId": str(uuid.uuid4()),
                    }
                ]
            },
            provisionaledits=None,
        )
        person_a_friends_tile_model.save()

    @classmethod
    def _create_person_b_resource_instance_and_tiles(cls):
        cls.person_b = ResourceInstance(
            resourceinstanceid=PERSON_B_ID,
            graph=cls.person_graph,
        )
        cls.person_b.save()

        person_b_fingernail_length_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.fingernail_length,
            resourceinstance=cls.person_b,
            data={str(cls.fingernail_length_node.nodeid): 10},
            provisionaledits=None,
        )
        person_b_fingernail_length_tile_model.save()

        person_b_age_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.age,
            resourceinstance=cls.person_b,
            data={str(cls.age_node.nodeid): None},
            provisionaledits=None,
        )
        person_b_age_tile_model.save()

        person_b_primary_alias_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.alias,
            resourceinstance=cls.person_b,
            data={
                str(cls.first_name_node.nodeid): {
                    "en": {"value": "INCOGNITO", "direction": "ltr"}
                },
                str(cls.last_name_node.nodeid): {
                    "en": {"value": "MOTHER", "direction": "ltr"}
                },
            },
            provisionaledits=None,
        )
        person_b_primary_alias_tile_model.save()

        person_b_secondary_alias_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.alias,
            resourceinstance=cls.person_b,
            data={
                str(cls.first_name_node.nodeid): {
                    "en": {"value": "NAME", "direction": "ltr"}
                },
                str(cls.last_name_node.nodeid): {
                    "en": {"value": "REAL", "direction": "ltr"}
                },
            },
            provisionaledits=None,
        )
        person_b_secondary_alias_tile_model.save()

        person_b_friends_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.friends,
            resourceinstance=cls.person_b,
            data={
                str(cls.friends_node.nodeid): [
                    {
                        "resourceId": str(PERSON_A_ID),
                        "ontologyProperty": "",
                        "inverseOntologyProperty": "",
                        "resourceXresourceId": str(uuid.uuid4()),
                    },
                    {
                        "resourceId": str(PERSON_C_ID),
                        "ontologyProperty": "",
                        "inverseOntologyProperty": "",
                        "resourceXresourceId": str(uuid.uuid4()),
                    },
                ]
            },
            provisionaledits=None,
        )
        person_b_friends_tile_model.save()

        person_b_pets_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.pets,
            resourceinstance=cls.person_b,
            data={
                str(cls.pets_node.nodeid): [
                    {
                        "resourceId": str(DOG_A_ID),
                        "ontologyProperty": "",
                        "inverseOntologyProperty": "",
                        "resourceXresourceId": str(uuid.uuid4()),
                    }
                ]
            },
            provisionaledits=None,
        )
        person_b_pets_tile_model.save()

    @classmethod
    def _create_person_c_resource_instance_and_tiles(cls):
        cls.person_c = ResourceInstance(
            resourceinstanceid=PERSON_C_ID,
            graph=cls.person_graph,
        )
        cls.person_c.save()

        person_c_fingernail_length_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.fingernail_length,
            resourceinstance=cls.person_c,
            data={str(cls.fingernail_length_node.nodeid): 55},
            provisionaledits=None,
        )
        person_c_fingernail_length_tile_model.save()

        person_c_age_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.age,
            resourceinstance=cls.person_c,
            data={str(cls.age_node.nodeid): 24},
            provisionaledits=None,
        )
        person_c_age_tile_model.save()

        person_c_alias_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.alias,
            resourceinstance=cls.person_c,
            data={
                str(cls.first_name_node.nodeid): {
                    "en": {"value": "FRIEND", "direction": "ltr"}
                },
                str(cls.last_name_node.nodeid): {
                    "en": {"value": "FRIEND!", "direction": "ltr"}
                },
            },
            provisionaledits=None,
        )
        person_c_alias_tile_model.save()

        person_c_pets_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.pets,
            resourceinstance=cls.person_c,
            data={
                str(cls.pets_node.nodeid): [
                    {
                        "resourceId": str(DOG_B_ID),
                        "ontologyProperty": "",
                        "inverseOntologyProperty": "",
                        "resourceXresourceId": str(uuid.uuid4()),
                    }
                ]
            },
            provisionaledits=None,
        )
        person_c_pets_tile_model.save()

    @classmethod
    def _create_dog_a_resource_instance_and_tiles(cls):
        cls.dog_a = ResourceInstance(
            resourceinstanceid=DOG_A_ID,
            graph=cls.dog_graph,
        )
        cls.dog_a.save()

        dog_a_tail_length_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.tail_length,
            resourceinstance=cls.dog_a,
            data={str(cls.tail_length_node.nodeid): 25},
            provisionaledits=None,
        )
        dog_a_tail_length_tile_model.save()

        dog_a_favorite_person_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.favorite_person,
            resourceinstance=cls.dog_a,
            data={
                str(cls.favorite_person_node.nodeid): [
                    {
                        "resourceId": str(PERSON_A_ID),
                        "ontologyProperty": "",
                        "inverseOntologyProperty": "",
                        "resourceXresourceId": str(uuid.uuid4()),
                    }
                ]
            },
            provisionaledits=None,
        )
        dog_a_favorite_person_tile_model.save()

    @classmethod
    def _create_dog_b_resource_instance_and_tiles(cls):
        cls.dog_b = ResourceInstance(
            resourceinstanceid=DOG_B_ID,
            graph=cls.dog_graph,
        )
        cls.dog_b.save()

        dog_b_tail_length_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.tail_length,
            resourceinstance=cls.dog_b,
            data={str(cls.tail_length_node.nodeid): 999},
            provisionaledits=None,
        )
        dog_b_tail_length_tile_model.save()

        dog_b_favorite_person_tile_model = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=cls.favorite_person,
            resourceinstance=cls.dog_b,
            data={
                str(cls.favorite_person_node.nodeid): [
                    {
                        "resourceId": str(PERSON_C_ID),
                        "ontologyProperty": "",
                        "inverseOntologyProperty": "",
                        "resourceXresourceId": str(uuid.uuid4()),
                    }
                ]
            },
            provisionaledits=None,
        )
        dog_b_favorite_person_tile_model.save()

    @classmethod
    def _reindex_advanced_search_tables(cls):
        call_command("db_index", "reindex_database")

    def _compile(self, payload):
        return set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

    def test_dog_baseline_returns_all_dogs(self):
        """
        Verifies that an empty query with no clauses, groups, or relationship returns all resources
        of the specified graph type.
        """
        result = self._compile(
            {
                "graph_slug": "dog",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {DOG_A_ID, DOG_B_ID})

    def test_person_age_greater_than_18(self):
        """
        Tests the GREATER_THAN numeric operator. Matches the two people with ages above 18 and
        excludes Person B whose age tile stores a null value.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "age"]],
                        "operator": "GREATER_THAN",
                        "operands": [{"type": "LITERAL", "value": 18}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_age_equals_22_or_24(self):
        """
        Tests top-level OR logic combining two EQUALS clauses on the same numeric field. Each
        person is matched by a different OR branch; Person B with a null age satisfies neither.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "OR",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "age"]],
                        "operator": "EQUALS",
                        "operands": [{"type": "LITERAL", "value": 22}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "age"]],
                        "operator": "EQUALS",
                        "operands": [{"type": "LITERAL", "value": 24}],
                    },
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_fingernail_length_lte_50(self):
        """
        Tests the LESS_THAN_OR_EQUALS numeric operator. Matches the two people with fingernail
        lengths at or below 50 and excludes Person C at 55.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "fingernail_length"]],
                        "operator": "LESS_THAN_OR_EQUALS",
                        "operands": [{"type": "LITERAL", "value": 50}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_person_has_no_age(self):
        """
        Tests the HAS_NO_VALUE operator on a numeric field. Matches only Person B, whose age tile
        stores an explicit null rather than a numeric value.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "age"]],
                        "operator": "HAS_NO_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_person_no_age_or_fingernail_lte_25_or_fingernail_gt_50(self):
        """
        Tests top-level OR logic with three heterogeneous clauses: a HAS_NO_VALUE condition and
        two numeric range conditions. All three people match, each satisfying a different branch.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "OR",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "age"]],
                        "operator": "HAS_NO_VALUE",
                        "operands": [],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "fingernail_length"]],
                        "operator": "LESS_THAN_OR_EQUALS",
                        "operands": [{"type": "LITERAL", "value": 25}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "fingernail_length"]],
                        "operator": "GREATER_THAN",
                        "operands": [{"type": "LITERAL", "value": 50}],
                    },
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID, PERSON_C_ID})

    def test_person_grouped_no_age_and_fingernail_10_or_fingernail_gt_50(self):
        """
        Tests a nested AND group participating in the outer OR logic. Person B is matched by the
        nested AND group (no age and fingernail=10); Person C is matched by the standalone
        GREATER_THAN clause in the outer OR.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "OR",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "fingernail_length"]],
                        "operator": "GREATER_THAN",
                        "operands": [{"type": "LITERAL", "value": 50}],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "HAS_NO_VALUE",
                                "operands": [],
                            },
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "fingernail_length"]],
                                "operator": "EQUALS",
                                "operands": [{"type": "LITERAL", "value": 10}],
                            },
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                ],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID, PERSON_C_ID})

    def test_person_has_no_value_friends(self):
        """
        Tests HAS_NO_VALUE on a resource-instance-list field. Matches only Person C, the only
        person whose friends tile holds no references.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_NO_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_C_ID})

    def test_person_resource_scope_cross_tile_failure(self):
        """
        Tests that resource scope AND still requires all clauses to be satisfied by the same
        resource. No person simultaneously has INCOGNITO as a first name and FOO as a last name.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "first_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "last_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "FOO"}],
                    },
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, set())

    def test_person_resource_scope_cross_tile_success(self):
        """
        Tests that resource scope allows AND conditions to be satisfied across different tiles of
        the same resource. Person B has INCOGNITO on one alias tile and REAL on another, which
        resource scope accepts.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "first_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "last_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "REAL"}],
                    },
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_person_tile_scope_cross_tile_failure(self):
        """
        Tests that tile scope AND requires all conditions to be co-located on the same tile.
        INCOGNITO and REAL exist on separate alias tiles for Person B, so no tile satisfies both.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "TILE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "first_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "last_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "REAL"}],
                    },
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, set())

    def test_person_tile_scope_same_tile_success(self):
        """
        Tests that tile scope AND matches when all conditions are satisfied within a single tile.
        INCOGNITO and MOTHER both appear on Person B's primary alias tile.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "TILE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "first_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "last_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "MOTHER"}],
                    },
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_person_is_some_dogs_favorite_person(self):
        """
        Tests inverse relationship traversal with ANY quantifier and a RELATED clause. A person
        matches if at least one dog's favorite_person node references them.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["dog", "favorite_person"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "dog",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_dog_tail_gte_person_fingernail(self):
        """
        Tests a PATH operand in a RELATED clause, comparing the child resource's numeric field
        against the anchor resource's numeric field. A person matches if the dog pointing at them
        has a tail length at least as large as the person's fingernail length.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["dog", "tail_length"]],
                        "operator": "GREATER_THAN_OR_EQUALS",
                        "operands": [
                            {"type": "PATH", "value": [["person", "fingernail_length"]]}
                        ],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "dog",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_dog_tail_equals_person_fingernail(self):
        """
        Tests a PATH operand EQUALS comparison between two resources. Only Person A matches
        because Dog A's tail length (25) equals Person A's fingernail length (25); Dog B's
        tail of 999 does not equal Person C's fingernail of 55.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["dog", "tail_length"]],
                        "operator": "EQUALS",
                        "operands": [
                            {"type": "PATH", "value": [["person", "fingernail_length"]]}
                        ],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "dog",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_person_dog_tail_lt_person_fingernail(self):
        """
        Tests a PATH operand LESS_THAN comparison that no pair satisfies. Dog A (tail=25) is not
        less than Person A's fingernail (25), and Dog B (tail=999) is not less than Person C's
        fingernail (55), so no person matches.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["dog", "tail_length"]],
                        "operator": "LESS_THAN",
                        "operands": [
                            {"type": "PATH", "value": [["person", "fingernail_length"]]}
                        ],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "dog",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, set())

    def test_friends_all_friends_lt_18(self):
        """
        Tests the ALL traversal quantifier with a filter that no child resource satisfies. No
        person matches because no friend in the fixture data has an age below 18, so ALL cannot
        be satisfied.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "LESS_THAN",
                                "operands": [{"type": "LITERAL", "value": 18}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, set())

    def test_friends_all_friends_gt_18(self):
        """
        Tests the ALL traversal quantifier with a filter that every relevant child satisfies.
        Every friend of Person A and Person B is older than 18, so both match.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "GREATER_THAN",
                                "operands": [{"type": "LITERAL", "value": 18}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_friends_any_friend_age_22(self):
        """
        Tests the ANY traversal quantifier with a specific age filter. Only Person B has a friend
        (Person A, age 22) satisfying the condition; Person A's only friend is Person C (age 24).
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "EQUALS",
                                "operands": [{"type": "LITERAL", "value": 22}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_people_all_friends_have_any_pet_tail_gt_10(self):
        """
        Tests ALL+ANY nested traversal quantifiers across two relationship levels (friends then
        pets). Person A's only friend is Person C, who has Dog B (tail=999 > 10), so ALL is
        satisfied. Person B has Person A as a friend, and Person A has no pets, so Person B fails.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [
                            {
                                "graph_slug": "dog",
                                "scope": "RESOURCE",
                                "logic": "AND",
                                "clauses": [
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": [["dog", "tail_length"]],
                                        "operator": "GREATER_THAN",
                                        "operands": [{"type": "LITERAL", "value": 10}],
                                    }
                                ],
                                "groups": [],
                                "aggregations": [],
                                "relationship": None,
                            }
                        ],
                        "aggregations": [],
                        "relationship": {
                            "path": [["person", "pets"]],
                            "is_inverse": False,
                            "traversal_quantifiers": ["ANY"],
                        },
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_people_all_friends_have_any_pet_tail_lt_10(self):
        """
        Tests ALL+ANY nested traversal quantifiers where the filter matches no existing pet.
        No person matches because no dog in the fixture has a tail under 10 — Dog A is 25 and
        Dog B is 999.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [
                            {
                                "graph_slug": "dog",
                                "scope": "RESOURCE",
                                "logic": "AND",
                                "clauses": [
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": [["dog", "tail_length"]],
                                        "operator": "LESS_THAN",
                                        "operands": [{"type": "LITERAL", "value": 10}],
                                    }
                                ],
                                "groups": [],
                                "aggregations": [],
                                "relationship": None,
                            }
                        ],
                        "aggregations": [],
                        "relationship": {
                            "path": [["person", "pets"]],
                            "is_inverse": False,
                            "traversal_quantifiers": ["ANY"],
                        },
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, set())

    def test_people_any_friend_has_any_pet_tail_gt_25(self):
        """
        Tests ANY+ANY nested traversal quantifiers. Both Person A and Person B have Person C as
        a friend, and Person C owns Dog B (tail=999 > 25), so both match.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [
                            {
                                "graph_slug": "dog",
                                "scope": "RESOURCE",
                                "logic": "AND",
                                "clauses": [
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": [["dog", "tail_length"]],
                                        "operator": "GREATER_THAN",
                                        "operands": [{"type": "LITERAL", "value": 25}],
                                    }
                                ],
                                "groups": [],
                                "aggregations": [],
                                "relationship": None,
                            }
                        ],
                        "aggregations": [],
                        "relationship": {
                            "path": [["person", "pets"]],
                            "is_inverse": False,
                            "traversal_quantifiers": ["ANY"],
                        },
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_people_any_friend_no_pet_with_tail_999(self):
        """
        Tests ANY+NONE nested traversal quantifiers. NONE requires that the child resource has at
        least one pet and none of them match the filter — a friend with no pets fails NONE just
        like a friend whose pet matches. Person C's pet Dog B has tail=999 (fails NONE); Person A
        has no pets at all (also fails NONE because no pets exist). No person has a qualifying friend.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [
                            {
                                "graph_slug": "dog",
                                "scope": "RESOURCE",
                                "logic": "AND",
                                "clauses": [
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": [["dog", "tail_length"]],
                                        "operator": "EQUALS",
                                        "operands": [{"type": "LITERAL", "value": 999}],
                                    }
                                ],
                                "groups": [],
                                "aggregations": [],
                                "relationship": None,
                            }
                        ],
                        "aggregations": [],
                        "relationship": {
                            "path": [["person", "pets"]],
                            "is_inverse": False,
                            "traversal_quantifiers": ["NONE"],
                        },
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, set())

    def test_people_any_friend_no_pet_with_tail_25(self):
        """
        Tests ANY+NONE nested traversal quantifiers where a qualifying path exists. Person C has
        Dog B (tail=999), so Person C satisfies NONE(pets, tail=25). Both Person A and Person B
        have Person C as a friend, so both match.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [
                            {
                                "graph_slug": "dog",
                                "scope": "RESOURCE",
                                "logic": "AND",
                                "clauses": [
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": [["dog", "tail_length"]],
                                        "operator": "EQUALS",
                                        "operands": [{"type": "LITERAL", "value": 25}],
                                    }
                                ],
                                "groups": [],
                                "aggregations": [],
                                "relationship": None,
                            }
                        ],
                        "aggregations": [],
                        "relationship": {
                            "path": [["person", "pets"]],
                            "is_inverse": False,
                            "traversal_quantifiers": ["NONE"],
                        },
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_person_any_friends_no_inner_filters(self):
        """
        Tests ANY traversal quantifier with no inner filter — requires only that at least one
        related resource exists. Matches the two people who have at least one friend.
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
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_person_none_friends_no_inner_filters(self):
        """
        Tests NONE traversal quantifier with no inner filter — matches resources that have no
        related resources at all. Matches only Person C, the only person with no friends.
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
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["NONE"],
                },
            }
        )
        self.assertEqual(result, {PERSON_C_ID})

    def test_person_all_friends_no_inner_filters(self):
        """
        Tests ALL traversal quantifier with no inner filter. ALL without filters still requires
        at least one related resource to exist, so it matches the two people who have friends.
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
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_person_inverse_friends_is_someones_friend(self):
        """
        Tests inverse traversal of the friends relationship with ANY quantifier. Matches the
        people who appear in at least one other person's friends list.
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
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_none_dogs_favorite_person_relationship_returns_only_person_b(self):
        """
        Tests inverse traversal with NONE quantifier and no inner filter. Matches the only person
        who is not referenced as a favorite person by any dog.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [],
                "groups": [
                    {
                        "graph_slug": "dog",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["NONE"],
                },
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_person_tile_scope_or_matches_incognito_or_mother_on_the_same_alias_tile(
        self,
    ):
        """
        Tests OR logic at tile scope across two fields of the same nodegroup. A resource matches
        if any single tile satisfies at least one OR branch. Person B matches via the alias tile
        that contains both INCOGNITO (first_name) and MOTHER (last_name).
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "TILE",
                "logic": "OR",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "first_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "last_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "MOTHER"}],
                    },
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_person_resource_scope_returns_no_results_for_a_wrong_graph_subject(self):
        """
        Tests that a clause whose subject references a node from a different graph (dog.tail_length)
        returns no results when querying the person graph without a relationship path linking them.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["dog", "tail_length"]],
                        "operator": "GREATER_THAN",
                        "operands": [{"type": "LITERAL", "value": 0}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, set())

    def test_person_fingernail_length_equals_10_returns_only_person_b(self):
        """
        Tests the EQUALS numeric operator at an exact boundary value. Matches only Person B
        whose fingernail length is exactly 10; Person A (25) and Person C (55) do not match.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "fingernail_length"]],
                        "operator": "EQUALS",
                        "operands": [{"type": "LITERAL", "value": 10}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_person_tile_scope_nested_and_group_still_enforces_same_tile_co_occurrence(
        self,
    ):
        """
        Tests that tile scope co-occurrence is preserved even when conditions are split across a
        parent group and a nested child group. Person B matches because INCOGNITO and MOTHER are
        on the same alias tile; a split across tiles would not match.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "TILE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "first_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "TILE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "last_name"]],
                                "operator": "LIKE",
                                "operands": [{"type": "LITERAL", "value": "MOTHER"}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_person_all_friends_age_greater_than_18_with_anchor_fingernail_length_lte_50_returns_a_and_b(
        self,
    ):
        """
        Tests that a literal clause on the anchor resource is applied alongside the ALL traversal
        filter. Person A and Person B each have fingernail_length ≤ 50 (passing the anchor filter)
        and all their friends are over 18 (passing ALL). Person C's fingernail is 55 so they fail
        the anchor filter before the traversal is considered.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "fingernail_length"]],
                        "operator": "LESS_THAN_OR_EQUALS",
                        "operands": [{"type": "LITERAL", "value": 50}],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "GREATER_THAN",
                                "operands": [{"type": "LITERAL", "value": 18}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_person_pets_has_any_value_returns_people_with_pets(self):
        """
        Tests HAS_ANY_VALUE on a resource-instance-list field without a relationship traversal.
        Matches the two people whose pets tile holds at least one reference.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "pets"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID, PERSON_C_ID})

    def test_person_pets_has_no_value_returns_only_person_a(self):
        """
        Tests HAS_NO_VALUE on a resource-instance-list field without a relationship traversal.
        Matches only Person A, the only person with no pet references.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "pets"]],
                        "operator": "HAS_NO_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_person_mother_has_no_value_returns_person_b_and_person_c(self):
        """
        Tests HAS_NO_VALUE on a resource-instance (single-value) field. Matches the two people
        who have no mother reference stored.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "mother"]],
                        "operator": "HAS_NO_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID, PERSON_C_ID})

    def test_person_mother_has_any_value_returns_only_person_a(self):
        """
        Tests HAS_ANY_VALUE on a resource-instance (single-value) field. Matches only Person A,
        the only person with a stored mother reference.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "mother"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_person_any_friend_age_greater_than_23_returns_person_a_and_person_b(self):
        """
        Tests ANY traversal quantifier with a numeric filter on related resources. Both Person A
        and Person B list Person C (age 24) as a friend, satisfying the GREATER_THAN 23 condition.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "GREATER_THAN",
                                "operands": [{"type": "LITERAL", "value": 23}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_person_any_friend_age_greater_than_100_returns_no_people(self):
        """
        Tests ANY traversal quantifier with a filter that no related resource satisfies. No person
        matches because no fixture friend has an age above 100.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["person", "friends"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "GREATER_THAN",
                                "operands": [{"type": "LITERAL", "value": 100}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, set())

    def test_person_none_friends_age_greater_than_or_equal_to_30_returns_person_a_and_person_b(
        self,
    ):
        """
        Tests NONE traversal quantifier with a filter that no actual friend satisfies. Matches
        the two people who have friends, since none of those friends are 30 or older — NONE
        requires that friends exist but none match the filter.
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
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "GREATER_THAN_OR_EQUALS",
                                "operands": [{"type": "LITERAL", "value": 30}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["NONE"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_person_all_friends_age_greater_than_or_equal_to_24_returns_only_person_a(
        self,
    ):
        """
        Tests ALL traversal quantifier where only one person has all friends satisfying the
        condition. Person A's only friend is Person C (age 24, passes ≥ 24). Person B also has
        Person A (age 22) as a friend, who fails the filter.
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
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "GREATER_THAN_OR_EQUALS",
                                "operands": [{"type": "LITERAL", "value": 24}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_person_all_friends_have_any_pets_returns_only_person_a(self):
        """
        Tests ALL traversal with a HAS_ANY_VALUE inner clause on the related resource. Person A's
        only friend is Person C who has pets. Person B also has Person A as a friend, and Person A
        has no pets, so not all of Person B's friends satisfy the condition.
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
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "pets"]],
                                "operator": "HAS_ANY_VALUE",
                                "operands": [],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_person_all_friends_have_no_pets_returns_no_people(self):
        """
        Tests ALL traversal with a HAS_NO_VALUE inner clause where the filter is never universally
        satisfied. Returns no people because Person C (a friend of both Person A and B) has pets,
        so no person's friends all lack pets.
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
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "pets"]],
                                "operator": "HAS_NO_VALUE",
                                "operands": [],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, set())

    def test_person_any_friends_have_no_pets_returns_only_person_b(self):
        """
        Tests ANY traversal with a HAS_NO_VALUE inner clause. Person B has Person A as a friend
        and Person A has no pets, satisfying the condition. Person A's only friend is Person C
        who has pets, so Person A does not match.
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
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "pets"]],
                                "operator": "HAS_NO_VALUE",
                                "operands": [],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_person_any_friends_who_are_any_dogs_favorite_person_returns_person_a_and_person_b(
        self,
    ):
        """
        Tests nested traversal where the inner group itself uses an inverse relationship. A person
        matches if at least one of their friends is pointed at by at least one dog as its favorite
        person. Person A's friend Person C is Dog B's favorite; Person B's friend Person C is also
        Dog B's favorite.
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
                        "groups": [],
                        "aggregations": [],
                        "relationship": {
                            "path": [["dog", "favorite_person"]],
                            "is_inverse": True,
                            "traversal_quantifiers": ["ANY"],
                        },
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_person_age_greater_than_23_or_is_some_dogs_favorite_person_returns_person_a_and_person_c(
        self,
    ):
        """
        Tests OR at the root level combining a literal clause with a relationship group. Person C
        (age 24) matches both branches; Person A matches only via the inverse-relationship branch
        (Dog A's favorite person); Person B matches neither.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "OR",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "age"]],
                        "operator": "GREATER_THAN",
                        "operands": [{"type": "LITERAL", "value": 23}],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "RELATED",
                                "quantifier": "ANY",
                                "subject": [["dog", "favorite_person"]],
                                "operator": "HAS_ANY_VALUE",
                                "operands": [],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": {
                            "path": [["dog", "favorite_person"]],
                            "is_inverse": True,
                            "traversal_quantifiers": ["ANY"],
                        },
                    }
                ],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_with_any_inverse_favorite_person_dog_tail_length_less_than_100_returns_only_person_a(
        self,
    ):
        """
        Tests inverse traversal (dogs pointing at a person) combined with a literal filter on the
        child dog. Person A is pointed at by Dog A (tail=25 < 100). Person C is pointed at only
        by Dog B (tail=999, fails the filter).
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["dog", "favorite_person"]],
                        "operator": "HAS_ANY_VALUE",
                        "operands": [],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "dog",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["dog", "tail_length"]],
                                "operator": "LESS_THAN",
                                "operands": [{"type": "LITERAL", "value": 100}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID})

    def test_person_all_inverse_favorite_person_dogs_tail_length_greater_than_or_equal_to_fingernail_length_returns_person_a_and_person_c(
        self,
    ):
        """
        Tests ALL over an inverse relationship with a PATH operand comparing each dog's tail
        length to the anchor person's fingernail length. ALL is internally converted to ANY for
        single-hop inverse traversals, requiring at least one qualifying dog. Person B has no dogs
        pointing at them and is excluded; Person A and Person C each have one dog that passes.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "RELATED",
                        "quantifier": "ANY",
                        "subject": [["dog", "tail_length"]],
                        "operator": "GREATER_THAN_OR_EQUALS",
                        "operands": [
                            {"type": "PATH", "value": [["person", "fingernail_length"]]}
                        ],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "dog",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_dog_tail_length_greater_than_or_equal_to_900_returns_only_dog_b(self):
        """
        Tests GREATER_THAN_OR_EQUALS on the dog graph's tail_length field. Only Dog B (tail=999)
        meets the threshold; Dog A (tail=25) does not.
        """
        result = self._compile(
            {
                "graph_slug": "dog",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["dog", "tail_length"]],
                        "operator": "GREATER_THAN_OR_EQUALS",
                        "operands": [{"type": "LITERAL", "value": 900}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {DOG_B_ID})

    def test_dog_favorite_person_age_greater_than_23_returns_only_dog_b(self):
        """
        Tests forward traversal from dog to person with a numeric filter on the related person.
        Dog B points to Person C (age 24 > 23). Dog A points to Person A (age 22, fails).
        """
        result = self._compile(
            {
                "graph_slug": "dog",
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
                                "subject": [["person", "age"]],
                                "operator": "GREATER_THAN",
                                "operands": [{"type": "LITERAL", "value": 23}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {DOG_B_ID})

    def test_dog_favorite_person_has_no_value_friends_returns_only_dog_b(self):
        """
        Tests forward traversal from dog to person where the inner filter uses HAS_NO_VALUE on
        the person's friends field. Dog B points to Person C who has no friends. Dog A points to
        Person A who does have friends.
        """
        result = self._compile(
            {
                "graph_slug": "dog",
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
                                "subject": [["person", "friends"]],
                                "operator": "HAS_NO_VALUE",
                                "operands": [],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {DOG_B_ID})

    def test_dog_any_inverse_owners_via_pets_returns_both_dogs(self):
        """
        Tests inverse traversal via the person.pets relationship with ANY quantifier and no inner
        filter. Both dogs appear in at least one person's pets list, so both match.
        """
        result = self._compile(
            {
                "graph_slug": "dog",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "pets"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {DOG_A_ID, DOG_B_ID})

    def test_dog_none_inverse_owners_via_pets_returns_no_dogs(self):
        """
        Tests inverse traversal with NONE quantifier and no inner filter. No dog matches because
        both dogs are referenced in at least one person's pets list, failing the NONE condition.
        """
        result = self._compile(
            {
                "graph_slug": "dog",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "pets"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["NONE"],
                },
            }
        )
        self.assertEqual(result, set())

    def test_dog_all_inverse_owners_age_greater_than_20_returns_only_dog_b(self):
        """
        Tests ALL inverse traversal with an age filter (converted to ANY for single-hop inverse).
        Dog B is owned by Person C (age 24, passes > 20). Dog A is owned by Person B whose age
        is null and fails the GREATER_THAN filter.
        """
        result = self._compile(
            {
                "graph_slug": "dog",
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
                                "subject": [["person", "age"]],
                                "operator": "GREATER_THAN",
                                "operands": [{"type": "LITERAL", "value": 20}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "pets"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ALL"],
                },
            }
        )
        self.assertEqual(result, {DOG_B_ID})

    def test_dog_owner_with_any_friend_age_equals_22_returns_only_dog_a(self):
        """
        Tests nested traversal from dog to its inverse owner (via person.pets) and then from
        owner to owner's friends. Dog A is owned by Person B, and Person B has Person A (age 22)
        as a friend. Dog B's owner (Person C) has no friends.
        """
        result = self._compile(
            {
                "graph_slug": "dog",
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
                                        "subject": [["person", "age"]],
                                        "operator": "EQUALS",
                                        "operands": [{"type": "LITERAL", "value": 22}],
                                    }
                                ],
                                "groups": [],
                                "aggregations": [],
                                "relationship": None,
                            }
                        ],
                        "aggregations": [],
                        "relationship": {
                            "path": [["person", "friends"]],
                            "is_inverse": False,
                            "traversal_quantifiers": ["ANY"],
                        },
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "pets"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {DOG_A_ID})

    def test_person_tile_scope_like_with_exact_punctuation_returns_only_person_c(self):
        """
        Tests that the LIKE string operator preserves special characters in the match value.
        Only Person C has the last name "FRIEND!" including the exclamation mark.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "TILE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "last_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "FRIEND!"}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_C_ID})

    def test_person_conflicting_fingernail_length_constraints_return_no_people(self):
        """
        Tests that mutually exclusive AND clauses on the same numeric field return no results.
        A value cannot be simultaneously greater than 50 and less than or equal to 50.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "fingernail_length"]],
                        "operator": "GREATER_THAN",
                        "operands": [{"type": "LITERAL", "value": 50}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "fingernail_length"]],
                        "operator": "LESS_THAN_OR_EQUALS",
                        "operands": [{"type": "LITERAL", "value": 50}],
                    },
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, set())

    def test_person_fingernail_length_less_than_or_equal_to_10_or_greater_than_or_equal_to_999_returns_only_person_b(
        self,
    ):
        """
        Tests OR logic with two numeric range clauses that between them cover only the extreme
        ends of the value range. Only Person B matches at the low boundary (fingernail=10);
        no fixture person has a value near 999.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "OR",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "fingernail_length"]],
                        "operator": "LESS_THAN_OR_EQUALS",
                        "operands": [{"type": "LITERAL", "value": 10}],
                    },
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "fingernail_length"]],
                        "operator": "GREATER_THAN_OR_EQUALS",
                        "operands": [{"type": "LITERAL", "value": 999}],
                    },
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_person_any_friends_with_no_age_returns_no_people(self):
        """
        Tests ANY traversal with a HAS_NO_VALUE filter on related resources. Returns no people
        because every actual friend in the fixture data has a recorded age value. Person B (who has
        no age) is never listed as anyone's friend.
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
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "HAS_NO_VALUE",
                                "operands": [],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, set())

    def test_person_none_friends_with_no_age_returns_person_a_and_person_b(self):
        """
        Tests NONE traversal with a HAS_NO_VALUE filter. Matches the two people who have friends,
        since none of those friends have a missing age value — NONE requires that friends exist
        but none match the filter.
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
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "age"]],
                                "operator": "HAS_NO_VALUE",
                                "operands": [],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["person", "friends"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["NONE"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID})

    def test_person_tile_scope_all_first_names_not_like_incognito_returns_person_a_and_person_c(
        self,
    ):
        """
        Tests quantifier=ALL with operator=NOT_LIKE at tile scope. Matches resources where every
        first-name tile contains a value other than INCOGNITO. Person B has an INCOGNITO alias
        tile and is excluded.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "TILE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ALL",
                        "subject": [["person", "first_name"]],
                        "operator": "NOT_LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_tile_scope_any_first_name_not_like_incognito_returns_all_people(
        self,
    ):
        """
        Tests quantifier=ANY with operator=NOT_LIKE at tile scope. Every person has at least one
        first-name tile with a value other than INCOGNITO, so all three match.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "TILE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "first_name"]],
                        "operator": "NOT_LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID, PERSON_C_ID})

    def test_person_tile_scope_none_first_name_like_incognito_returns_person_a_and_person_c(
        self,
    ):
        """
        Tests quantifier=NONE with operator=LIKE at tile scope. Matches resources that have no
        first-name tile containing INCOGNITO. Person B has INCOGNITO and is excluded.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "TILE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "NONE",
                        "subject": [["person", "first_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_resource_scope_all_first_names_not_like_incognito_returns_person_a_and_person_c(
        self,
    ):
        """
        Tests quantifier=ALL with operator=NOT_LIKE at resource scope. Matches resources where
        every first-name value across all tiles is something other than INCOGNITO. Person B has
        INCOGNITO among their values and is excluded.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ALL",
                        "subject": [["person", "first_name"]],
                        "operator": "NOT_LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_resource_scope_any_first_name_not_like_incognito_returns_all_people(
        self,
    ):
        """
        Tests quantifier=ANY with operator=NOT_LIKE at resource scope. Every person has at least
        one first-name value that is not INCOGNITO, so all three match.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["person", "first_name"]],
                        "operator": "NOT_LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_B_ID, PERSON_C_ID})

    def test_person_resource_scope_none_first_name_like_incognito_returns_person_a_and_person_c(
        self,
    ):
        """
        Tests quantifier=NONE with operator=LIKE at resource scope. Matches resources that have
        no first-name value of INCOGNITO anywhere across their tiles. Person B has INCOGNITO and
        is excluded.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "NONE",
                        "subject": [["person", "first_name"]],
                        "operator": "LIKE",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_resource_scope_not_like_first_name_with_all_quantifier_returns_person_a_and_person_c(
        self,
    ):
        """
        Tests that operator=NOT_LIKE with quantifier=ALL is semantically equivalent to
        operator=LIKE with quantifier=NONE — both express "no first-name value matches INCOGNITO".
        Produces the same result as the NONE+LIKE variant above.
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "subject": [["person", "first_name"]],
                        "operator": "NOT_LIKE",
                        "quantifier": "ALL",
                        "operands": [{"type": "LITERAL", "value": "INCOGNITO"}],
                    }
                ],
                "groups": [],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_person_inverse_favorite_person_any_with_dog_tail_length_equal_to_25_or_999_returns_person_a_and_person_c(
        self,
    ):
        """
        Tests OR logic at the outer group level across two sibling child groups on an inverse
        relationship. Each subgroup filters dogs by a different tail length; together they match
        Person A via Dog A (tail=25) and Person C via Dog B (tail=999).
        """
        result = self._compile(
            {
                "graph_slug": "person",
                "scope": "RESOURCE",
                "logic": "OR",
                "clauses": [],
                "groups": [
                    {
                        "graph_slug": "dog",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["dog", "tail_length"]],
                                "operator": "EQUALS",
                                "operands": [{"type": "LITERAL", "value": 25}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                    {
                        "graph_slug": "dog",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["dog", "tail_length"]],
                                "operator": "EQUALS",
                                "operands": [{"type": "LITERAL", "value": 999}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": True,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {PERSON_A_ID, PERSON_C_ID})

    def test_dog_tail_length_less_than_100_and_favorite_person_fingernail_length_greater_than_10_returns_only_dog_a(
        self,
    ):
        """
        Tests an anchor-side literal clause on the dog combined with a forward traversal filter
        on the related person. Dog A passes both (tail=25 < 100, Person A fingernail=25 > 10).
        Dog B fails at the anchor filter (tail=999 ≥ 100).
        """
        result = self._compile(
            {
                "graph_slug": "dog",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [
                    {
                        "type": "LITERAL",
                        "quantifier": "ANY",
                        "subject": [["dog", "tail_length"]],
                        "operator": "LESS_THAN",
                        "operands": [{"type": "LITERAL", "value": 100}],
                    }
                ],
                "groups": [
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "fingernail_length"]],
                                "operator": "GREATER_THAN",
                                "operands": [{"type": "LITERAL", "value": 10}],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    }
                ],
                "aggregations": [],
                "relationship": {
                    "path": [["dog", "favorite_person"]],
                    "is_inverse": False,
                    "traversal_quantifiers": ["ANY"],
                },
            }
        )
        self.assertEqual(result, {DOG_A_ID})

    def test_person_pet_tail_length_equals_25_and_fingernail_length_greater_than_5_returns_only_person_b(
        self,
    ):
        """
        Tests AND logic across two sibling root groups: one uses a forward traversal to a pet
        with tail=25, and the other directly filters the person by fingernail length. Only Person B
        satisfies both — they own Dog A (tail=25) and have fingernail length 10 > 5.
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
                                "graph_slug": "dog",
                                "scope": "RESOURCE",
                                "logic": "AND",
                                "clauses": [
                                    {
                                        "type": "LITERAL",
                                        "quantifier": "ANY",
                                        "subject": [["dog", "tail_length"]],
                                        "operator": "EQUALS",
                                        "operands": [
                                            {
                                                "type": "LITERAL",
                                                "value": 25,
                                            }
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
                            "path": [["person", "pets"]],
                            "is_inverse": False,
                            "traversal_quantifiers": ["ANY"],
                        },
                    },
                    {
                        "graph_slug": "person",
                        "scope": "RESOURCE",
                        "logic": "AND",
                        "clauses": [
                            {
                                "type": "LITERAL",
                                "quantifier": "ANY",
                                "subject": [["person", "fingernail_length"]],
                                "operator": "GREATER_THAN",
                                "operands": [
                                    {
                                        "type": "LITERAL",
                                        "value": 5,
                                    }
                                ],
                            }
                        ],
                        "groups": [],
                        "aggregations": [],
                        "relationship": None,
                    },
                ],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {PERSON_B_ID})

    def test_dog_favorite_person_with_none_friends_nested_under_relationshipless_child_group_returns_only_dog_b(
        self,
    ):
        """
        Tests a deeply nested structure where a NONE traversal (no friends) is placed inside a
        relationship group that is itself nested inside a relationshipless group. Dog B's favorite
        person is Person C who has no friends; Dog A's favorite person is Person A who does.
        """
        result = self._compile(
            {
                "graph_slug": "dog",
                "scope": "RESOURCE",
                "logic": "AND",
                "clauses": [],
                "groups": [
                    {
                        "graph_slug": "dog",
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
                                        "clauses": [],
                                        "groups": [
                                            {
                                                "graph_slug": "person",
                                                "scope": "RESOURCE",
                                                "logic": "AND",
                                                "clauses": [],
                                                "groups": [],
                                                "aggregations": [],
                                                "relationship": None,
                                            }
                                        ],
                                        "aggregations": [],
                                        "relationship": {
                                            "path": [["person", "friends"]],
                                            "is_inverse": False,
                                            "traversal_quantifiers": ["NONE"],
                                        },
                                    }
                                ],
                                "aggregations": [],
                                "relationship": None,
                            }
                        ],
                        "aggregations": [],
                        "relationship": {
                            "path": [["dog", "favorite_person"]],
                            "is_inverse": False,
                            "traversal_quantifiers": ["ANY"],
                        },
                    }
                ],
                "aggregations": [],
                "relationship": None,
            }
        )
        self.assertEqual(result, {DOG_B_ID})
