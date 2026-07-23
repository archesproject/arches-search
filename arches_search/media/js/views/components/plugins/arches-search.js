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
            // Force light mode: createVueApplication() (arches-vue-components) auto-applies
            // dark mode from the OS/localStorage preference before this resolves; undo that here
            // rather than in the shared package, since other Arches apps still want that behavior.
            const darkModeClass = SearchTheme.theme.options.darkModeSelector.substring(1);
            document.documentElement.classList.remove(darkModeClass);

            vueApp.use(router);
            vueApp.mount('#arches-search-mounting-point');
        });
    },
    template: ArchesSearchTemplate,
});