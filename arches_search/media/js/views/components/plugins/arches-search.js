import ko from 'knockout';
import createVueApplication from 'arches/arches/app/media/js/utils/create-vue-application';

import AdvancedSearch from '@/arches_search/AdvancedSearch/AdvancedSearch.vue';
import ArchesSearchTemplate from 'templates/views/components/plugins/arches-search.htm';


// const query = {
//     "graph_slug": "dog",
//     "scope": "TILE",
//     "logic": "AND",
//     "clauses": [],
//     "groups": [],
//     "aggregations": [],
//     "relationship": null
// }

const query = {
    "graph_slug": "person",
    "scope": "TILE",
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
            "relationship": null,
        }
    ],
    "aggregations": [],
    "relationship": {
        "path": [["dog", "favorite_person"]],
        "is_inverse": true,
        "traversal_quantifiers": ["ANY"],
    },
}

// const query = {
//     "graph_slug": "dog",
//     "scope": "RESOURCE",
//     "logic": "AND",
//     "clauses": [],
//     "groups": [
//         {
//             "graph_slug": "person",
//             "scope": "TILE",
//             "logic": "AND",
//             "clauses": [
//                 {
//                     "subject": [["person", "first_name"]],
//                     "operator": "LIKE",
//                     "operands": [{ "type": "LITERAL", "value": "INCOGNITO" }]
//                 },
//                 {
//                     "subject": [["person", "last_name"]],
//                     "operator": "LIKE",
//                     "operands": [{ "type": "LITERAL", "value": "MOTHER" }]
//                 }
//             ],
//             "groups": [],
//             "aggregations": [],
//             "relationship": null
//         }
//     ],
//     "aggregations": [],
//     "relationship": {
//         "path": [["person", "pets"]],
//         "quantifier": "AT_LEAST",
//         "value": 1,
//         "is_inverse_relationship": true
//     }
// }


// const query = {
//     "graph_slug": "person",
//     "scope": "RESOURCE",
//     "logic": "AND",
//     "clauses": [
//         {
//             "subject": [["person", "fingernail_length"]],
//             "operator": "LESS_THAN_OR_EQUALS",
//             "operands": [
//                 { "type": "RELATED", "value": [["person", "fingernail_length"]] }
//             ]
//         }
//     ],
//     "groups": [
//         {
//             "graph_slug": "person",
//             "scope": "RESOURCE",
//             "logic": "AND",
//             "clauses": [
//                 {
//                     "subject": [["person", "age"]],
//                     "operator": "GREATER_THAN",
//                     "operands": [{ "type": "LITERAL", "value": 18 }]
//                 },
//                 {
//                     "subject": [["person", "age"]],
//                     "operator": "LESS_THAN",
//                     "operands": [{ "type": "LITERAL", "value": 24 }]
//                 }
//             ],
//             "groups": [],
//             "aggregations": [],
//             "relationship": null
//         }
//     ],
//     "aggregations": [],
//     "relationship": {
//         "path": [["person", "friends"]],
//         "quantifier": "EXACTLY",
//         "value": 0,
//         "is_inverse_relationship": false
//     }
// }


// const query = {
//     "graph_slug": "person",
//     "scope": "RESOURCE",
//     "logic": "AND",
//     "clauses": [],
//     "groups": [
//         {
//             "graph_slug": "person",
//             "scope": "RESOURCE",
//             "logic": "AND",
//             "clauses": [],
//             "groups": [
//                 {
//                     "graph_slug": "person",
//                     "scope": "RESOURCE",
//                     "logic": "AND",
//                     "clauses": [],
//                     "groups": [],
//                     "aggregations": [],
//                     "relationship": null
//                 }
//             ],
//             "aggregations": [],
//             "relationship": {
//                 "path": [["person", "friends"]],
//                 "quantifier": "AT_LEAST",
//                 "value": 1,
//                 "is_inverse_relationship": false
//             }
//         },
//         {
//             "graph_slug": "person",
//             "scope": "RESOURCE",
//             "logic": "AND",
//             "clauses": [
//                 {
//                     "subject": [["person", "fingernail_length"]],
//                     "operator": "LESS_THAN_OR_EQUALS",
//                     "operands": [
//                         { "type": "RELATED", "value": [["person", "fingernail_length"]] }
//                     ]
//                 }
//             ],
//             "groups": [
//                 {
//                     "graph_slug": "person",
//                     "scope": "RESOURCE",
//                     "logic": "AND",
//                     "clauses": [],
//                     "groups": [],
//                     "aggregations": [],
//                     "relationship": null
//                 }
//             ],
//             "aggregations": [],
//             "relationship": {
//                 "path": [["person", "friends"]],
//                 "quantifier": "AT_MOST",
//                 "value": 0,
//                 "is_inverse_relationship": false
//             }
//         }
//     ],
//     "aggregations": [],
//     "relationship": null
// }


