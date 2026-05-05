import { computed, inject, provide, ref } from "vue";

import { fetchSearchResults } from "@/arches_search/SimpleSearch/api.ts";

import type { ComputedRef, InjectionKey, Ref } from "vue";
import { LogicToken } from "@/arches_search/AdvancedSearch/types.ts";
import type {
    GroupPayload,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    ActiveFilter,
    ResourceType,
    SortSpec,
} from "@/arches_search/SimpleSearch/types.ts";

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
    resultsGraph: Ref<ResourceType | null>;
    searchResults: Ref<SearchResults>;
    sort: Ref<SortSpec[]>;
    clearQuery(filterKey: string): void;
    clearTermFilter(key: string): void;
    search(page?: number): void;
    setGraph(graph: ResourceType | null): void;
    setQuery(filterKey: string, payload: GroupPayload): void;
    setSort(next: SortSpec[]): void;
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
// Empty by default: the user must pick a sort before one is applied. Populate
// with SortSpec entries to preset a sort without requiring user selection.
const DEFAULT_SORT: SortSpec[] = [];

function createSearchFilters(): SearchFilters {
    const terms = ref<Map<string, ActiveFilter>>(new Map());
    const queries = ref<Map<string, GroupPayload>>(new Map());
    const activeGraph = ref<ResourceType | null>(null);
    const resultsGraph = ref<ResourceType | null>(null);
    const searchResults = ref<SearchResults>(createEmptySearchResults());
    const isSearching = ref(false);
    const currentPage = ref(FIRST_SEARCH_PAGE);
    const sort = ref<SortSpec[]>(DEFAULT_SORT);
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

    function setGraph(graph: ResourceType | null): void {
        activeGraph.value = graph;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function setSort(next: SortSpec[]): void {
        sort.value = next;
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
                    sort: sort.value,
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
        const queryList = [...queries.value.values()];
        if (queryList.length === 0) return undefined;
        if (queryList.length === 1) return queryList[0];
        return {
            graph_slug: queryList[0].graph_slug,
            scope: queryList[0].scope,
            logic: LogicToken.AND,
            clauses: [],
            groups: queryList,
            aggregations: [],
            relationship: null,
        };
    }

    return {
        activeFilters,
        activeGraph,
        clearQuery,
        clearTermFilter,
        currentPage,
        isSearching,
        resultsGraph,
        search,
        searchResults,
        setGraph,
        setQuery,
        setSort,
        setTermFilter,
        sort,
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
