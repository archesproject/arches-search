import ko from 'knockout';
import { createRouter, createWebHistory } from 'vue-router';
import { createVueApplication } from '@/arches_vue_components/application';

import SearchApp from '@/arches_search/SearchApp.vue';
import { routes } from '@/arches_search/routes.ts';
import ArchesSearchTemplate from 'templates/views/components/plugins/arches-search.htm';
import SearchTheme from '@/arches_search/default_theme.ts';

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default ko.components.register('arches-search', {
    viewModel: function () {
        createVueApplication({ component: SearchApp, themeConfiguration: SearchTheme }).then(vueApp => {
            vueApp.use(router);
            vueApp.mount('#arches-search-mounting-point');
        });
    },
    template: ArchesSearchTemplate,
});