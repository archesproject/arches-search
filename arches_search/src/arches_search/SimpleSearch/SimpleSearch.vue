<script setup lang="ts">
import {
    computed,
    defineAsyncComponent,
    onMounted,
    ref,
    watch,
    watchEffect,
} from "vue";
import dayjs from "dayjs";
import { useRouter } from "vue-router";
import { useGettext } from "vue3-gettext";

import Splitter from "openvue/splitter";
import SplitterPanel from "openvue/splitterpanel";
import Toast from "openvue/toast";

import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";
import ActiveFilters from "@/arches_search/SimpleSearch/components/ActiveFilters.vue";
import AttributeFilters from "@/arches_search/SimpleSearch/components/attribute-filters/AttributeFilters.vue";
import ExportResultsPanel from "@/arches_search/SimpleSearch/components/ExportResultsPanel.vue";
import IdleInfoTiles from "@/arches_search/SimpleSearch/components/IdleInfoTiles.vue";
import ResourceTypeFilter from "@/arches_search/SimpleSearch/components/ResourceTypeFilter.vue";
import ResultsToolbar from "@/arches_search/SimpleSearch/components/ResultsToolbar.vue";
import SavedSearchPanel from "@/arches_search/SimpleSearch/components/SavedSearchPanel.vue";
import TermFilter from "@/arches_search/SimpleSearch/components/TermFilter/TermFilter.vue";
import MapFilterPanel from "@/arches_search/SimpleSearch/components/MapFilterPanel.vue";
import TimeFilter from "@/arches_search/SimpleSearch/components/TimeFilter/TimeFilter.vue";

import { useToast } from "openvue/usetoast";
import { getGraphs } from "@/arches_search/AdvancedSearch/api.ts";
import {
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import { routeNames } from "@/arches_search/routes.ts";
import { formatAttributeFilterValue } from "@/arches_search/SimpleSearch/components/attribute-filters/registry.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import {
    ACTIVE_FILTER_KIND_ATTRIBUTE,
    ACTIVE_FILTER_KIND_MAP,
    ACTIVE_FILTER_KIND_RESOURCE_TYPE,
    ACTIVE_FILTER_KIND_TIME,
    ADVANCED_QUERY_KEY,
    EXPORT_STATE_IDLE,
    TERM_FILTER_KEY,
    TIME_FILTER_QUERY_KEY,
} from "@/arches_search/SimpleSearch/types.ts";
import { useResultsExport } from "@/arches_search/SimpleSearch/composables/useResultsExport.ts";
import { useSidePanel } from "@/arches_search/SimpleSearch/composables/useSidePanel.ts";
import { applyPendingSearch } from "@/arches_search/SimpleSearch/utils/apply-pending-search.ts";
import {
    sortDirectionForSpecs,
    sortFieldForSpecs,
    sortSpecForField,
} from "@/arches_search/SimpleSearch/utils/results-sort.ts";
import { parseSearchDefinition } from "@/arches_search/SimpleSearch/utils/search-definition.ts";
import { usePendingSearchStore } from "@/arches_search/stores/usePendingSearchStore.ts";
import { parseStoredDate } from "@/arches_search/AdvancedSearch/utils/advanced-search-payload-builder.ts";
import { toError } from "@/arches_search/AdvancedSearch/utils/errors.ts";

import type { FeatureCollection } from "geojson";
import type {
    GraphModel,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    ActiveFilter,
    ExportRequest,
    NodeFilterConfigNode,
    ResultsSortDirection,
    ResultsSortField,
    SearchDefinition,
} from "@/arches_search/SimpleSearch/types.ts";

// Kept out of the search page's own code, as most visits never open it and it
// brings a graph library with it
const RelationshipGraph = defineAsyncComponent(
    () => import("@/arches_search/RelationshipGraph/RelationshipGraph.vue"),
);

const INITIAL_RESULTS_PAGE = 1;
const RESULTS_PANEL_MIN_SIZE = 20;
const UNREPRESENTED_QUERIES_FILTER_ID = "unrepresentedQueries";

const { $gettext } = useGettext();
const toast = useToast();
const router = useRouter();

