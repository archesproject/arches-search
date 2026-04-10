<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import ActiveFilters from "@/arches_search/SimpleSearch/components/ActiveFilters.vue";
import AttributeFilters from "@/arches_search/SimpleSearch/components/AttributeFilters.vue";
import ResourceTypeFilter from "@/arches_search/SimpleSearch/components/ResourceTypeFilter.vue";
import ResultsToolbar from "@/arches_search/SimpleSearch/components/ResultsToolbar.vue";
import TermFilter from "@/arches_search/SimpleSearch/components/TermFilter.vue";
import TimeFilter from "@/arches_search/SimpleSearch/components/TimeFilter/TimeFilter.vue";
import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import { provideSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import { getGraphs } from "@/arches_search/AdvancedSearch/api.ts";
import {
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    GraphModel,
    GroupPayload,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";

import type {
    AttributeFilterSection,
    SortOption,
} from "@/arches_search/SimpleSearch/types.ts";

const { $gettext } = useGettext();

defineEmits<{
    (event: "switch-to-advanced"): void;
}>();

const {
    searchResults,
    isSearching,
    search,
    setQuery,
    clearQuery,
    activeGraph,
} = provideSearchFilters();

const sortValue = ref("aToZ");
const showAttributeFilters = ref(false);
const showTimeFilter = ref(false);
const selectedFilterOptions = ref<Record<string, string[]>>({});
const graphModels = ref<GraphModel[]>([]);
const timeFilterClauses = ref<LiteralClause[]>([]);

const sortOptions: SortOption[] = [
    { label: $gettext("A to Z"), value: "aToZ" },
    { label: $gettext("Z to A"), value: "zToA" },
    { label: $gettext("Newest first"), value: "newest" },
    { label: $gettext("Oldest first"), value: "oldest" },
];

const attributeFilterSections = ref<AttributeFilterSection[]>([
    { id: "color", label: $gettext("Color"), options: [] },
    {
        id: "referenceItemType",
        label: $gettext("Reference Item Type"),
        options: [],
    },
    { id: "mixture", label: $gettext("Mixture"), options: [] },
    { id: "elements", label: $gettext("Elements"), options: [] },
    { id: "chemicalFormula", label: $gettext("Chemical Formula"), options: [] },
    { id: "pigments", label: $gettext("Pigments"), options: [] },
    { id: "itemCategory", label: $gettext("Item Category"), options: [] },
    { id: "materials", label: $gettext("Materials"), options: [] },
]);

const activeGraphSlug = computed<string | null>(() => {
    if (!activeGraph.value) return null;
    const match = graphModels.value.find(
        (g) => g.graphid === activeGraph.value!.id,
    );
    return match?.slug ?? null;
});

const hasTimeFilter = computed<boolean>(
    () => timeFilterClauses.value.length > 0,
);

const TIME_FILTER_SIZE = 40;
const ATTR_FILTER_SIZE = 20;
const FLEX_TRANSITION = "240ms ease";
const BORDER_TRANSITION = "180ms ease";

const resultsPanelSize = computed<number>(() => {
    let size = 100;
    if (showTimeFilter.value) size -= timePanelBasis.value;
    if (showAttributeFilters.value) size -= ATTR_FILTER_SIZE;
    return size;
});

const timePanelBasis = ref<number>(TIME_FILTER_SIZE);
const isSplitterResizing = ref(false);

const visibleTimePanelSize = computed<number>(() =>
    showTimeFilter.value ? timePanelBasis.value : 0,
);

const timePanelStyle = computed(() => ({
    flexGrow: "0",
    flexShrink: "0",
    flexBasis: showTimeFilter.value ? `${timePanelBasis.value}%` : "0px",
    maxWidth: showTimeFilter.value ? `${timePanelBasis.value}%` : "0px",
    minWidth: "0",
    borderInlineStartColor: showTimeFilter.value
        ? "var(--p-content-border-color)"
        : "transparent",
    transition: isSplitterResizing.value
        ? `border-inline-start-color ${BORDER_TRANSITION}`
        : [
              `flex-basis ${FLEX_TRANSITION}`,
              `max-width ${FLEX_TRANSITION}`,
              `border-inline-start-color ${BORDER_TRANSITION}`,
          ].join(", "),
    pointerEvents: showTimeFilter.value ? "auto" : "none",
}));

function syncTimePanelSizeFromEvent(event: { sizes?: number[] }): void {
    const nextTimePanelSize = event.sizes?.[1];

    if (
        showTimeFilter.value &&
        typeof nextTimePanelSize === "number" &&
        nextTimePanelSize > 0
    ) {
        timePanelBasis.value = nextTimePanelSize;
    }
}

function onSplitterResizeStart(): void {
    isSplitterResizing.value = true;
}

function onSplitterResize(event: { sizes?: number[] }): void {
    syncTimePanelSizeFromEvent(event);
}

function onSplitterResizeEnd(event: { sizes?: number[] }): void {
    syncTimePanelSizeFromEvent(event);
    isSplitterResizing.value = false;
}

function buildTimeFilterPayload(clauses: LiteralClause[]): GroupPayload | null {
    const slug = activeGraphSlug.value;
    if (!slug || clauses.length === 0) return null;
    return {
        graph_slug: slug,
        scope: GraphScopeToken.RESOURCE,
        logic: LogicToken.OR,
        clauses,
        groups: [],
        aggregations: [],
        relationship: null,
    };
}

function onRequestPage(page: number) {
    search(page);
}

function onToggleTimeFilter() {
    showTimeFilter.value = !showTimeFilter.value;
}

function onTimeFilterUpdate(clauses: LiteralClause[]) {
    timeFilterClauses.value = clauses;
    const payload = buildTimeFilterPayload(clauses);
    if (payload) setQuery("timeFilter", payload);
    else clearQuery("timeFilter");
}

function onRemoveTimeFilter() {
    timeFilterClauses.value = [];
    showTimeFilter.value = false;
    clearQuery("timeFilter");
}

onMounted(async () => {
    try {
        graphModels.value = await getGraphs();
    } catch {
        // Non-fatal: time filter degrades gracefully without graph models
    }
    search();
});
</script>

<template>
    <div class="simple-search">
        <TermFilter
            :config="{}"
            filter-key="termfilter"
        />

        <ResourceTypeFilter />

        <ActiveFilters />

        <!-- Sort + action buttons -->
        <ResultsToolbar
            :sort-options="sortOptions"
            :sort-value="sortValue"
            :show-filters="showAttributeFilters"
            :show-time="showTimeFilter"
            :has-time-filter="hasTimeFilter"
            @update:sort-value="sortValue = $event"
            @toggle-filters="showAttributeFilters = !showAttributeFilters"
            @toggle-map="() => {}"
            @toggle-time="onToggleTimeFilter"
            @export="() => {}"
        />

        <!-- Main content: results + optional filter panels -->
        <div class="simple-search-body">
            <Splitter
                :key="`splitter-${showAttributeFilters}`"
                :class="[
                    'simple-search-splitter',
                    {
                        'time-filter-open': showTimeFilter,
                        'time-filter-closed': !showTimeFilter,
                    },
                ]"
                @resizestart="onSplitterResizeStart"
                @resize="onSplitterResize"
                @resizeend="onSplitterResizeEnd"
            >
                <SplitterPanel
                    class="results-pane"
                    :size="resultsPanelSize"
                    :min-size="20"
                >
                    <SearchResults
                        :results="searchResults"
                        :is-searching="isSearching"
                        :filter-text="''"
                        @request-page="onRequestPage"
                    />
                </SplitterPanel>

                <SplitterPanel
                    class="time-filter-pane"
                    :size="visibleTimePanelSize"
                    :min-size="showTimeFilter ? 15 : 0"
                    :style="timePanelStyle"
                >
                    <div
                        :class="[
                            'time-filter-panel-inner',
                            { 'time-filter-panel-inner-open': showTimeFilter },
                        ]"
                        :aria-hidden="!showTimeFilter"
                    >
                        <TimeFilter
                            :graph-slug="activeGraphSlug"
                            :graph-id="activeGraph?.id ?? null"
                            :graph-label="activeGraph?.label ?? null"
                            :is-open="showTimeFilter"
                            :model-value="timeFilterClauses[0] ?? null"
                            @update:model-value="onTimeFilterUpdate"
                            @remove="onRemoveTimeFilter"
                        />
                    </div>
                </SplitterPanel>

                <SplitterPanel
                    v-if="showAttributeFilters"
                    class="filters-pane"
                    :size="ATTR_FILTER_SIZE"
                    :min-size="10"
                >
                    <AttributeFilters
                        :sections="attributeFilterSections"
                        :selected-options="selectedFilterOptions"
                        @update:selected-options="
                            selectedFilterOptions = $event
                        "
                    />
                </SplitterPanel>
            </Splitter>
        </div>
    </div>
</template>

<style scoped>
.simple-search {
    --time-filter-inline-offset: 1.25rem;
    display: flex;
    flex-direction: column;
    height: 100%;
    font-size: var(--p-arches-search-font-size);
}

:global([dir="rtl"]) .simple-search {
    --time-filter-inline-offset: -1.25rem;
}

.simple-search-body {
    display: flex;
    flex: 1;
    overflow: hidden;
}

.simple-search-splitter {
    flex: 1;
    overflow: hidden;
    border-radius: 0;
}

.results-pane {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background-color: var(--p-content-background);
    min-width: 0;
}

.time-filter-pane {
    overflow: hidden;
    border-inline-start: 0.0625rem solid var(--p-content-border-color);
}

.filters-pane {
    overflow-y: auto;
}

.time-filter-panel-inner {
    height: 100%;
    overflow-y: auto;
    opacity: 0;
    translate: var(--time-filter-inline-offset) 0;
    transition:
        opacity 180ms ease,
        translate 240ms ease;
}

.time-filter-panel-inner-open {
    opacity: 1;
    translate: 0 0;
}

.simple-search-splitter.time-filter-closed
    :deep(.results-pane + .p-splitter-gutter) {
    display: none;
}
</style>
