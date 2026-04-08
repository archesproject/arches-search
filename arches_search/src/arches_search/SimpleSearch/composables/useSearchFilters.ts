import { ref, computed, provide, inject } from "vue";
import type { InjectionKey } from "vue";

import type { ActiveFilter } from "@/arches_search/SimpleSearch/types.ts";
import type {
    GroupPayload,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import { fetchSearchResults } from "@/arches_search/SimpleSearch/api.ts";

interface FilterRegistration {
    text: string;
    clear: () => void;
    options?: Record<string, unknown>;
}

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
    const terms = ref<Map<string, FilterRegistration>>(new Map());
    const queries = ref<Map<string, GroupPayload>>(new Map());
    const activeGraph = ref<{ id: string } | null>(null);
    const searchResults = ref<SearchResults>({ ...emptyResults });
    const isSearching = ref(false);
    const currentPage = ref(1);

    const activeFilters = computed<ActiveFilter[]>(() =>
        [...terms.value.entries()].map(([key, { text, clear, options }]) => ({
            id: key,
            text,
            clear,
            options,
        })),
    );

    function setTerm(
        key: string,
        text: string,
        clear: () => void,
        options?: Record<string, unknown>,
    ) {
        const next = new Map(terms.value);
        next.set(key, { text, clear, options });
        terms.value = next;
        currentPage.value = 1;
        search();
    }

    function clearTerm(key: string) {
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

    function setGraph(graph: { id: string } | null) {
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
            const requestTerms = [...terms.value.values()].map((term) => (term.text));
            const requestQueries = queries.value.values() ? queries.value.values() : {};
            try {
                searchResults.value = await fetchSearchResults({ 
                    terms: requestTerms, 
                    query: requestQueries, 
                    page: page,
                    graphId: activeGraph.value ? activeGraph.value.id : null,
                });
            } finally {
                isSearching.value = false;
            }
        }, 300); // 300ms debounce delay
    }

    return {
        activeFilters,
        activeGraph,
        setTerm,
        clearTerm,
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
    if (!filters) throw new Error("useSearchFilters must be used within SimpleSearch");
    return filters;
}
