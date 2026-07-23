import { computed, inject, provide, ref } from "vue";
import { useGettext } from "vue3-gettext";

import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";
import {
    createSearchMVTContext,
    fetchSearchResults,
} from "@/arches_search/SimpleSearch/api.ts";

import type { ComputedRef, InjectionKey, Ref } from "vue";
import { LogicToken } from "@/arches_search/AdvancedSearch/types.ts";
import type {
    GroupPayload,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    ActiveFilter,
    ResourceType,
    SearchDefinition,
    SortSpec,
} from "@/arches_search/SimpleSearch/types.ts";
import type { FeatureCollection } from "geojson";

interface SearchRequestTerm {
    type: string;
    text: string;
    inverted: boolean;
}

interface ExportPayload {
    terms: SearchRequestTerm[];
    query: GroupPayload | undefined;
    graphId: string | null;
}

interface SearchFilters {
    activeFilters: ComputedRef<ActiveFilter[]>;
    activeGraph: Ref<ResourceType | null>;
    currentPage: Ref<number>;
    isSearching: Ref<boolean>;
    mapFilter: Ref<FeatureCollection | null>;
    queries: ComputedRef<ReadonlyMap<string, GroupPayload>>;
    resultsTileUrl: ComputedRef<string | null>;
    resultsGraph: Ref<ResourceType | null>;
    searchResults: Ref<SearchResults>;
    sort: Ref<SortSpec[]>;
    applySearchDefinition(definition: SearchDefinition): void;
    clearMapFilter(): void;
    clearQuery(filterKey: string): void;
    clearTermFilter(key: string): void;
    getExportPayload(): ExportPayload;
    getSearchDefinition(): SearchDefinition;
    search(page?: number): void;
    setGraph(graph: ResourceType | null): void;
    setMapFilter(featureCollection: FeatureCollection): void;
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
    const { $gettext } = useGettext();
    const terms = ref<Map<string, ActiveFilter>>(new Map());
    const queries = ref<Map<string, GroupPayload>>(new Map());
    const mapFilter = ref<FeatureCollection | null>(null);
    const activeGraph = ref<ResourceType | null>(null);
    const resultsGraph = ref<ResourceType | null>(null);
    const searchResults = ref<SearchResults>(createEmptySearchResults());
    const isSearching = ref(false);
    const currentPage = ref(FIRST_SEARCH_PAGE);
    const mvtContextId = ref<string | null>(null);
    const sort = ref<SortSpec[]>(DEFAULT_SORT);
    let searchTimeout: ReturnType<typeof setTimeout> | null = null;

    const resultsTileUrl = computed<string | null>(() => {
        if (!mvtContextId.value) return null;
        const path = generateArchesURL("arches_search:search_mvt", {
            context_id: mvtContextId.value,
            zoom: "{z}",
            x: "{x}",
            y: "{y}",
        });
        return `${window.location.origin}${path}`;
    });

    const activeFilters = computed<ActiveFilter[]>(() => {
        return [...terms.value.values()];
    });

    const queriesView = computed<ReadonlyMap<string, GroupPayload>>(
        () => queries.value,
    );

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
            kind: "term",
            category: $gettext("Search"),
            icon: "pi pi-search",
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
                const searchParams = {
                    terms: getRequestTerms(),
                    query: getRequestQuery(),
                    page,
                    graphId: requestGraph ? requestGraph.id : null,
                    mapFilter: mapFilter.value,
                    sort: sort.value,
                };

                const { page: _page, sort: _sort, ...mvtParams } = searchParams;
                const [results, context] = await Promise.all([
                    fetchSearchResults(searchParams),
                    createSearchMVTContext(mvtParams).catch((error) => {
                        throw new Error(
                            `Failed to create MVT context: ${error.message}`,
                        );
                    }),
                ]);

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
                mvtContextId.value = context?.context_id ?? null;
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

    function getSearchDefinition(): SearchDefinition {
        // Strip the `clear` closure off each ActiveFilter — closures aren't
        // serializable, and the restore path rebuilds them from `id`.
        const serializedTerms = [...terms.value.values()].map(
            ({ id, text, inverted, options }) => ({
                id,
                text,
                inverted,
                ...(options !== undefined ? { options } : {}),
            }),
        );
        return {
            version: 1,
            terms: serializedTerms,
            queries: Object.fromEntries(queries.value),
            graphId: activeGraph.value?.id ?? null,
        };
    }

    function applySearchDefinition(definition: SearchDefinition): void {
        // Clear current state first. Each setter triggers a debounced search,
        // so the cascade collapses to a single fetch on the trailing edge.
        for (const id of [...terms.value.keys()]) {
            clearTermFilter(id);
        }
        for (const filterKey of [...queries.value.keys()]) {
            clearQuery(filterKey);
        }

        if (definition.graphId) {
            setGraph({ id: definition.graphId, label: "", icon: "" });
        } else {
            setGraph(null);
        }

        for (const term of definition.terms) {
            setTermFilter(
                term.id,
                term.text,
                () => clearTermFilter(term.id),
                term.options,
            );
        }
        for (const [filterKey, payload] of Object.entries(definition.queries)) {
            setQuery(filterKey, payload);
        }
    }

    function getExportPayload(): ExportPayload {
        return {
            terms: getRequestTerms(),
            query: getRequestQuery(),
            graphId: activeGraph.value ? activeGraph.value.id : null,
        };
    }

    return {
        activeFilters,
        activeGraph,
        applySearchDefinition,
        clearMapFilter,
        clearQuery,
        clearTermFilter,
        currentPage,
        getSearchDefinition,
        getExportPayload,
        isSearching,
        mapFilter,
        queries: queriesView,
        resultsTileUrl,
        resultsGraph,
        search,
        searchResults,
        setGraph,
        setMapFilter,
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
