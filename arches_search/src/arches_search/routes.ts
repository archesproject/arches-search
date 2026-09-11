import arches from "arches";
import SearchLanding from "@/arches_search/SearchLanding/SearchLanding.vue";
import SimpleSearch from "@/arches_search/SimpleSearch/SimpleSearch.vue";
import AdvancedSearch from "@/arches_search/AdvancedSearch/AdvancedSearch.vue";

export const routes = [
    {
        path: arches.urls.plugin("arches-search"),
        name: "search-landing",
        component: SearchLanding,
    },
    {
        path: arches.urls.plugin("arches-search/simple"),
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
    searchLanding: "search-landing",
    simpleSearch: "simple-search",
    advancedSearch: "advanced-search",
};
