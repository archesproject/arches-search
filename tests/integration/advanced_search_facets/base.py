import uuid
from typing import Any, Sequence

from django.test import TestCase

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    TileModel,
)
from arches_search.models.models import DateRangeSearch, TermSearch
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.advanced_search.search_model_registry import (
    SearchModelRegistry,
)


class BaseAdvancedSearchFacetIntegrationTestCase(TestCase):
    datatype_name = ""

    def setUp(self):
        self.search_model_registry = SearchModelRegistry()

    def create_literal_fixture(
        self,
        matching_values: Sequence[Any],
        non_matching_values: Sequence[Any],
    ) -> tuple[str, str, uuid.UUID]:
        slug_suffix = uuid.uuid4().hex[:8]
        graph_slug = f"facet_{self.datatype_name.replace('-', '_')}_{slug_suffix}"
        node_alias = f"value_{slug_suffix}"

        graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug=graph_slug,
            isresource=True,
        )
        nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
            cardinality="1",
        )
        Node.objects.create(
            nodeid=uuid.uuid4(),
            name=node_alias,
            alias=node_alias,
            datatype=self.datatype_name,
            graph=graph,
            nodegroup=nodegroup,
            istopnode=True,
        )

        matching_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=graph,
        )
        matching_resource.save()

        non_matching_resource = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=graph,
        )
        non_matching_resource.save()

        self._create_search_rows(
            graph_slug=graph_slug,
            node_alias=node_alias,
            resource=matching_resource,
            row_values=matching_values,
        )
        self._create_search_rows(
            graph_slug=graph_slug,
            node_alias=node_alias,
            resource=non_matching_resource,
            row_values=non_matching_values,
        )

        return graph_slug, node_alias, matching_resource.resourceinstanceid

    def build_literal_payload(
        self,
        graph_slug: str,
        node_alias: str,
        operator: str,
        operands: Sequence[Any] = (),
    ) -> dict:
        return {
            "graph_slug": graph_slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [[graph_slug, node_alias]],
                    "operator": operator,
                    "operands": [
                        {"type": "LITERAL", "value": operand} for operand in operands
                    ],
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": None,
        }

    def assert_payload_matches_only_resource(
        self,
        payload: dict,
        expected_resource_id: uuid.UUID,
    ) -> None:
        result = set(
            AdvancedSearchQueryCompiler(payload)
            .compile()
            .values_list("resourceinstanceid", flat=True)
        )
        self.assertEqual(result, {expected_resource_id})

    def _create_search_rows(
        self,
        graph_slug: str,
        node_alias: str,
        resource: ResourceInstance,
        row_values: Sequence[Any],
    ) -> None:
        if not row_values:
            return

        model_class = self.search_model_registry.get_model_for_datatype(
            self.datatype_name
        )
        tile = TileModel(
            tileid=uuid.uuid4(),
            nodegroup=NodeGroup.objects.create(
                nodegroupid=uuid.uuid4(),
                cardinality="1",
            ),
            resourceinstance=resource,
            data={},
            provisionaledits=None,
        )
        tile.save()

        for row_value in row_values:
            create_kwargs = {
                "tileid": tile,
                "resourceinstanceid": resource,
                "graph_slug": graph_slug,
                "node_alias": node_alias,
                "datatype": self.datatype_name,
            }

            if model_class is DateRangeSearch:
                create_kwargs["start_value"] = row_value[0]
                create_kwargs["end_value"] = row_value[1]
            else:
                create_kwargs["value"] = row_value

            if model_class is TermSearch:
                create_kwargs["language"] = "en"

            model_class.objects.create(**create_kwargs)
