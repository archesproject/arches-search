import uuid

from django.core.management import call_command
from django.test import TestCase

from arches.app.models.models import (
    Concept,
    GraphModel,
    Node,
    NodeGroup,
    Relation,
    ResourceInstance,
    TileModel,
    Value,
)
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)


class ConceptAdvancedSearchFacetIntegrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent_value = cls._create_concept_label("Religious institution")
        cls.child_value = cls._create_concept_label("Mosque")
        cls.other_value = cls._create_concept_label("Bridge")
        Relation.objects.create(
            relationid=uuid.uuid4(),
            conceptfrom=cls.parent_value.concept,
            conceptto=cls.child_value.concept,
            relationtype_id="narrower",
        )

        suffix = uuid.uuid4().hex[:8]
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(), slug=f"facet_concept_{suffix}", isresource=True
        )
        nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4(), cardinality="1")
        cls.concept_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name=f"type_{suffix}",
            alias=f"type_{suffix}",
            datatype="concept",
            graph=cls.graph,
            nodegroup=nodegroup,
            istopnode=True,
        )
        cls.resources_by_value = {}
        for value in (cls.parent_value, cls.child_value, cls.other_value):
            resource = ResourceInstance.objects.create(
                resourceinstanceid=uuid.uuid4(), graph=cls.graph
            )
            TileModel.objects.create(
                tileid=uuid.uuid4(),
                nodegroup=nodegroup,
                resourceinstance=resource,
                data={str(cls.concept_node.nodeid): str(value.pk)},
                provisionaledits=None,
            )
            cls.resources_by_value[value.pk] = resource.pk

        call_command("arches_search", "reindex_database")

    @staticmethod
    def _create_concept_label(label):
        concept = Concept.objects.create(
            conceptid=uuid.uuid4(), nodetype_id="Concept", legacyoid=str(uuid.uuid4())
        )
        return Value.objects.create(
            valueid=uuid.uuid4(),
            concept=concept,
            valuetype_id="prefLabel",
            language_id="en",
            value=label,
        )

    def _matches(self, operator, value_id):
        payload = {
            "graph_slug": self.graph.slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": self.graph.slug,
                        "node_alias": self.concept_node.alias,
                        "search_models": [],
                    },
                    "operator": operator,
                    "operands": [{"type": "LITERAL", "value": str(value_id)}],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }
        return set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )

    def test_references_any_matches_narrower_concepts(self):
        self.assertEqual(
            self._matches("REFERENCES_ANY", self.parent_value.pk),
            {
                self.resources_by_value[self.parent_value.pk],
                self.resources_by_value[self.child_value.pk],
            },
        )
