<script setup lang="ts">
import { computed, ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";
import { useToast } from "primevue/usetoast";
import Toast from "primevue/toast";

import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";
import ActiveFilters from "@/arches_search/SimpleSearch/components/ActiveFilters.vue";
import AttributeFilters from "@/arches_search/SimpleSearch/components/AttributeFilters.vue";
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
    ClauseSubjectTypeToken,
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import {
    createSavedSearch,
    fetchNodeFilterConfig,
    fetchControlledListItems,
} from "@/arches_search/SimpleSearch/api.ts";
import { provideSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import { useSidePanel } from "@/arches_search/SimpleSearch/composables/useSidePanel.ts";

import type { FeatureCollection } from "geojson";
import type {
    GraphModel,
    GroupPayload,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    AttributeFilterSection,
    NodeFilterConfigNode,
    SearchDefinition,
    SortSpec,
} from "@/arches_search/SimpleSearch/types.ts";

const SWITCH_TO_ADVANCED_EVENT = "switch-to-advanced";
const TERM_FILTER_KEY = "termfilter";
const TIME_FILTER_QUERY_KEY = "timeFilter";
const INITIAL_RESULTS_PAGE = 1;
const RESULTS_PANEL_MIN_SIZE = 20;

defineEmits<{
    (event: typeof SWITCH_TO_ADVANCED_EVENT): void;
}>();

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
const timeFilterClauses = ref<LiteralClause[]>([]);
const showSavedSearches = ref(false);
const showExportPanel = ref(false);
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

const attributeFilterSections = ref<AttributeFilterSection[]>([]);
const nodeFilterConfigNodes = ref<NodeFilterConfigNode[]>([]);

watch(
    () => activeGraph.value,
    async (graph) => {
        if (!graph || !graph.id) {
            attributeFilterSections.value = [];
            nodeFilterConfigNodes.value = [];
            return;
        }
        try {
            const config = await fetchNodeFilterConfig(graph.id);
            nodeFilterConfigNodes.value = config.nodes;
            attributeFilterSections.value = config.nodes.map((node) => ({
                id: node.node_alias,
                label: node.label,
                options: [],
            }));

            // Populate options from controlled lists for reference nodes
            const sections = [...attributeFilterSections.value];
            await Promise.all(
                config.nodes.map(async (node, index) => {
                    if (
                        node.datatype !== "reference" ||
                        !node.config?.controlledList
                    ) {
                        return;
                    }
                    const items = await fetchControlledListItems(
                        node.config.controlledList as string,
                    );
                    sections[index] = {
                        ...sections[index],
                        options: items.map((item) => ({
                            id: item.uri,
                            label: item.label,
                        })),
                    };
                }),
            );
            attributeFilterSections.value = sections;
        } catch (err) {
            console.error("[SimpleSearch] error loading filter config:", err);
            attributeFilterSections.value = [];
            nodeFilterConfigNodes.value = [];
        }
    },
);

function onFilterOptionsChanged(selected: Record<string, string[]>) {
    selectedFilterOptions.value = selected;

    // Clear all existing attribute filter queries
    for (const node of nodeFilterConfigNodes.value) {
        clearQuery(node.node_alias);
    }

    // Set a query for each section that has selections
    for (const [nodeAlias, values] of Object.entries(selected)) {
        if (values.length === 0) continue;

        const section = attributeFilterSections.value.find(
            (s) => s.id === nodeAlias,
        );
        const resolvedValues = values.map((val) => {
            const opt = section?.options.find((o) => o.id === val);
            return opt?.label ?? val;
        });

        const query: GroupPayload = {
            graph_slug: activeGraphSlug.value!,
            scope: GraphScopeToken.RESOURCE,
            logic: LogicToken.AND,
            clauses: [
                {
                    type: "LITERAL" as const,
                    quantifier: "ANY" as const,
                    subject: {
                        type: ClauseSubjectTypeToken.NODE,
                        graph_slug: activeGraphSlug.value!,
                        node_alias: nodeAlias,
                        search_models: [],
                    },
                    operator: "REFERENCES_ANY",
                    operands: [
                        { type: "LITERAL" as const, value: resolvedValues },
                    ],
                },
            ],
            groups: [],
            aggregations: [],
            relationship: null,
        };

        setQuery(nodeAlias, query);
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
    selectedFilterOptions.value = {};
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
            @update:sort-value="onSortValueUpdate"
            @save-search="showSaveDialog = true"
            @toggle-filters="onToggleAttributeFilters"
            @toggle-map="onToggleMapFilter"
            @toggle-time="onToggleTimeFilter"
            @toggle-saved-searches="showSavedSearches = !showSavedSearches"
            @export="showExportPanel = !showExportPanel"
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
                            :is-open="isTimeFilterOpen"
                            :model-value="selectedTimeFilterClause"
                            @update:model-value="onTimeFilterUpdate"
                            @remove="onRemoveTimeFilter"
                        />
                        <AttributeFilters
                            v-else-if="isAttributeFiltersActive"
                            :sections="attributeFilterSections"
                            :selected-options="selectedFilterOptions"
                            @update:selected-options="onFilterOptionsChanged"
                        />
                        <SavedSearchPanel
                            v-else-if="isSavedSearchesActive"
                            ref="savedSearchPanelRef"
                            @run-query="onRunSavedQuery"
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

            <aside
                v-if="showExportPanel"
                class="export-pane"
            >
                <ExportPanel />
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

.saved-searches-pane {
    width: 20rem;
    flex-shrink: 0;
    border-left: 0.125rem solid var(--p-content-border-color);
    overflow-y: auto;
}

.export-pane {
    width: 20rem;
    flex-shrink: 0;
    border-left: 0.125rem solid var(--p-content-border-color);
    overflow-y: auto;
}
</style>