// const query = 
//         {
//             "graph_slug": "person",
//             "scope": "RESOURCE",
//             "logic": "AND",
//             "clauses": [
//                 {
//                     "subject": [["person", "fingernail_length"]],
//                     "operator": "LESS_THAN",
//                     "operands": [
//                         { "type": "RELATED", "value": [["person", "fingernail_length"]] }
//                     ]
//                 }
//             ],
//             "groups": [
//                 {
//                     "graph_slug": "person",
//                     "scope": "TILE",
//                     "logic": "AND",
//                     "clauses": [
//                         {
//                             "subject": [["person", "first_name"]],
//                             "operator": "LIKE",
//                             "operands": [{ "type": "LITERAL", "value": "FRIEND" }]
//                         },
//                         {
//                             "subject": [["person", "last_name"]],
//                             "operator": "LIKE",
//                             "operands": [{ "type": "LITERAL", "value": "FRIEND!" }]
//                         }
//                     ],
//                     "groups": [],
//                     "aggregations": [],
//                     "relationship": null
//                 }
//             ],
//             "aggregations": [],
//             "relationship": {
//                 "path": [["person", "friends"]],
//                 "quantifier": "AT_LEAST",
//                 "value": 1,
//                 "is_inverse_relationship": false
//             }
//         }


// const query = {
//     "graph_slug": "person",
//     "scope": "RESOURCE",
//     "logic": "AND",
//     "clauses": [],
//     "groups": [
//         {
//             "graph_slug": "person",
//             "scope": "RESOURCE",
//             "logic": "AND",
//             "clauses": [
//                 {
//                     "subject": [["person", "fingernail_length"]],
//                     "operator": "LESS_THAN",
//                     "operands": [
//                         { "type": "RELATED", "value": [["person", "fingernail_length"]] }
//                     ]
//                 }
//             ],
//             "groups": [
//                 {
//                     "graph_slug": "person",
//                     "scope": "TILE",
//                     "logic": "AND",
//                     "clauses": [
//                         {
//                             "subject": [["person", "first_name"]],
//                             "operator": "LIKE",
//                             "operands": [{ "type": "LITERAL", "value": "FRIEND" }]
//                         },
//                         {
//                             "subject": [["person", "last_name"]],
//                             "operator": "LIKE",
//                             "operands": [{ "type": "LITERAL", "value": "FRIEND!" }]
//                         }
//                     ],
//                     "groups": [],
//                     "aggregations": [],
//                     "relationship": null
//                 }
//             ],
//             "aggregations": [],
//             "relationship": {
//                 "path": [["person", "friends"]],
//                 "quantifier": "AT_LEAST",
//                 "value": 1,
//                 "is_inverse_relationship": false
//             }
//         },
//         {
//             "graph_slug": "person",
//             "scope": "RESOURCE",
//             "logic": "AND",
//             "clauses": [],
//             "groups": [
//                 {
//                     "graph_slug": "dog",
//                     "scope": "RESOURCE",
//                     "logic": "AND",
//                     "clauses": [],
//                     "groups": [],
//                     "aggregations": [],
//                     "relationship": null
//                 }
//             ],
//             "aggregations": [],
//             "relationship": {
//                 "path": [["person", "pets"]],
//                 "quantifier": "EXACTLY",
//                 "value": 0,
//                 "is_inverse_relationship": false
//             }
//         }
//     ],
//     "aggregations": [],
//     "relationship": null
// }



export default ko.components.register('arches-search', {
    viewModel: function () {
        createVueApplication(AdvancedSearch, undefined, { query }).then(vueApp => {
            vueApp.mount('#arches-search-mounting-point');
        });
    },
    template: ArchesSearchTemplate,
});