const {
    activeFilters,
    activeGraphs,
    advancedQuery,
    applySearchDefinition,
    attributeFilterValues,
    clearAll,
    clearAttributeFilter,
    clearMapFilter,
    clearQuery,
    getExportPayload,
    getSearchDefinition,
    isSearching,
    mapFilter,
    nodeFilterConfigNodes,
    queries,
    savedSearchName,
    search,
    searchResults,
    setAdvancedQuery,
    setAttributeFilter,
    setGraphsBySlug,
    setMapFilter,
    setQuery,
    setSort,
    setTermFilter,
    singleActiveGraph,
    sort,
    toggleGraph,
    unrepresentedQueryKeys,
} = useSearchFilters();

const {
    isIdle,
    isAttributeFiltersActive,
    isAttributeFiltersOpen,
    isMapFilterActive,
    isMapFilterOpen,
    isSavedSearchesActive,
    isSavedSearchesOpen,
    isExportResultsActive,
    isExportResultsOpen,
    isTimeFilterActive,
    isTimeFilterOpen,
    isRelatedResourcesOpen,
    relatedResources,
    resultsPanelSize,
    visibleSidePanelSize,
    sidePanelMinSize,
    sidePanelContentClass,
    sidePanelStyle,
    closeSidePanel,
    removeRelatedResource,
    setRelatedResourcesGraphVisible,
    onToggleAttributeFilters,
    onToggleMapFilter,
    onToggleSavedSearches,
    onToggleExportResults,
    onToggleTimeFilter,
    openAttributeFilters,
    openMapFilter,
    openTimeFilter,
    onSplitterResizeStart,
    onSplitterResize,
    onSplitterResizeEnd,
} = useSidePanel();
const { exportState, exportResults } = useResultsExport();

const graphModels = ref<GraphModel[]>([]);

const searchDefinition = computed<SearchDefinition>(() =>
    getSearchDefinition(),
);

const sortField = computed<ResultsSortField>(() =>
    sortFieldForSpecs(sort.value),
);

const sortDirection = computed<ResultsSortDirection>(() =>
    sortDirectionForSpecs(sort.value),
);

const isSingleGraphSelected = computed<boolean>(
    () => singleActiveGraph.value !== null,
);

const activeGraphId = computed<string | null>(
    () => singleActiveGraph.value?.id ?? null,
);

const activeGraphLabel = computed<string | null>(
    () => singleActiveGraph.value?.label ?? null,
);

const filterableNodeFilterConfigNodes = computed<NodeFilterConfigNode[]>(() =>
    nodeFilterConfigNodes.value.filter(
        (node: NodeFilterConfigNode) => node.filterable,
    ),
);

const sortableNodeFilterConfigNodes = computed<NodeFilterConfigNode[]>(() =>
    nodeFilterConfigNodes.value.filter(
        (node: NodeFilterConfigNode) => node.sortable,
    ),
);

const activeGraphSlug = computed<string | null>(
    () => singleActiveGraph.value?.slug ?? null,
);

const timeFilterQuery = computed(
    () => queries.value.get(TIME_FILTER_QUERY_KEY) ?? null,
);

const timeFilterClauses = computed<LiteralClause[]>(
    () => timeFilterQuery.value?.clauses ?? [],
);

const hasTimeFilter = computed<boolean>(
    () => timeFilterClauses.value.length > 0,
);

// The chip row surfaces every active filter, but only term/resource-type
// filters live in the always-visible top bar — time/map/attribute filters
// live behind the collapsible side panel, so their chips get an onEdit that
// reopens it (openXFilter, not onToggleXFilter — a toggle would close an
// already-open panel instead of keeping it open for editing).
const resourceTypeActiveFilters = computed<ActiveFilter[]>(() =>
    activeGraphs.value.map((graph) => {
        const graphModel = graphModels.value.find(
            (candidate) => candidate.graphid === graph.id,
        );

        return {
            id: `resourceType:${graph.id}`,
            text: graphModel?.name ?? graph.label,
            clear: () => toggleGraph(graph),
            inverted: false,
            kind: ACTIVE_FILTER_KIND_RESOURCE_TYPE,
            category: $gettext("Type"),
            icon: graphModel?.iconclass ?? graph.icon,
        };
    }),
);

const timeActiveFilter = computed<ActiveFilter | null>(() => {
    const clause = timeFilterClauses.value[0];
    if (!clause) {
        return null;
    }

    return {
        id: TIME_FILTER_QUERY_KEY,
        text: formatTimeFilterLabel(clause),
        clear: onRemoveTimeFilter,
        inverted: false,
        kind: ACTIVE_FILTER_KIND_TIME,
        category: $gettext("Date"),
        icon: "pi pi-clock",
        onEdit: openTimeFilter,
    };
});

