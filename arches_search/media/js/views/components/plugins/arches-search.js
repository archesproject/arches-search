import ko from 'knockout';
import createVueApplication from 'arches/arches/app/media/js/utils/create-vue-application';

import AdvancedSearch from '@/arches_search/AdvancedSearch/AdvancedSearch.vue';
import ArchesSearchTemplate from 'templates/views/components/plugins/arches-search.htm';


export default ko.components.register('arches-search', {
    viewModel: function () {
        createVueApplication(AdvancedSearch, undefined, { query: {
    "graph_slug": "casf-project",
    "scope": "RESOURCE",
    "logic": "AND",
    "clauses": [],
    "groups": [
        {
            "graph_slug": "casf-project",
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [],
            "groups": [
                {
                    "graph_slug": "account-award-cycle",
                    "scope": "RESOURCE",
                    "logic": "AND",
                    "clauses": [
                        {
                            "type": "LITERAL",
                            "quantifier": "ANY",
                            "subject": [
                                [
                                    "account-award-cycle",
                                    "account_type"
                                ]
                            ],
                            "operator": "REFERENCES_ANY",
                            "operands": [
                                {
                                    "type": "LITERAL",
                                    "value": [
                                        "Broadband Public Housing Account"
                                    ]
                                }
                            ]
                        }
                    ],
                    "groups": [],
                    "aggregations": [],
                    "relationship": null
                }
            ],
            "aggregations": [],
            "relationship": {
                "path": [
                    [
                        "casf-project",
                        "related_account_award_cycle"
                    ]
                ],
                "is_inverse": false,
                "traversal_quantifiers": [
                    "ANY"
                ]
            }
        },
        {
            "graph_slug": "casf-project",
            "scope": "RESOURCE",
            "logic": "OR",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": [
                        [
                            "casf-project",
                            "county"
                        ]
                    ],
                    "operator": "REFERENCES_ANY",
                    "operands": [
                        {
                            "type": "LITERAL",
                            "value": [
                                "Alameda"
                            ]
                        }
                    ]
                },
                {
                    "type": "LITERAL",
                    "quantifier": "ALL",
                    "subject": [
                        [
                            "casf-project",
                            "county"
                        ]
                    ],
                    "operator": "REFERENCES_ANY",
                    "operands": [
                        {
                            "type": "LITERAL",
                            "value": [
                                "Alpine"
                            ]
                        }
                    ]
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": null
        }
    ],
    "aggregations": [],
    "relationship": null
}}).then(vueApp => {
            vueApp.mount('#arches-search-mounting-point');
        });
    },
    template: ArchesSearchTemplate,
});