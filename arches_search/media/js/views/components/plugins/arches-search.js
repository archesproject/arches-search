import ko from 'knockout';
import createVueApplication from 'arches/arches/app/media/js/utils/create-vue-application';

import AdvancedSearch from '@/arches_search/AdvancedSearch/AdvancedSearch.vue';
import ArchesSearchTemplate from 'templates/views/components/plugins/arches-search.htm';

export default ko.components.register('arches-search', {
    viewModel: function() {
        createVueApplication(AdvancedSearch).then(vueApp => {
            vueApp.mount('#arches-search-mounting-point');
        });
    },
    template: ArchesSearchTemplate,
});