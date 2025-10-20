from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase

from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.search_aggregation import apply_json_aggregations


class AdvancedSearchAPI(APIBase):
    def post(self, request):
        body = JSONDeserializer().deserialize(request.body)
        payload_query = body.get("query", {})

        aggregations = {}
        # payload_query = {
        #     "graph_slug": "new_resource_model",
        #     "logic": "AND",
        #     "clauses": [
        #         {
        #             "operator": "GREATER_THAN",
        #             "subject": ["new_resource_model:mother", "new_resource_model:toenail_length"],
        #             "operands": [  { "type": "LITERAL", "value": 5 } ]
        #         }
        #     ],
        #     "groups": [],
        #     "aggregations": []
        # }
        # payload_query = {
        #     "graph_slug": "new_resource_model",
        #     "logic": "AND",
        #     "clauses": [
        #         {
        #             "operator": "REFERENCES_ONLY",
        #             "subject": ["new_resource_model:mother"],
        #             "operands": [
        #                 { "type": "RESULTSET", "value": [] }
        #             ]
        #         },
        #         {
        #             "operator": "NOT_EQUALS",
        #             "subject": ["new_resource_model:toenail_length"],
        #             "operands": [
        #                 { "type": "LITERAL", "value": 1 }
        #             ]
        #         }
        #     ],
        #     "groups": [
        #         {
        #             "graph_slug": "new_resource_model",
        #             "logic": "AND",
        #             "clauses": [],
        #             "groups": [
        #                 {
        #                 "graph_slug": "dog",
        #                 "logic": "AND",
        #                 "clauses": [
        #                     {
        #                         "operator": "REFERENCES_ONLY",
        #                         "subject": ["dog:favorite_person"],
        #                         "operands": [
        #                             { "type": "PARENT", "value": [] }
        #                         ]
        #                     },
        #                     {
        #                         "operator": "NOT_EQUALS",
        #                         "subject": ["dog:favorite_person", "new_resource_model:toenail_length"],
        #                         "operands": [
        #                             { "type": "SELF", "value": ["dog:tail_length"] }
        #                         ]
        #                     },
        #                     {
        #                         "operator": "EQUALS",
        #                         "subject": ["dog:favorite_person", "new_resource_model:toenail_length"],
        #                         "operands": [
        #                             { "type": "SELF", "value": ["dog:favorite_person", "new_resource_model:toenail_length"] }
        #                         ]
        #                     }
        #                 ],
        #                 "groups": [],
        #                 "aggregations": []
        #                 }
        #             ],
        #             "aggregations": []
        #         }
        #     ],
        #     "aggregations": []
        # }

        results = AdvancedSearchQueryCompiler(payload_query).build_resources_queryset()
        raw_aggregations = payload_query.get("aggregations")

        if raw_aggregations:
            aggregations = apply_json_aggregations(raw_aggregations, results)

        return JSONResponse(
            {
                "resources": list(results),
                "aggregations": aggregations,
            }
        )
