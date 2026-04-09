<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import ActiveFilters from "@/arches_search/SimpleSearch/components/ActiveFilters.vue";
import AttributeFilters from "@/arches_search/SimpleSearch/components/AttributeFilters.vue";
import ResourceTypeFilter from "@/arches_search/SimpleSearch/components/ResourceTypeFilter.vue";
import ResultsToolbar from "@/arches_search/SimpleSearch/components/ResultsToolbar.vue";
import TermFilter from "@/arches_search/SimpleSearch/components/TermFilter.vue";
import SimpleSearchTimeFilter from "@/arches_search/SimpleSearch/components/SimpleSearchTimeFilter.vue";
import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";

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
const timeFilterClause = ref<LiteralClause | null>(null);

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

const hasTimeFilter = computed<boolean>(() => timeFilterClause.value !== null);

function buildTimeFilterPayload(clause: LiteralClause): GroupPayload | null {
    const slug = activeGraphSlug.value;
    if (!slug) return null;
    return {
        graph_slug: slug,
        scope: GraphScopeToken.RESOURCE,
        logic: LogicToken.AND,
        clauses: [clause],
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

function onTimeFilterUpdate(clause: LiteralClause) {
    timeFilterClause.value = clause;
    const payload = buildTimeFilterPayload(clause);
    if (payload) setQuery("timeFilter", payload);
}

function onRemoveTimeFilter() {
    timeFilterClause.value = null;
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

        <SimpleSearchTimeFilter
            v-if="showTimeFilter"
            :graph-slug="activeGraphSlug"
            :model-value="timeFilterClause"
            @update:model-value="onTimeFilterUpdate"
            @remove="onRemoveTimeFilter"
        />

        <!-- Main content: results + optional filter panel -->
        <div class="simple-search-body">
            <div class="results-pane">
                <SearchResults
                    :results="searchResults"
                    :is-searching="isSearching"
                    :filter-text="''"
                    @request-page="onRequestPage"
                />
            </div>

            <aside
                v-if="showAttributeFilters"
                class="filters-pane"
            >
                <AttributeFilters
                    :sections="attributeFilterSections"
                    :selected-options="selectedFilterOptions"
                    @update:selected-options="selectedFilterOptions = $event"
                />
            </aside>
        </div>
    </div>
</template>

<style scoped>
.simple-search {
    display: flex;
    flex-direction: column;
    height: 100%;
    font-size: var(--p-arches-search-font-size);
}

.simple-search-body {
    display: flex;
    flex: 1;
    overflow: hidden;
}

.results-pane {
    display: flex;
    flex-direction: column;
    flex: 1;
    overflow: hidden;
    background-color: var(--p-content-background);
}

.filters-pane {
    width: 260px;
    flex-shrink: 0;
    border-left: 0.125rem solid var(--p-content-border-color);
    overflow-y: auto;
}
</style>
