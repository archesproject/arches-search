import { computed, inject, provide, ref } from "vue";
import { useGettext } from "vue3-gettext";

import { generateArchesURL } from "@/arches_vue_components/application";
import {
    createSearchMVTContext,
    fetchSearchResults,
} from "@/arches_search/SimpleSearch/api.ts";

import type { ComputedRef, InjectionKey, Ref } from "vue";
import {
    ClauseSubjectTypeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    GroupPayload,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import {
    ACTIVE_FILTER_KIND_TERM,
    TERM_KIND_CONTROLLED_TERM,
    TERM_KIND_RECORD,
} from "@/arches_search/SimpleSearch/types.ts";
import type {
    ActiveFilter,
    ResourceFieldFilter,
    ResourceType,
    SearchDefinition,
    SortSpec,
    TermKind,
} from "@/arches_search/SimpleSearch/types.ts";
import type { FeatureCollection } from "geojson";

interface SearchRequestTerm {
    type: string;
    text: string;
    inverted: boolean;
}

interface DateRangeFilter {
    from: string;
    to: string;
}

interface ExportPayload {
    terms: SearchRequestTerm[];
    query: GroupPayload | undefined;
    graphIds: string[];
    dateRange: DateRangeFilter | null;
}

interface SearchFilters {
    activeFilters: ComputedRef<ActiveFilter[]>;
    activeGraphs: Ref<ResourceType[]>;
    currentPage: Ref<number>;
    isSearching: Ref<boolean>;
    mapFilter: Ref<FeatureCollection | null>;
    resourceFieldFilters: Ref<Map<string, ResourceFieldFilter>>;
    queries: ComputedRef<ReadonlyMap<string, GroupPayload>>;
    resultsTileUrl: ComputedRef<string | null>;
    resultsGraphs: Ref<ResourceType[]>;
    searchResults: Ref<SearchResults>;
    sort: Ref<SortSpec[]>;
    applySearchDefinition(definition: SearchDefinition): void;
    clearMapFilter(): void;
    clearQuery(filterKey: string): void;
    clearTermFilter(key: string): void;
    getExportPayload(): ExportPayload;
    getSearchDefinition(): SearchDefinition;
    search(page?: number): void;
    setMapFilter(featureCollection: FeatureCollection): void;
    setQuery(filterKey: string, payload: GroupPayload): void;
    setResourceFieldFilter(
        field: string,
        filter: ResourceFieldFilter | null,
    ): void;
    clearResourceFieldFilters(): void;
    setSort(next: SortSpec[]): void;
    setTermFilter(
        key: string,
        text: string,
        clear: () => void,
        options?: Record<string, unknown>,
        termKind?: TermKind,
        icon?: string,
    ): void;
    toggleGraph(resourceType: ResourceType): void;
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
    // Keyed by field name so re-selecting a field replaces its filter rather
    // than stacking a second, contradictory one.
    const resourceFieldFilters = ref<Map<string, ResourceFieldFilter>>(
        new Map(),
    );
    const activeGraphs = ref<ResourceType[]>([]);
    const resultsGraphs = ref<ResourceType[]>([]);
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

    function getTermFilterCategory(termKind?: TermKind): string {
        if (termKind === TERM_KIND_CONTROLLED_TERM) {
            return $gettext("Term");
        }
        if (termKind === TERM_KIND_RECORD) {
            return $gettext("Record");
        }
        return $gettext("Search");
    }

    function getTermFilterIcon(termKind?: TermKind): string {
        if (termKind === TERM_KIND_CONTROLLED_TERM) {
            return "pi pi-tag";
        }
        if (termKind === TERM_KIND_RECORD) {
            return "pi pi-database";
        }
        return "pi pi-search";
    }

    function setTermFilter(
        key: string,
        text: string,
        clear: () => void,
        options?: Record<string, unknown>,
        termKind?: TermKind,
        icon?: string,
    ): void {
        const next = new Map(terms.value);
        next.set(key, {
            id: key,
            text,
            clear,
            inverted: false,
            kind: termKind ?? ACTIVE_FILTER_KIND_TERM,
            category: getTermFilterCategory(termKind),
            icon: icon || getTermFilterIcon(termKind),
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

    function setGraphs(graphs: ResourceType[]): void {
        activeGraphs.value = graphs;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function toggleGraph(resourceType: ResourceType): void {
        if (resourceType.id === null) {
            setGraphs([]);
            return;
        }

        const isActive = activeGraphs.value.some(
            (graph) => graph.id === resourceType.id,
        );
        setGraphs(
            isActive
                ? activeGraphs.value.filter(
                      (graph) => graph.id !== resourceType.id,
                  )
                : [...activeGraphs.value, resourceType],
        );
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
                const requestGraphs = activeGraphs.value;
                const searchParams = {
                    terms: getRequestTerms(),
                    query: getRequestQuery(),
                    dateRange: getNodeAgnosticDateRange(),
                    page,
                    graphIds: requestGraphs.map((graph) => graph.id as string),
                    mapFilter: mapFilter.value,
                    resourceFieldFilters: getRequestResourceFieldFilters(),
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

                resultsGraphs.value = requestGraphs;
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

    function isNodeAgnosticDateQuery(payload: GroupPayload): boolean {
        return (
            payload.clauses.length === 1 &&
            payload.clauses[0].subject.type ===
                ClauseSubjectTypeToken.SEARCH_MODELS
        );
    }

    function getNodeAgnosticDateRange(): DateRangeFilter | null {
        for (const payload of queries.value.values()) {
            if (!isNodeAgnosticDateQuery(payload)) {
                continue;
            }
            const [fromOperand, toOperand] = payload.clauses[0].operands;
            return {
                from: fromOperand.value as string,
                to:
                    (toOperand?.value as string | undefined) ??
                    (fromOperand.value as string),
            };
        }
        return null;
    }

    function setResourceFieldFilter(
        field: string,
        filter: ResourceFieldFilter | null,
    ) {
        const next = new Map(resourceFieldFilters.value);
        if (filter === null) {
            next.delete(field);
        } else {
            next.set(field, filter);
        }
        resourceFieldFilters.value = next;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function clearResourceFieldFilters() {
        resourceFieldFilters.value = new Map();
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function getRequestResourceFieldFilters(): ResourceFieldFilter[] | null {
        const filters = [...resourceFieldFilters.value.values()];
        return filters.length > 0 ? filters : null;
    }

    function getRequestQuery(): GroupPayload | undefined {
        const queryList = [...queries.value.values()].filter(
            (payload) => !isNodeAgnosticDateQuery(payload),
        );
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
            ({ id, text, inverted, kind, icon, options }) => ({
                id,
                text,
                inverted,
                ...(kind === TERM_KIND_CONTROLLED_TERM ||
                kind === TERM_KIND_RECORD
                    ? { termKind: kind }
                    : {}),
                ...(kind === TERM_KIND_RECORD ? { icon } : {}),
                ...(options !== undefined ? { options } : {}),
            }),
        );
        return {
            terms: serializedTerms,
            queries: Object.fromEntries(queries.value),
            graphIds: activeGraphs.value.map((graph) => graph.id as string),
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

        setGraphs(
            definition.graphIds.map((id) => ({ id, label: "", icon: "" })),
        );

        for (const term of definition.terms) {
            setTermFilter(
                term.id,
                term.text,
                () => clearTermFilter(term.id),
                term.options,
                term.termKind,
                term.icon,
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
            graphIds: activeGraphs.value.map((graph) => graph.id as string),
            dateRange: getNodeAgnosticDateRange(),
        };
    }

    return {
        activeFilters,
        activeGraphs,
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
        resourceFieldFilters,
        resultsTileUrl,
        resultsGraphs,
        search,
        setResourceFieldFilter,
        clearResourceFieldFilters,
        searchResults,
        setMapFilter,
        setQuery,
        setSort,
        setTermFilter,
        sort,
        toggleGraph,
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
        resource_type_counts: [],
        all_resource_count: 0,
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
