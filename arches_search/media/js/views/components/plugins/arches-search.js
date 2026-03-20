import ko from 'knockout';
import createVueApplication from 'arches/arches/app/media/js/utils/create-vue-application';

import SearchApp from '@/arches_search/SearchApp.vue';
import ArchesSearchTemplate from 'templates/views/components/plugins/arches-search.htm';
import SearchTheme from '@/arches_search/default_theme.ts';

export default ko.components.register('arches-search', {
    viewModel: function () {
        createVueApplication(SearchApp, SearchTheme).then(vueApp => {
            vueApp.mount('#arches-search-mounting-point');
        });
    },
    template: ArchesSearchTemplate,
});