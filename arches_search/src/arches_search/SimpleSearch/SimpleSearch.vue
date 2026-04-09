<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";
import { useToast } from "primevue/usetoast";
import Toast from "primevue/toast";

import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";
import ActiveFilters from "@/arches_search/SimpleSearch/components/ActiveFilters.vue";
import AttributeFilters from "@/arches_search/SimpleSearch/components/AttributeFilters.vue";
import ResourceTypeFilter from "@/arches_search/SimpleSearch/components/ResourceTypeFilter.vue";
import ResultsToolbar from "@/arches_search/SimpleSearch/components/ResultsToolbar.vue";
import SavedSearchPanel from "@/arches_search/SimpleSearch/components/SavedSearchPanel.vue";
import SaveDialog from "@/arches_search/SimpleSearch/components/SaveDialog.vue";
import TermFilter from "@/arches_search/SimpleSearch/components/TermFilter.vue";
import TimeFilter from "@/arches_search/SimpleSearch/components/TimeFilter/TimeFilter.vue";

import { getGraphs } from "@/arches_search/AdvancedSearch/api.ts";
import {
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import { createSavedSearch } from "@/arches_search/SimpleSearch/api.ts";
import { provideSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import { useSidePanel } from "@/arches_search/SimpleSearch/composables/useSidePanel.ts";

import type {
    GraphModel,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";

const SWITCH_TO_ADVANCED_EVENT = "switch-to-advanced";
const TERM_FILTER_KEY = "termfilter";
const TIME_FILTER_QUERY_KEY = "timeFilter";
const INITIAL_RESULTS_PAGE = 1;
const RESULTS_PANEL_MIN_SIZE = 20;

defineEmits<{
    (event: typeof SWITCH_TO_ADVANCED_EVENT): void;
}>();

const {
    activeFilters,
    activeGraph,
    clearQuery,
    clearTermFilter,
    isSearching,
    search,
    searchResults,
    setGraph,
    setQuery,
    setTermFilter,
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

const { $gettext } = useGettext();
const toast = useToast();
const sortValue = ref("aToZ");
const graphModels = ref<GraphModel[]>([]);
const timeFilterClauses = ref<LiteralClause[]>([]);
const showSavedSearches = ref(false);
const showSaveDialog = ref(false);
const selectedFilterOptions = ref<Record<string, string[]>>({});
const savedSearchPanelRef = ref<InstanceType<typeof SavedSearchPanel> | null>(
    null,
);

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

// ── Saved searches ──────────────────────────────────────────────────────────
function buildQueryDefinition(): Record<string, unknown> {
    const terms = activeFilters.value.map((filter) => ({
        type: "term",
        value: filter.id,
        text: filter.text,
        inverted: false,
    }));
    return {
        terms,
        graphId: activeGraph.value?.id ?? null,
    };
}

async function onSaveSearch(payload: { name: string; description: string }) {
    try {
        await createSavedSearch(
            payload.name,
            payload.description,
            buildQueryDefinition(),
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
    const terms =
        (queryDefinition.terms as Array<{
            type: string;
            value: string;
            text: string;
            inverted: boolean;
        }>) || [];
    const graphId = (queryDefinition.graphId as string | null) ?? null;

    // Clear existing search before applying saved query
    activeFilters.value.forEach((f) => clearTermFilter(f.id));

    terms.forEach((t) => {
        setTermFilter(t.value, t.text, () => clearTermFilter(t.value));
    });
    if (graphId) {
        setGraph({ id: graphId, label: "", icon: "" });
    } else {
        setGraph(null);
    }
    selectedFilterOptions.value = {};
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
            :show-time="isTimeFilterOpen"
            :has-time-filter="hasTimeFilter"
            :show-saved-searches="showSavedSearches"
            @update:sort-value="onSortValueUpdate"
            @save-search="showSaveDialog = true"
            @toggle-filters="onToggleAttributeFilters"
            @toggle-map="() => {}"
            @toggle-time="onToggleTimeFilter"
            @toggle-saved-searches="showSavedSearches = !showSavedSearches"
            @export="() => {}"
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

            <aside
                v-if="showSavedSearches"
                class="saved-searches-pane"
            >
                <SavedSearchPanel
                    ref="savedSearchPanelRef"
                    @run-query="onRunSavedQuery"
                />
            </aside>
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

.saved-searches-pane {
    width: 320px;
    flex-shrink: 0;
    border-left: 0.125rem solid var(--p-content-border-color);
    overflow-y: auto;
}
</style>
