import arches from "arches";
import SimpleSearch from "@/arches_search/SimpleSearch/SimpleSearch.vue";
import AdvancedSearch from "@/arches_search/AdvancedSearch/AdvancedSearch.vue";

export const routes = [
    {
        path: arches.urls.plugin("arches-search"),
        name: "simple-search",
        component: SimpleSearch,
    },
    {
        path: arches.urls.plugin("arches-search/advanced"),
        name: "advanced-search",
        component: AdvancedSearch,
    },
];

export const routeNames = {
    simpleSearch: "simple-search",
    advancedSearch: "advanced-search",
};
