<script setup lang="ts">
import { computed, ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";
import { useToast } from "primevue/usetoast";
import Toast from "primevue/toast";

import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";
import ActiveFilters from "@/arches_search/SimpleSearch/components/ActiveFilters.vue";
import AttributeFilters from "@/arches_search/SimpleSearch/components/attribute-filters/AttributeFilters.vue";
import ExportPanel from "@/arches_search/SimpleSearch/components/ExportPanel.vue";
import ResourceTypeFilter from "@/arches_search/SimpleSearch/components/ResourceTypeFilter.vue";
import ResultsToolbar from "@/arches_search/SimpleSearch/components/ResultsToolbar.vue";
import SavedSearchPanel from "@/arches_search/SimpleSearch/components/SavedSearchPanel.vue";
import SaveDialog from "@/arches_search/SimpleSearch/components/SaveDialog.vue";
import TermFilter from "@/arches_search/SimpleSearch/components/TermFilter.vue";
import MapFilterPanel from "@/arches_search/SimpleSearch/components/MapFilterPanel.vue";
import TimeFilter from "@/arches_search/SimpleSearch/components/TimeFilter/TimeFilter.vue";

import { getGraphs } from "@/arches_search/AdvancedSearch/api.ts";
import {
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import {
    createSavedSearch,
    fetchNodeFilterConfig,
} from "@/arches_search/SimpleSearch/api.ts";
import { buildAttributeFilterQuery } from "@/arches_search/SimpleSearch/components/attribute-filters/registry.ts";
import { provideSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import { useSidePanel } from "@/arches_search/SimpleSearch/composables/useSidePanel.ts";

import type { FeatureCollection } from "geojson";
import type {
    GraphModel,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    NodeFilterConfigNode,
    SearchDefinition,
    SortSpec,
} from "@/arches_search/SimpleSearch/types.ts";

const TERM_FILTER_KEY = "termfilter";
const TIME_FILTER_QUERY_KEY = "timeFilter";
const INITIAL_RESULTS_PAGE = 1;
const RESULTS_PANEL_MIN_SIZE = 20;

const {
    activeGraph,
    applySearchDefinition,
    clearMapFilter,
    clearQuery,
    getSearchDefinition,
    isSearching,
    mapFilter,
    queries,
    search,
    searchResults,
    setMapFilter,
    setQuery,
    setSort,
} = provideSearchFilters();

const {
    isAttributeFiltersActive,
    isAttributeFiltersOpen,
    isMapFilterActive,
    isMapFilterOpen,
    isExportPanelActive,
    isExportPanelOpen,
    isSavedSearchesActive,
    isSavedSearchesOpen,
    isTimeFilterActive,
    isTimeFilterOpen,
    hasOpenSidePanel,
    resultsPanelSize,
    visibleSidePanelSize,
    sidePanelMinSize,
    splitterStateClass,
    sidePanelContentClass,
    sidePanelStyle,
    closeSidePanel,
    onToggleAttributeFilters,
    onToggleMapFilter,
    onToggleExportPanel,
    onToggleSavedSearches,
    onToggleTimeFilter,
    onSplitterResizeStart,
    onSplitterResize,
    onSplitterResizeEnd,
} = useSidePanel();

const { $gettext } = useGettext();
const toast = useToast();
const sortValue = ref<string | null>(null);
const graphModels = ref<GraphModel[]>([]);
const showSaveDialog = ref(false);
const filterValues = ref<Record<string, unknown>>({});
const savedSearchPanelRef = ref<InstanceType<typeof SavedSearchPanel> | null>(
    null,
);

const activeGraphId = computed<string | null>(
    () => activeGraph.value?.id ?? null,
);

const activeGraphLabel = computed<string | null>(
    () => activeGraph.value?.label ?? null,
);

const nodeFilterConfigNodes = ref<NodeFilterConfigNode[]>([]);

watch(
    () => activeGraph.value,
    (graph) => {
        // Drop any attribute-filter queries from the previously active graph.
        for (const node of nodeFilterConfigNodes.value) {
            clearQuery(node.node_alias);
        }
        filterValues.value = {};

        if (!graph || !graph.id) {
            nodeFilterConfigNodes.value = [];

            if (isTimeFilterOpen.value || isAttributeFiltersOpen.value) {
                closeSidePanel();
            }

            return;
        }

        void loadNodeFilterConfig(graph.id);
    },
);

async function loadNodeFilterConfig(graphId: string): Promise<void> {
    try {
        const config = await fetchNodeFilterConfig(graphId);
        nodeFilterConfigNodes.value = config.nodes;
    } catch (err) {
        console.error("[SimpleSearch] error loading filter config:", err);
        nodeFilterConfigNodes.value = [];
    }
}

// Each attribute-filter widget emits a datatype-specific value; the registry
// turns it into a query (or null to clear). Query-shape logic lives in the
// per-datatype builders, so this handler stays datatype-agnostic.
function onAttributeFilterChange(nodeAlias: string, value: unknown): void {
    filterValues.value = { ...filterValues.value, [nodeAlias]: value };

    const node = nodeFilterConfigNodes.value.find(
        (candidate) => candidate.node_alias === nodeAlias,
    );
    const graphSlug = activeGraphSlug.value;
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

const activeGraphSlug = computed<string | null>(() => {
    if (!activeGraphId.value) {
        return null;
    }

    const matchingGraph = graphModels.value.find((graphModel) => {
        return graphModel.graphid === activeGraphId.value;
    });

    return matchingGraph?.slug ?? null;
});

const timeFilterQuery = computed(
    () => queries.value.get(TIME_FILTER_QUERY_KEY) ?? null,
);

const hasTimeFilter = computed<boolean>(
    () => (timeFilterQuery.value?.clauses.length ?? 0) > 0,
);

const selectedTimeFilterClause = computed<LiteralClause | null>(
    () => timeFilterQuery.value?.clauses[0] ?? null,
);

watchEffect(() => {
    void initializeSearch();
});

async function initializeSearch(): Promise<void> {
    await loadGraphModels();
    search(INITIAL_RESULTS_PAGE);
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

function onSortValueUpdate(nextSortValue: string | null): void {
    sortValue.value = nextSortValue;
    setSort(sortSpecForValue(nextSortValue));
}

function sortSpecForValue(value: string | null): SortSpec[] {
    switch (value) {
        case "aToZ":
            return [{ type: "primary_name", direction: "asc" }];
        case "zToA":
            return [{ type: "primary_name", direction: "desc" }];
        default:
            return [];
    }
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

async function onSaveSearch(payload: { name: string; description: string }) {
    try {
        await createSavedSearch(
            payload.name,
            payload.description,
            getSearchDefinition() as unknown as Record<string, unknown>,
        );
        showSaveDialog.value = false;
        savedSearchPanelRef.value?.loadSearches();
        toast.add({
            severity: "success",
            life: 3000,
            summary: $gettext("Search saved"),
        });
    } catch (error) {
        toast.add({
            severity: "error",
            life: 5000,
            summary: $gettext("Failed to save search"),
            detail: error instanceof Error ? error.message : undefined,
        });
    }
}

function onRunSavedQuery(queryDefinition: Record<string, unknown>) {
    applySearchDefinition(parseSearchDefinition(queryDefinition));
    filterValues.value = {};
}

// Tolerant parser so older saved rows (which only stored `terms` + `graphId`)
// load cleanly. New code always writes the full SearchDefinition shape.
function parseSearchDefinition(raw: Record<string, unknown>): SearchDefinition {
    const rawTerms = Array.isArray(raw.terms) ? raw.terms : [];
    const terms = rawTerms.flatMap((t) => {
        if (!t || typeof t !== "object") return [];
        const term = t as Record<string, unknown>;
        // Legacy rows used `value` for the id; new rows use `id`.
        const id =
            typeof term.id === "string"
                ? term.id
                : typeof term.value === "string"
                  ? term.value
                  : null;
        const text = typeof term.text === "string" ? term.text : null;
        if (!id || text === null) return [];
        return [
            {
                id,
                text,
                inverted: term.inverted === true,
                ...(term.options && typeof term.options === "object"
                    ? { options: term.options as Record<string, unknown> }
                    : {}),
            },
        ];
    });

    const queriesIn =
        raw.queries && typeof raw.queries === "object"
            ? (raw.queries as SearchDefinition["queries"])
            : {};

    return {
        version: 1,
        terms,
        queries: queriesIn,
        graphId: typeof raw.graphId === "string" ? raw.graphId : null,
    };
}
</script>

<template>
    <div class="simple-search">
        <TermFilter :filter-key="TERM_FILTER_KEY" />

        <ResourceTypeFilter />

        <ActiveFilters />

        <ResultsToolbar
            :sort-value="sortValue"
            :show-filters="isAttributeFiltersOpen"
            :show-map="isMapFilterOpen"
            :has-map-filter="mapFilter !== null"
            :show-time="isTimeFilterOpen"
            :has-time-filter="hasTimeFilter"
            :show-saved-searches="isSavedSearchesOpen"
            :show-export-panel="isExportPanelOpen"
            :hide-filters-button="!activeGraph"
            :hide-time-button="!activeGraph"
            @update:sort-value="onSortValueUpdate"
            @save-search="showSaveDialog = true"
            @toggle-filters="onToggleAttributeFilters"
            @toggle-map="onToggleMapFilter"
            @toggle-time="onToggleTimeFilter"
            @toggle-saved-searches="onToggleSavedSearches"
            @export="onToggleExportPanel"
        />

        <div class="body">
            <Splitter
                class="splitter"
                :class="splitterStateClass"
                @resizestart="onSplitterResizeStart"
                @resize="onSplitterResize"
                @resizeend="onSplitterResizeEnd"
            >
                <SplitterPanel
                    class="results-pane"
                    :size="resultsPanelSize"
                    :min-size="RESULTS_PANEL_MIN_SIZE"
                >
                    <SearchResults
                        :results="searchResults"
                        :is-searching="isSearching"
                        :filter-text="''"
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
                        :aria-hidden="!hasOpenSidePanel"
                    >
                        <MapFilterPanel
                            v-show="isMapFilterActive"
                            :model-value="mapFilter"
                            @update:model-value="onMapFilterUpdate"
                            @remove="onRemoveMapFilter"
                        />
                        <TimeFilter
                            v-if="isTimeFilterActive"
                            :graph-slug="activeGraphSlug"
                            :graph-id="activeGraphId"
                            :graph-label="activeGraphLabel"
                            :model-value="selectedTimeFilterClause"
                            @update:model-value="onTimeFilterUpdate"
                            @remove="onRemoveTimeFilter"
                        />
                        <AttributeFilters
                            v-else-if="isAttributeFiltersActive"
                            :nodes="nodeFilterConfigNodes"
                            :values="filterValues"
                            @update:value="onAttributeFilterChange"
                        />
                        <SavedSearchPanel
                            v-else-if="isSavedSearchesActive"
                            ref="savedSearchPanelRef"
                            @run-query="onRunSavedQuery"
                        />
                        <ExportPanel v-else-if="isExportPanelActive" />
                    </div>
                </SplitterPanel>
            </Splitter>
        </div>
    </div>

    <SaveDialog
        v-model:visible="showSaveDialog"
        @save="onSaveSearch"
    />

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
    overflow: hidden;
}

.simple-search .splitter {
    flex: 1;
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
    border-inline-start: 0.0625rem solid var(--p-content-border-color);
}

.simple-search .side-panel-content {
    display: flex;
    flex-direction: column;
    flex: 1;
    overflow-y: auto;
    opacity: 0;
    translate: 1.25rem 0;
    transition:
        opacity 180ms ease,
        translate 240ms ease;
}

.simple-search .side-panel-content.side-panel-content-open {
    opacity: 1;
    translate: 0 0;
}

.simple-search
    .splitter.side-panel-closed
    :deep(.results-pane + .p-splitter-gutter) {
    display: none;
}
</style>
