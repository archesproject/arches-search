import { ref, computed, provide, inject } from "vue";
import type { InjectionKey } from "vue";

import type {
    ActiveFilter,
    ResourceType,
} from "@/arches_search/SimpleSearch/types.ts";
import type {
    GroupPayload,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import { fetchSearchResults } from "@/arches_search/SimpleSearch/api.ts";

const SEARCH_FILTERS_KEY: InjectionKey<ReturnType<typeof createSearchFilters>> =
    Symbol("searchFilters");

const emptyResults: SearchResults = {
    resources: [],
    aggregations: {},
    pagination: {
        page: 1,
        page_size: 25,
        total_results: 0,
        total_pages: 0,
        has_next: false,
        has_previous: false,
    },
};

function createSearchFilters() {
    const terms = ref<Map<string, ActiveFilter>>(new Map());
    const queries = ref<Map<string, GroupPayload>>(new Map());
    const activeGraph = ref<ResourceType | null>(null);
    const searchResults = ref<SearchResults>({ ...emptyResults });
    const isSearching = ref(false);
    const currentPage = ref(1);

    const activeFilters = computed<ActiveFilter[]>(() => {
        return [...terms.value.values()];
    });

    function setTermFilter(
        key: string,
        text: string,
        clear: () => void,
        options?: Record<string, unknown>,
    ) {
        const next = new Map(terms.value);
        next.set(key, {
            id: key,
            text: text,
            clear: clear,
            inverted: false,
            options: options,
        });
        terms.value = next;
        currentPage.value = 1;
        search();
    }

    function clearTermFilter(key: string) {
        const next = new Map(terms.value);
        next.delete(key);
        terms.value = next;
        currentPage.value = 1;
        search();
    }

    function setQuery(filterKey: string, payload: GroupPayload) {
        const next = new Map(queries.value);
        next.set(filterKey, payload);
        queries.value = next;
        currentPage.value = 1;
        search();
    }

    function clearQuery(filterKey: string) {
        const next = new Map(queries.value);
        next.delete(filterKey);
        queries.value = next;
        search();
    }

    function setGraph(graph: ResourceType | null) {
        activeGraph.value = graph;
        currentPage.value = 1;
        search();
    }

    let searchTimeout: ReturnType<typeof setTimeout> | null = null;

    function search(page = currentPage.value) {
        if (searchTimeout) clearTimeout(searchTimeout);
        searchTimeout = setTimeout(async () => {
            currentPage.value = page;
            isSearching.value = true;
            const requestTerms = [...terms.value.values()].map((term) => ({
                type: "string",
                text: term.text,
                inverted: term.inverted,
            }));
            const requestQueries = queries.value.values()
                ? queries.value.values()
                : {};
            try {
                const results = await fetchSearchResults({
                    terms: requestTerms,
                    query: requestQueries as GroupPayload,
                    page: page,
                    graphId: activeGraph.value ? activeGraph.value.id : null,
                });
                if (page > 1) {
                    searchResults.value = {
                        ...results,
                        resources: [
                            ...searchResults.value.resources,
                            ...results.resources,
                        ],
                    };
                } else {
                    searchResults.value = results;
                }
            } finally {
                isSearching.value = false;
            }
        }, 300); // 300ms debounce delay
    }

    return {
        activeFilters,
        activeGraph,
        setTermFilter: setTermFilter,
        clearTermFilter: clearTermFilter,
        setQuery,
        clearQuery,
        setGraph,
        searchResults,
        isSearching,
        currentPage,
        search,
    };
}

export function provideSearchFilters() {
    const filters = createSearchFilters();
    provide(SEARCH_FILTERS_KEY, filters);
    return filters;
}

export function useSearchFilters() {
    const filters = inject(SEARCH_FILTERS_KEY);
    if (!filters)
        throw new Error(
            "a parent component must call provideSearchFilters before using useSearchFilters in a child component",
        );
    return filters;
}
