import ko from 'knockout';
import createVueApplication from 'arches/arches/app/media/js/utils/create-vue-application';

import AdvancedSearch from '@/arches_search/AdvancedSearch/AdvancedSearch.vue';
import ArchesSearchTemplate from 'templates/views/components/plugins/arches-search.htm';

export default ko.components.register('arches-search', {
    viewModel: function() {
        createVueApplication(AdvancedSearch, null, {
                query: {
                graph_slug: "new_resource_model",
                query: {
                    logic: "AND",
                    clauses: [
                        {
                            node_alias: "toenail_length",
                            search_table: "numeric",
                            datatype: "number",
                            operator: "GREATER_THAN",
                            params: [5],
                        },
                    ],
                    groups: [
                        {
                            logic: "OR",
                            clauses: [
                                {
                                    node_alias: "fingernail_length",
                                    search_table: null,
                                    datatype: null,
                                    operator: null,
                                    params: [],
                                },
                            ],
                            groups: [],
                        },
                    ],
                },
                aggregations: [],
            }
            }).then(vueApp => {
            vueApp.mount('#arches-search-mounting-point');
        });
    },
    template: ArchesSearchTemplate,
});