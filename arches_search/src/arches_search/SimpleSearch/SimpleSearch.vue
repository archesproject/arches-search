<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";

import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";
import ActiveFilters from "@/arches_search/SimpleSearch/components/ActiveFilters.vue";
import AttributeFilters from "@/arches_search/SimpleSearch/components/AttributeFilters.vue";
import ResourceTypeFilter from "@/arches_search/SimpleSearch/components/ResourceTypeFilter.vue";
import ResultsToolbar from "@/arches_search/SimpleSearch/components/ResultsToolbar.vue";
import TermFilter from "@/arches_search/SimpleSearch/components/TermFilter.vue";
import TimeFilter from "@/arches_search/SimpleSearch/components/TimeFilter/TimeFilter.vue";

import { getGraphs } from "@/arches_search/AdvancedSearch/api.ts";
import {
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import { provideSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import { useSidePanel } from "@/arches_search/SimpleSearch/composables/useSidePanel.ts";

import type {
    GraphModel,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";
const SWITCH_TO_ADVANCED_EVENT = "switch-to-advanced" as const;
const TERM_FILTER_KEY = "termfilter" as const;
const TIME_FILTER_QUERY_KEY = "timeFilter" as const;
const TERM_FILTER_CONFIG: Record<string, never> = {};
const INITIAL_RESULTS_PAGE = 1;
const RESULTS_PANEL_MIN_SIZE = 20;

defineEmits<{
    (event: typeof SWITCH_TO_ADVANCED_EVENT): void;
}>();

const {
    activeGraph,
    clearQuery,
    isSearching,
    search,
    searchResults,
    setQuery,
} = provideSearchFilters();

const {
    isAttributeFiltersActive,
    isAttributeFiltersOpen,
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
    onToggleTimeFilter,
    onSplitterResizeStart,
    onSplitterResize,
    onSplitterResizeEnd,
} = useSidePanel();

const sortValue = ref("aToZ");
const graphModels = ref<GraphModel[]>([]);
const timeFilterClauses = ref<LiteralClause[]>([]);
const selectedFilterOptions = ref<Record<string, string[]>>({});

const activeGraphId = computed<string | null>(
    () => activeGraph.value?.id ?? null,
);

const activeGraphLabel = computed<string | null>(
    () => activeGraph.value?.label ?? null,
);

const activeGraphSlug = computed<string | null>(() => {
    if (!activeGraphId.value) {
        return null;
    }

    const matchingGraph = graphModels.value.find((graphModel) => {
        return graphModel.graphid === activeGraphId.value;
    });

    return matchingGraph?.slug ?? null;
});

const hasTimeFilter = computed<boolean>(
    () => timeFilterClauses.value.length > 0,
);

const selectedTimeFilterClause = computed<LiteralClause | null>(() => {
    return timeFilterClauses.value[0] ?? null;
});

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
        // Non-fatal: time filter degrades gracefully without graph models.
    }
}

function onRequestPage(page: number): void {
    search(page);
}

function onSelectedOptionsUpdate(
    nextSelectedFilterOptions: Record<string, string[]>,
): void {
    selectedFilterOptions.value = nextSelectedFilterOptions;
}

function onSortValueUpdate(nextSortValue: string): void {
    sortValue.value = nextSortValue;
}

function onTimeFilterUpdate(clauses: LiteralClause[]): void {
    timeFilterClauses.value = clauses;

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
    timeFilterClauses.value = [];
    closeSidePanel();
    clearQuery(TIME_FILTER_QUERY_KEY);
}
</script>

<template>
    <div class="simple-search">
        <TermFilter
            :filter-key="TERM_FILTER_KEY"
            :config="TERM_FILTER_CONFIG"
        />

        <ResourceTypeFilter />

        <ActiveFilters />

        <ResultsToolbar
            :sort-value="sortValue"
            :show-filters="isAttributeFiltersOpen"
            :show-time="isTimeFilterOpen"
            :has-time-filter="hasTimeFilter"
            @update:sort-value="onSortValueUpdate"
            @toggle-filters="onToggleAttributeFilters"
            @toggle-time="onToggleTimeFilter"
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
                        <TimeFilter
                            v-if="isTimeFilterActive"
                            :graph-slug="activeGraphSlug"
                            :graph-id="activeGraphId"
                            :graph-label="activeGraphLabel"
                            :is-open="isTimeFilterOpen"
                            :model-value="selectedTimeFilterClause"
                            @update:model-value="onTimeFilterUpdate"
                            @remove="onRemoveTimeFilter"
                        />
                        <AttributeFilters
                            v-else-if="isAttributeFiltersActive"
                            :selected-options="selectedFilterOptions"
                            @update:selected-options="onSelectedOptionsUpdate"
                        />
                    </div>
                </SplitterPanel>
            </Splitter>
        </div>
    </div>
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
    overflow: hidden;
    border-inline-start: 0.0625rem solid var(--p-content-border-color);
}

.simple-search .side-panel-content {
    block-size: 100%;
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
