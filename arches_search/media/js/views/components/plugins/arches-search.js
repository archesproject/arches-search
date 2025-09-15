import ko from 'knockout';
import createVueApplication from 'arches/arches/app/media/js/utils/create-vue-application';

import ArchesSearch from '@/arches_search/ArchesSearch.vue';
import ArchesSearchTemplate from 'templates/views/components/plugins/arches-search.htm';

export default ko.components.register('arches-search', {
    viewModel: function() {
        createVueApplication(ArchesSearch).then(vueApp => {
            vueApp.mount('#arches-search-mounting-point');
        });
    },
    template: ArchesSearchTemplate,
});