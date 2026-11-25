from django.db import transaction
from django.test import TransactionTestCase

from arches.app.models.models import FunctionXGraph
from arches.extensions.querysets.models import ResourceTileTree
from arches.extensions.querysets.utils.tests import GraphTestCase

from arches_search.indexing.index_descriptor import DESCRIPTOR_NODE_ALIAS
from arches_search.models.models import TermSearch

PRIMARY_DESCRIPTORS_FUNCTION_ID = "60000000-0000-0000-0000-000000000001"


class DescriptorQuerysetsSaveTest(TransactionTestCase):
    def setUp(self):
        class QuerysetsGraph(GraphTestCase):
            pass

        with transaction.atomic():
            QuerysetsGraph.setUpTestData()
        self.graph = QuerysetsGraph.graph
        self.resource_id = QuerysetsGraph.resource_42.pk
        FunctionXGraph.objects.create(
            function_id=PRIMARY_DESCRIPTORS_FUNCTION_ID,
            graph_id=self.graph.pk,
            config={
                "descriptor_types": {
                    "name": {
                        "nodegroup_id": str(QuerysetsGraph.nodegroup_1.pk),
                        "string_template": "<number>",
                    },
                    "description": {"nodegroup_id": "", "string_template": ""},
                    "map_popup": {"nodegroup_id": "", "string_template": ""},
                }
            },
        )

    def test_save_through_resource_tile_tree_indexes_the_new_name(self):
        resource = ResourceTileTree.get_tiles(
            self.graph.slug, resource_ids=[self.resource_id]
        ).get()
        resource.aliased_data.datatypes_1.aliased_data.number_alias = 43
        resource.save(index=False, force_admin=True)

        descriptor_values = TermSearch.objects.filter(
            resourceinstanceid_id=self.resource_id,
            node_alias=DESCRIPTOR_NODE_ALIAS,
        ).values_list("value", flat=True)
        self.assertEqual(list(descriptor_values), ["43"])