const mapActiveFilter = computed<ActiveFilter | null>(() => {
    const featureCount = mapFilter.value?.features.length ?? 0;
    if (featureCount === 0) {
        return null;
    }

    return {
        id: "mapFilter",
        text: $gettext("%{count} area(s) selected", {
            count: String(featureCount),
        }),
        clear: onRemoveMapFilter,
        inverted: false,
        kind: ACTIVE_FILTER_KIND_MAP,
        category: $gettext("Area"),
        icon: "pi pi-map",
        onEdit: openMapFilter,
    };
});

const attributeActiveFilters = computed<ActiveFilter[]>(() => {
    return nodeFilterConfigNodes.value.flatMap((node) => {
        if (!queries.value.has(node.node_alias)) {
            return [];
        }

        const text = formatAttributeFilterValue(
            node,
            attributeFilterValues.value[node.node_alias],
        );
        if (!text) {
            return [];
        }

        return [
            {
                id: node.node_alias,
                text,
                clear: () => clearAttributeFilter(node.node_alias),
                inverted: false,
                kind: ACTIVE_FILTER_KIND_ATTRIBUTE,
                category: node.label,
                icon: "pi pi-filter",
                onEdit: openAttributeFilters,
            },
        ];
    });
});

const unrepresentedQueriesActiveFilter = computed<ActiveFilter | null>(() => {
    if (unrepresentedQueryKeys.value.length === 0) {
        return null;
    }

    return {
        id: UNREPRESENTED_QUERIES_FILTER_ID,
        text: savedSearchName.value ?? $gettext("Saved filters"),
        clear: () => {
            for (const filterKey of unrepresentedQueryKeys.value) {
                clearQuery(filterKey);
            }
        },
        inverted: false,
        kind: ACTIVE_FILTER_KIND_ATTRIBUTE,
        category: $gettext("Saved search"),
        icon: "pi pi-bookmark",
    };
});

const advancedQueryActiveFilter = computed<ActiveFilter | null>(() => {
    const appliedQuery = advancedQuery.value;
    if (!appliedQuery) {
        return null;
    }

    const graphName =
        graphModels.value.find(
            (graphModel) => graphModel.slug === appliedQuery.graph_slug,
        )?.name ?? appliedQuery.graph_slug;
    const isModelSearched =
        activeGraphs.value.length === 0 ||
        activeGraphs.value.some(
            (graph) => graph.slug === appliedQuery.graph_slug,
        );

    let inactiveNote: string | undefined;
    if (!isModelSearched) {
        inactiveNote = $gettext(
            "Not applied while %{model} is not selected. Select it to apply the advanced query.",
            { model: graphName },
        );
    }

    return {
        id: ADVANCED_QUERY_KEY,
        text: graphName,
        clear: () => setAdvancedQuery(null),
        inverted: false,
        kind: ACTIVE_FILTER_KIND_ATTRIBUTE,
        category: $gettext("Advanced search"),
        icon: "pi pi-sliders-h",
        onEdit: openAdvancedSearch,
        inactiveNote,
    };
});

const allActiveFilters = computed<ActiveFilter[]>(() =>
    [
        ...activeFilters.value,
        ...resourceTypeActiveFilters.value,
        timeActiveFilter.value,
        mapActiveFilter.value,
        ...attributeActiveFilters.value,
        unrepresentedQueriesActiveFilter.value,
        advancedQueryActiveFilter.value,
    ].filter(
        (activeFilter): activeFilter is ActiveFilter => activeFilter !== null,
    ),
);

watch(isExportResultsOpen, (isOpen) => {
    if (!isOpen) {
        exportState.value = EXPORT_STATE_IDLE;
    }
});

// Attribute and time filters are single-graph features, so their panels
// close once more or fewer than one resource model is selected.
watch(singleActiveGraph, (graph) => {
    if (graph) {
        return;
    }
    if (isTimeFilterOpen.value || isAttributeFiltersOpen.value) {
        closeSidePanel();
    }
});

watchEffect(() => {
    void initializeSearch();
});

onMounted(() => {
    const pendingSearch = usePendingSearchStore().consume();
    if (pendingSearch) {
        applyPendingSearch(pendingSearch, {
            applySearchDefinition: applySavedSearch,
            clearAll,
            openMapFilter,
            setGraphsBySlug,
            setMapFilter,
            setTermFilter,
        });
    }
});

