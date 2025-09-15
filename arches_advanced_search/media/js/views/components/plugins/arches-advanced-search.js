import ko from 'knockout';
import createVueApplication from 'arches/arches/app/media/js/utils/create-vue-application';

import ArchesAdvancedSearch from '@/arches_advanced_search/ArchesAdvancedSearch.vue';
import AdvancedSearchTemplate from 'templates/views/components/plugins/arches-advanced-search.htm';

export default ko.components.register('arches-advanced-search', {
    viewModel: function() {
        createVueApplication(ArchesAdvancedSearch).then(vueApp => {
            vueApp.mount('#arches-advanced-search-mounting-point');
        });
    },
    template: AdvancedSearchTemplate,
});