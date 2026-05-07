import { computed, inject, provide, ref } from "vue";

import { fetchSearchResults } from "@/arches_search/SimpleSearch/api.ts";

import type { ComputedRef, InjectionKey, Ref } from "vue";
import type {
    GroupPayload,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    ActiveFilter,
    ResourceType,
} from "@/arches_search/SimpleSearch/types.ts";
import type { FeatureCollection } from "geojson";

interface SearchRequestTerm {
    type: string;
    text: string;
    inverted: boolean;
}

interface SearchFilters {
    activeFilters: ComputedRef<ActiveFilter[]>;
    activeGraph: Ref<ResourceType | null>;
    currentPage: Ref<number>;
    isSearching: Ref<boolean>;
    mapFilter: Ref<FeatureCollection | null>;
    resultsGraph: Ref<ResourceType | null>;
    searchResults: Ref<SearchResults>;
    clearMapFilter(): void;
    clearQuery(filterKey: string): void;
    clearTermFilter(key: string): void;
    search(page?: number): void;
    setGraph(graph: ResourceType | null): void;
    setMapFilter(featureCollection: FeatureCollection): void;
    setQuery(filterKey: string, payload: GroupPayload): void;
    setTermFilter(
        key: string,
        text: string,
        clear: () => void,
        options?: Record<string, unknown>,
    ): void;
}

const FIRST_SEARCH_PAGE = 1;
const SEARCH_DEBOUNCE_MS = 300;
const SEARCH_RESULTS_PAGE_SIZE = 25;
const SEARCH_FILTERS_KEY: InjectionKey<SearchFilters> = Symbol("searchFilters");

function createSearchFilters(): SearchFilters {
    const terms = ref<Map<string, ActiveFilter>>(new Map());
    const queries = ref<Map<string, GroupPayload>>(new Map());
    const mapFilter = ref<FeatureCollection | null>(null);
    const activeGraph = ref<ResourceType | null>(null);
    const resultsGraph = ref<ResourceType | null>(null);
    const searchResults = ref<SearchResults>(createEmptySearchResults());
    const isSearching = ref(false);
    const currentPage = ref(FIRST_SEARCH_PAGE);
    let searchTimeout: ReturnType<typeof setTimeout> | null = null;

    const activeFilters = computed<ActiveFilter[]>(() => {
        return [...terms.value.values()];
    });

    function setTermFilter(
        key: string,
        text: string,
        clear: () => void,
        options?: Record<string, unknown>,
    ): void {
        const next = new Map(terms.value);
        next.set(key, {
            id: key,
            text,
            clear,
            inverted: false,
            options,
        });
        terms.value = next;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function clearTermFilter(key: string): void {
        const next = new Map(terms.value);
        next.delete(key);
        terms.value = next;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function setQuery(filterKey: string, payload: GroupPayload): void {
        const next = new Map(queries.value);
        next.set(filterKey, payload);
        queries.value = next;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function clearQuery(filterKey: string): void {
        const next = new Map(queries.value);
        next.delete(filterKey);
        queries.value = next;
        search();
    }

    function setMapFilter(featureCollection: FeatureCollection): void {
        mapFilter.value = featureCollection;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function clearMapFilter(): void {
        mapFilter.value = null;
        search();
    }

    function setGraph(graph: ResourceType | null): void {
        activeGraph.value = graph;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function search(page = currentPage.value): void {
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        searchTimeout = setTimeout(async () => {
            currentPage.value = page;
            isSearching.value = true;

            try {
                const requestGraph = activeGraph.value;
                const results = await fetchSearchResults({
                    terms: getRequestTerms(),
                    query: getRequestQuery(),
                    page,
                    graphId: requestGraph ? requestGraph.id : null,
                    mapFilter: mapFilter.value,
                });

                if (page > FIRST_SEARCH_PAGE) {
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

                resultsGraph.value = requestGraph;
            } finally {
                isSearching.value = false;
            }
        }, SEARCH_DEBOUNCE_MS);
    }

    function getRequestTerms(): SearchRequestTerm[] {
        return [...terms.value.values()].map((term) => ({
            type: "string",
            text: term.text,
            inverted: term.inverted,
        }));
    }

    function getRequestQuery(): GroupPayload | undefined {
        return queries.value.values().next().value;
    }

    return {
        activeFilters,
        activeGraph,
        clearMapFilter,
        clearQuery,
        clearTermFilter,
        currentPage,
        isSearching,
        mapFilter,
        resultsGraph,
        search,
        searchResults,
        setGraph,
        setMapFilter,
        setQuery,
        setTermFilter,
    };
}

function createEmptySearchResults(): SearchResults {
    return {
        resources: [],
        aggregations: {},
        pagination: {
            page: FIRST_SEARCH_PAGE,
            page_size: SEARCH_RESULTS_PAGE_SIZE,
            total_results: 0,
            total_pages: 0,
            has_next: false,
            has_previous: false,
        },
    };
}

export function provideSearchFilters(): SearchFilters {
    const filters = createSearchFilters();
    provide(SEARCH_FILTERS_KEY, filters);
    return filters;
}

export function useSearchFilters(): SearchFilters {
    const filters = inject(SEARCH_FILTERS_KEY);

    if (!filters) {
        throw new Error(
            "a parent component must call provideSearchFilters before using useSearchFilters in a child component",
        );
    }

    return filters;
}