function onExportResults(exportRequest: ExportRequest): void {
    void exportResults({ ...getExportPayload(), exportRequest });
}

async function initializeSearch(): Promise<void> {
    try {
        await loadGraphModels();
        search(INITIAL_RESULTS_PAGE);
    } catch (err) {
        console.error("[SimpleSearch] error initializing search:", err);
    }
}

async function loadGraphModels(): Promise<void> {
    try {
        graphModels.value = await getGraphs();
    } catch {
        graphModels.value = [];
    }
}

function onRequestPage(page: number): void {
    search(page);
}

function onSortFieldUpdate(nextField: ResultsSortField | null): void {
    setSort(
        sortSpecForField(nextField, sortDirection.value, activeGraphSlug.value),
    );
}

function onSortDirectionUpdate(nextDirection: ResultsSortDirection): void {
    setSort(
        sortSpecForField(sortField.value, nextDirection, activeGraphSlug.value),
    );
}

function onTimeFilterUpdate(clauses: LiteralClause[]): void {
    const graphSlug = activeGraphSlug.value;
    if (!graphSlug || clauses.length === 0) {
        clearQuery(TIME_FILTER_QUERY_KEY);
        return;
    }

    setQuery(TIME_FILTER_QUERY_KEY, {
        graph_slug: graphSlug,
        scope: GraphScopeToken.RESOURCE,
        logic: LogicToken.OR,
        clauses,
        groups: [],
        aggregations: [],
        relationship: null,
    });
}

function onRemoveTimeFilter(): void {
    closeSidePanel();
    clearQuery(TIME_FILTER_QUERY_KEY);
}

function onMapFilterUpdate(featureCollection: FeatureCollection): void {
    setMapFilter(featureCollection);
}

function onRemoveMapFilter(): void {
    clearMapFilter();
}

function formatTimeFilterLabel(clause: LiteralClause): string {
    const from = parseStoredDate(clause.operands[0]?.value);
    const to = parseStoredDate(clause.operands[1]?.value);

    if (!from || !to) {
        return $gettext("Custom range");
    }

    const fromText = dayjs(from).format("MMM D, YYYY");
    if (dayjs(from).isSame(to, "day")) {
        return fromText;
    }

    return `${fromText} – ${dayjs(to).format("MMM D, YYYY")}`;
}

function openAdvancedSearch(): void {
    void router.push({ name: routeNames.advancedSearch });
}

async function onRunSavedQuery(
    queryDefinition: Record<string, unknown>,
    searchName: string,
): Promise<void> {
    await applySavedSearch(parseSearchDefinition(queryDefinition), searchName);
}

async function applySavedSearch(
    definition: SearchDefinition,
    searchName: string | null,
): Promise<void> {
    try {
        await applySearchDefinition(definition, searchName);
    } catch (error) {
        toast.add({
            severity: "error",
            life: 5000,
            summary: $gettext("The saved search could not be opened."),
            detail: toError(error).message,
        });
    }
}
</script>

