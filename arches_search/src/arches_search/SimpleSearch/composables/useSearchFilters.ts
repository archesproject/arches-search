import { computed, inject, provide, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import { generateArchesURL } from "@/arches_vue_components/application";
import { getGraphs } from "@/arches_search/AdvancedSearch/api.ts";
import {
    createSearchMVTContext,
    fetchNodeFilterConfig,
    fetchSearchResults,
} from "@/arches_search/SimpleSearch/api.ts";
import {
    buildAttributeFilterQuery,
    formatAttributeFilterValue,
    parseAttributeFilterValue,
} from "@/arches_search/SimpleSearch/components/attribute-filters/registry.ts";
import {
    buildRequestDateRange,
    buildRequestQueries,
    buildRequestTerms,
    foldQueriesIntoAdvancedQuery,
} from "@/arches_search/SimpleSearch/utils/search-definition.ts";

import type { ComputedRef, InjectionKey, Ref } from "vue";
import type {
    GraphModel,
    GroupPayload,
    QueryBuilderGroup,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import {
    ACTIVE_FILTER_KIND_TERM,
    ADVANCED_QUERY_KEY,
    TERM_KIND_CONTROLLED_TERM,
    TERM_KIND_RECORD,
    TIME_FILTER_QUERY_KEY,
} from "@/arches_search/SimpleSearch/types.ts";
import type {
    ActiveFilter,
    DateRangeFilter,
    NodeFilterConfigNode,
    ResourceFieldFilter,
    ResourceType,
    SearchDefinition,
    SearchRequestTerm,
    SerializedTerm,
    SortSpec,
    TermKind,
} from "@/arches_search/SimpleSearch/types.ts";
import type { FeatureCollection } from "geojson";

interface ExportPayload {
    terms: SearchRequestTerm[];
    queries: GroupPayload[];
    graphSlugs: string[];
    mapFilter: FeatureCollection | null;
    dateRange: DateRangeFilter | null;
    resourceFieldFilters: ResourceFieldFilter[] | null;
}

interface SearchFilters {
    activeFilters: ComputedRef<ActiveFilter[]>;
    activeGraphs: Ref<ResourceType[]>;
    advancedQuery: Ref<GroupPayload | null>;
    advancedQueryDraft: Ref<QueryBuilderGroup | null>;
    attributeFilterValues: ComputedRef<Record<string, unknown>>;
    unrepresentedQueryKeys: ComputedRef<string[]>;
    availableGraphs: Ref<ResourceType[]>;
    loadAvailableGraphs(): Promise<void>;
    currentPage: Ref<number>;
    isSearching: Ref<boolean>;
    mapFilter: Ref<FeatureCollection | null>;
    nodeFilterConfigNodes: Ref<NodeFilterConfigNode[]>;
    resourceFieldFilters: Ref<Map<string, ResourceFieldFilter>>;
    queries: ComputedRef<ReadonlyMap<string, GroupPayload>>;
    resultsTileUrl: ComputedRef<string | null>;
    resultsGraphs: Ref<ResourceType[]>;
    savedSearchName: Ref<string | null>;
    searchResults: Ref<SearchResults>;
    singleActiveGraph: ComputedRef<ResourceType | null>;
    sort: Ref<SortSpec[]>;
    applySearchDefinition(
        definition: SearchDefinition,
        searchName?: string | null,
    ): Promise<void>;
    applyAdvancedQuery(payload: GroupPayload | null): void;
    foldUnrepresentedQueriesIntoAdvancedQuery(): void;
    clearAll(): void;
    clearAttributeFilter(nodeAlias: string): void;
    clearMapFilter(): void;
    clearQuery(filterKey: string): void;
    clearTermFilter(id: string): void;
    getExportPayload(): ExportPayload;
    getSearchDefinition(): SearchDefinition;
    search(page?: number): void;
    setAdvancedQuery(payload: GroupPayload | null): void;
    setAdvancedQueryDraft(root: QueryBuilderGroup | null): void;
    setAttributeFilter(nodeAlias: string, value: unknown): void;
    setGraphsBySlug(graphSlugs: string[]): Promise<void>;
    setMapFilter(featureCollection: FeatureCollection): void;
    setQuery(filterKey: string, payload: GroupPayload): void;
    setResourceFieldFilter(
        field: string,
        filter: ResourceFieldFilter | null,
    ): void;
    clearResourceFieldFilters(): void;
    setSort(next: SortSpec[]): void;
    setTermFilter(term: SerializedTerm): void;
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
    const terms = ref<SerializedTerm[]>([]);
    const queries = ref<Map<string, GroupPayload>>(new Map());
    const advancedQuery = ref<GroupPayload | null>(null);
    const advancedQueryDraft = ref<QueryBuilderGroup | null>(null);
    const mapFilter = ref<FeatureCollection | null>(null);
    // Keyed by field name so re-selecting a field replaces its filter rather
    // than stacking a second, contradictory one.
    const resourceFieldFilters = ref<Map<string, ResourceFieldFilter>>(
        new Map(),
    );
    const activeGraphs = ref<ResourceType[]>([]);
    // Every searchable resource model.
    const availableGraphs = ref<ResourceType[]>([]);
    let availableGraphsRequest: Promise<void> | null = null;
    const nodeFilterConfigNodes = ref<NodeFilterConfigNode[]>([]);
    let nodeFilterConfigRequestGraphId: string | null = null;
    const storedAttributeFilterValues = ref<Record<string, unknown>>({});
    const savedSearchName = ref<string | null>(null);
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
        return terms.value.map((term) => ({
            id: term.id,
            text: term.text,
            clear: () => clearTermFilter(term.id),
            inverted: term.inverted,
            kind: term.termKind ?? ACTIVE_FILTER_KIND_TERM,
            category: getTermFilterCategory(term.termKind),
            icon: term.icon || getTermFilterIcon(term.termKind),
            options: term.options,
        }));
    });

    const queriesView = computed<ReadonlyMap<string, GroupPayload>>(
        () => queries.value,
    );

    const singleActiveGraph = computed<ResourceType | null>(() => {
        if (activeGraphs.value.length !== 1) {
            return null;
        }
        return activeGraphs.value[0];
    });

    // A value the widget emitted wins over one parsed back out of its query:
    // re-parsing while the user types would rewrite their input.
    const attributeFilterValues = computed<Record<string, unknown>>(() => {
        return Object.fromEntries(
            nodeFilterConfigNodes.value.flatMap((node) => {
                const query = queries.value.get(node.node_alias);
                if (!query) {
                    return [];
                }
                const value =
                    storedAttributeFilterValues.value[node.node_alias] ??
                    parseAttributeFilterValue(node, query);
                return [[node.node_alias, value]];
            }),
        );
    });

    // Keyed queries the filters cannot show, like those of searches saved
    // before a node had a filter.
    const unrepresentedQueryKeys = computed<string[]>(() => {
        const representedKeys = new Set<string>([TIME_FILTER_QUERY_KEY]);
        for (const node of nodeFilterConfigNodes.value) {
            const formattedValue = formatAttributeFilterValue(
                node,
                attributeFilterValues.value[node.node_alias],
            );
            if (queries.value.has(node.node_alias) && formattedValue) {
                representedKeys.add(node.node_alias);
            }
        }
        return [...queries.value.keys()].filter(
            (filterKey) => !representedKeys.has(filterKey),
        );
    });

    watch(activeGraphs, (graphs) => {
        dropFiltersForOtherGraphs(graphs);
        void loadNodeFilterConfig(singleActiveGraph.value);
    });

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

    // Time and attribute filters only exist while exactly one resource model is
    // selected, and filter that model; switching models leaves them behind.
    function dropFiltersForOtherGraphs(graphs: ResourceType[]): void {
        const nextGraphSlug = graphs.length === 1 ? graphs[0].slug : null;
        const singleGraphFilterKeys = [
            TIME_FILTER_QUERY_KEY,
            ...nodeFilterConfigNodes.value.map((node) => node.node_alias),
        ];

        const nextQueries = new Map(queries.value);
        for (const filterKey of singleGraphFilterKeys) {
            const query = nextQueries.get(filterKey);
            if (query && query.graph_slug !== nextGraphSlug) {
                nextQueries.delete(filterKey);
            }
        }
        queries.value = nextQueries;
        storedAttributeFilterValues.value = {};
    }

    async function loadNodeFilterConfig(
        graph: ResourceType | null,
    ): Promise<void> {
        const graphId = graph?.id ?? null;
        nodeFilterConfigRequestGraphId = graphId;
        if (!graphId) {
            nodeFilterConfigNodes.value = [];
            return;
        }

        try {
            const config = await fetchNodeFilterConfig(graphId);
            if (nodeFilterConfigRequestGraphId === graphId) {
                nodeFilterConfigNodes.value = config.nodes;
            }
        } catch (error) {
            console.error(error);
            if (nodeFilterConfigRequestGraphId === graphId) {
                nodeFilterConfigNodes.value = [];
            }
        }
    }

    function setTermFilter(term: SerializedTerm): void {
        const existingIndex = terms.value.findIndex(
            (existingTerm) => existingTerm.id === term.id,
        );
        const nextTerms = [...terms.value];
        if (existingIndex === -1) {
            nextTerms.push(term);
        } else {
            nextTerms[existingIndex] = term;
        }
        terms.value = nextTerms;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function clearTermFilter(id: string): void {
        terms.value = terms.value.filter((term) => term.id !== id);
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

    // Each attribute-filter widget emits a datatype-specific value; the registry
    // turns it into a query (or null to clear). Query-shape logic lives in the
    // per-datatype builders, so this handler stays datatype-agnostic.
    function setAttributeFilter(nodeAlias: string, value: unknown): void {
        storedAttributeFilterValues.value = {
            ...storedAttributeFilterValues.value,
            [nodeAlias]: value,
        };

        const node = nodeFilterConfigNodes.value.find(
            (candidate) => candidate.node_alias === nodeAlias,
        );
        const graphSlug = singleActiveGraph.value?.slug;
        if (!node || !graphSlug) {
            return;
        }

        const query = buildAttributeFilterQuery(node, value, graphSlug);
        if (query) {
            setQuery(nodeAlias, query);
        } else {
            clearQuery(nodeAlias);
        }
    }

    function clearAttributeFilter(nodeAlias: string): void {
        const { [nodeAlias]: _removedValue, ...remainingValues } =
            storedAttributeFilterValues.value;
        storedAttributeFilterValues.value = remainingValues;
        clearQuery(nodeAlias);
    }

    function setAdvancedQuery(payload: GroupPayload | null): void {
        advancedQuery.value = payload;
        advancedQueryDraft.value = null;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function foldUnrepresentedQueriesIntoAdvancedQuery(): void {
        const unrepresentedQueries = new Map(
            [...queries.value].filter(([filterKey]) =>
                unrepresentedQueryKeys.value.includes(filterKey),
            ),
        );
        const folded = foldQueriesIntoAdvancedQuery(
            advancedQuery.value,
            unrepresentedQueries,
        );
        if (!folded) {
            return;
        }
        const nextQueries = new Map(queries.value);
        for (const foldedKey of folded.foldedKeys) {
            nextQueries.delete(foldedKey);
        }
        queries.value = nextQueries;
        setAdvancedQuery(folded.advancedQuery);
    }

    // Advanced Search runs its own search over the query alone; Simple Search
    // searches again with it when next opened.
    function applyAdvancedQuery(payload: GroupPayload | null): void {
        advancedQuery.value = payload;
    }

    function setAdvancedQueryDraft(root: QueryBuilderGroup | null): void {
        advancedQueryDraft.value = root;
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

    function resetFilters(): void {
        terms.value = [];
        queries.value = new Map();
        advancedQuery.value = null;
        advancedQueryDraft.value = null;
        storedAttributeFilterValues.value = {};
        mapFilter.value = null;
        resourceFieldFilters.value = new Map();
        activeGraphs.value = [];
        savedSearchName.value = null;
        currentPage.value = FIRST_SEARCH_PAGE;
    }

    function clearAll(): void {
        resetFilters();
        search();
    }

    function loadAvailableGraphs(): Promise<void> {
        if (!availableGraphsRequest) {
            availableGraphsRequest = getGraphs()
                .then((graphs: GraphModel[]) => {
                    availableGraphs.value = graphs
                        .filter((graph) => graph.isresource && graph.is_active)
                        .map((graph) => ({
                            id: graph.graphid,
                            slug: graph.slug,
                            label: graph.name,
                            icon: graph.iconclass,
                        }));
                })
                .catch((error) => {
                    // Unset, so a later search can retry.
                    availableGraphsRequest = null;
                    throw error;
                });
        }
        return availableGraphsRequest;
    }

    function getRequestGraphs(): ResourceType[] {
        // "All" is an empty activeGraphs; the API will not accept that as a
        // selection, so it has to be spelled out.
        if (activeGraphs.value.length > 0) {
            return activeGraphs.value;
        }
        return availableGraphs.value;
    }

    function getRequestQueries(requestGraphSlugs: string[]): GroupPayload[] {
        const candidateQueries = [...queries.value.values()];
        if (advancedQuery.value) {
            candidateQueries.push(advancedQuery.value);
        }
        return buildRequestQueries(candidateQueries, requestGraphSlugs);
    }

    function setGraphs(graphs: ResourceType[]): void {
        activeGraphs.value = graphs;
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function findAvailableGraphs(graphSlugs: string[]): ResourceType[] {
        return graphSlugs
            .map((slug) =>
                availableGraphs.value.find((graph) => graph.slug === slug),
            )
            .filter((graph): graph is ResourceType => graph !== undefined);
    }

    // "All" is saved as every resource model by name, which reads back as each
    // one selected individually; selecting every one is "All".
    function findSavedGraphSelection(graphSlugs: string[]): ResourceType[] {
        const savedGraphs = findAvailableGraphs(graphSlugs);
        if (
            availableGraphs.value.length > 0 &&
            savedGraphs.length === availableGraphs.value.length
        ) {
            return [];
        }
        return savedGraphs;
    }

    async function setGraphsBySlug(graphSlugs: string[]): Promise<void> {
        await loadAvailableGraphs();
        setGraphs(findAvailableGraphs(graphSlugs));
    }

    function toggleGraph(resourceType: ResourceType): void {
        if (resourceType.id === null) {
            setGraphs([]);
            return;
        }

        const isActive = activeGraphs.value.some(
            (graph) => graph.id === resourceType.id,
        );

        let nextGraphs: ResourceType[];
        if (isActive) {
            nextGraphs = activeGraphs.value.filter(
                (graph) => graph.id !== resourceType.id,
            );
        } else {
            nextGraphs = [...activeGraphs.value, resourceType];
        }

        setGraphs(nextGraphs);
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
                await loadAvailableGraphs();
                const requestGraphs = getRequestGraphs();
                const requestGraphSlugs = requestGraphs.map(
                    (graph) => graph.slug,
                );
                const searchParams = {
                    terms: buildRequestTerms(terms.value),
                    queries: getRequestQueries(requestGraphSlugs),
                    dateRange: buildRequestDateRange([
                        ...queries.value.values(),
                    ]),
                    page,
                    graphSlugs: requestGraphSlugs,
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
            } catch (error) {
                console.error(error);
            } finally {
                isSearching.value = false;
            }
        }, SEARCH_DEBOUNCE_MS);
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

    function clearResourceFieldFilters(): void {
        resourceFieldFilters.value = new Map();
        currentPage.value = FIRST_SEARCH_PAGE;
        search();
    }

    function getRequestResourceFieldFilters(): ResourceFieldFilter[] | null {
        const filters = [...resourceFieldFilters.value.values()];
        return filters.length > 0 ? filters : null;
    }

    function getSearchDefinition(): SearchDefinition {
        const serializedTerms = terms.value.map(serializeTerm);

        const savedQueries: Record<string, GroupPayload> = Object.fromEntries(
            queries.value,
        );
        if (advancedQuery.value) {
            savedQueries[ADVANCED_QUERY_KEY] = advancedQuery.value;
        }

        return {
            terms: serializedTerms,
            queries: savedQueries,
            graphSlugs: getRequestGraphs().map((graph) => graph.slug),
            mapFilter: mapFilter.value,
            sort: sort.value,
        };
    }

    async function applySearchDefinition(
        definition: SearchDefinition,
        searchName: string | null = null,
    ): Promise<void> {
        await loadAvailableGraphs();

        resetFilters();
        const { [ADVANCED_QUERY_KEY]: savedAdvancedQuery, ...keyedQueries } =
            definition.queries;

        terms.value = definition.terms.map((term) => ({ ...term }));
        queries.value = new Map(Object.entries(keyedQueries));
        advancedQuery.value = savedAdvancedQuery ?? null;
        mapFilter.value = definition.mapFilter;
        activeGraphs.value = findSavedGraphSelection(definition.graphSlugs);
        sort.value = definition.sort ?? DEFAULT_SORT;
        savedSearchName.value = searchName;
        search();
    }

    function getExportPayload(): ExportPayload {
        const requestGraphSlugs = getRequestGraphs().map((graph) => graph.slug);
        return {
            terms: buildRequestTerms(terms.value),
            queries: getRequestQueries(requestGraphSlugs),
            graphSlugs: requestGraphSlugs,
            mapFilter: mapFilter.value,
            dateRange: buildRequestDateRange([...queries.value.values()]),
            resourceFieldFilters: getRequestResourceFieldFilters(),
        };
    }

    return {
        activeFilters,
        activeGraphs,
        advancedQuery,
        advancedQueryDraft,
        attributeFilterValues,
        unrepresentedQueryKeys,
        availableGraphs,
        loadAvailableGraphs,
        applyAdvancedQuery,
        foldUnrepresentedQueriesIntoAdvancedQuery,
        applySearchDefinition,
        clearAll,
        clearAttributeFilter,
        clearMapFilter,
        clearQuery,
        clearTermFilter,
        currentPage,
        getSearchDefinition,
        getExportPayload,
        isSearching,
        mapFilter,
        nodeFilterConfigNodes,
        queries: queriesView,
        resourceFieldFilters,
        resultsTileUrl,
        resultsGraphs,
        savedSearchName,
        search,
        setAdvancedQuery,
        setAdvancedQueryDraft,
        setAttributeFilter,
        setResourceFieldFilter,
        clearResourceFieldFilters,
        searchResults,
        setGraphsBySlug,
        setMapFilter,
        setQuery,
        setSort,
        setTermFilter,
        singleActiveGraph,
        sort,
        toggleGraph,
    };
}

function serializeTerm(term: SerializedTerm): SerializedTerm {
    const serializedTerm: SerializedTerm = {
        id: term.id,
        text: term.text,
        inverted: term.inverted,
    };
    if (term.termKind) {
        serializedTerm.termKind = term.termKind;
    }
    if (term.termKind === TERM_KIND_RECORD && term.icon) {
        serializedTerm.icon = term.icon;
    }
    if (term.options !== undefined) {
        serializedTerm.options = term.options;
    }
    return serializedTerm;
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