<template>
    <div class="simple-search">
        <TermFilter :filter-key="TERM_FILTER_KEY" />

        <ResourceTypeFilter />

        <ActiveFilters
            :active-filters="allActiveFilters"
            @clear-all="clearAll"
        />

        <div class="body">
            <Splitter
                class="splitter"
                @resizestart="onSplitterResizeStart"
                @resize="onSplitterResize"
                @resizeend="onSplitterResizeEnd"
            >
                <SplitterPanel
                    class="results-pane"
                    :size="resultsPanelSize"
                    :min-size="RESULTS_PANEL_MIN_SIZE"
                >
                    <ResultsToolbar
                        :total-results="searchResults.pagination.total_results"
                        :sort-field="sortField"
                        :sort-direction="sortDirection"
                        :sortable-nodes="sortableNodeFilterConfigNodes"
                        :show-filters="isAttributeFiltersOpen"
                        :show-map="isMapFilterOpen"
                        :has-map-filter="mapFilter !== null"
                        :show-time="isTimeFilterOpen"
                        :has-time-filter="hasTimeFilter"
                        :show-saved-searches="isSavedSearchesOpen"
                        :show-export-results="isExportResultsOpen"
                        :hide-filters-button="!isSingleGraphSelected"
                        :hide-time-button="!isSingleGraphSelected"
                        @update:sort-field="onSortFieldUpdate"
                        @update:sort-direction="onSortDirectionUpdate"
                        @toggle-filters="onToggleAttributeFilters"
                        @toggle-map="onToggleMapFilter"
                        @toggle-time="onToggleTimeFilter"
                        @toggle-saved-searches="onToggleSavedSearches"
                        @toggle-export-results="onToggleExportResults"
                    />
                    <SearchResults
                        :results="searchResults"
                        :is-searching="isSearching"
                        :graph-models="graphModels"
                        @request-page="onRequestPage"
                    />
                </SplitterPanel>

                <SplitterPanel
                    class="side-panel"
                    :size="visibleSidePanelSize"
                    :min-size="sidePanelMinSize"
                    :style="sidePanelStyle"
                >
                    <div
                        class="side-panel-content"
                        :class="sidePanelContentClass"
                    >
                        <MapFilterPanel
                            v-show="isMapFilterActive"
                            :model-value="mapFilter"
                            @update:model-value="onMapFilterUpdate"
                            @remove="onRemoveMapFilter"
                            @close="closeSidePanel()"
                        />
                        <RelationshipGraph
                            v-if="isRelatedResourcesOpen"
                            :resources="relatedResources"
                            @remove-resource="removeRelatedResource"
                            @graph-visibility-change="
                                setRelatedResourcesGraphVisible
                            "
                            @close="closeSidePanel()"
                        />
                        <TimeFilter
                            v-else-if="isTimeFilterActive"
                            :graph-slug="activeGraphSlug"
                            :graph-id="activeGraphId"
                            :graph-label="activeGraphLabel"
                            :model-value="timeFilterClauses"
                            @update:model-value="onTimeFilterUpdate"
                            @remove="onRemoveTimeFilter"
                            @close="closeSidePanel()"
                        />
                        <AttributeFilters
                            v-else-if="isAttributeFiltersActive"
                            :nodes="filterableNodeFilterConfigNodes"
                            :values="attributeFilterValues"
                            @update:value="setAttributeFilter"
                            @close="closeSidePanel()"
                        />
                        <SavedSearchPanel
                            v-else-if="isSavedSearchesActive"
                            :definition-to-save="searchDefinition"
                            @run-query="onRunSavedQuery"
                            @close="closeSidePanel()"
                        />
                        <ExportResultsPanel
                            v-else-if="isExportResultsActive"
                            :has-single-graph="isSingleGraphSelected"
                            :export-state="exportState"
                            :result-count="
                                searchResults.pagination.total_results
                            "
                            @export="onExportResults"
                            @close="closeSidePanel()"
                        />
                        <IdleInfoTiles
                            v-else-if="isIdle"
                            :hide-filters="!isSingleGraphSelected"
                            :hide-time="!isSingleGraphSelected"
                            @open-filters="onToggleAttributeFilters"
                            @open-map="onToggleMapFilter"
                            @open-time="onToggleTimeFilter"
                            @open-saved-searches="onToggleSavedSearches"
                            @open-export-results="onToggleExportResults"
                        />
                    </div>
                </SplitterPanel>
            </Splitter>
        </div>
    </div>

    <Toast />
</template>

<style scoped>
.simple-search {
    display: flex;
    flex-direction: column;
    block-size: 100%;
    font-size: var(--p-arches-search-font-size);
}

.simple-search .body {
    display: flex;
    flex: 1;
    min-block-size: 0;
    overflow: hidden;
}

.simple-search .splitter {
    flex: 1;
    min-block-size: 0;
    overflow: hidden;
    border-radius: 0;
}

.simple-search .results-pane {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-inline-size: 0;
    background-color: var(--p-content-background);
}

.simple-search .side-panel {
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.simple-search .side-panel-content {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-inline-size: 20rem;
    overflow-y: auto;
    background-color: var(--arches-search-card-bg);
    opacity: 0;
    translate: 1.25rem 0;
    transition:
        opacity 180ms ease,
        translate 240ms ease;
}

.simple-search .side-panel-content.side-panel-content-open {
    opacity: 1;
    translate: 0 0;
    border-inline-start: 0.1rem solid var(--p-content-border-color);
}

.simple-search .splitter :deep(.p-splitter-gutter) {
    background: var(--p-content-border-color);
    transition: background 0.12s;
}

.simple-search .splitter :deep(.p-splitter-gutter:hover),
.simple-search .splitter :deep(.p-splitter-gutter-handle:hover) {
    background: var(--p-primary-color);
}
</style>
