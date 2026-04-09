<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Toast from "primevue/toast";
import { useToast } from "primevue/usetoast";

import ActiveFilters from "@/arches_search/SimpleSearch/components/ActiveFilters.vue";
import AttributeFilters from "@/arches_search/SimpleSearch/components/AttributeFilters.vue";
import ResourceTypeFilter from "@/arches_search/SimpleSearch/components/ResourceTypeFilter.vue";
import ResultsToolbar from "@/arches_search/SimpleSearch/components/ResultsToolbar.vue";
import SearchBar from "@/arches_search/SimpleSearch/components/SearchBar.vue";
import SimpleSearchTimeFilter from "@/arches_search/SimpleSearch/components/SimpleSearchTimeFilter.vue";
import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";

import { fetchSimpleSearchResults } from "@/arches_search/SimpleSearch/api.ts";
import {
    getGraphs,
    getSearchResults,
} from "@/arches_search/AdvancedSearch/api.ts";

import type {
    ActiveFilter,
    AttributeFilterSection,
    ResourceType,
    SortOption,
} from "@/arches_search/SimpleSearch/types.ts";
import {
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    GroupPayload,
    LiteralClause,
    GraphModel,
    SearchResults as SearchResultsType,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();
const toast = useToast();

defineEmits<{
    (event: "switch-to-advanced"): void;
}>();

const searchText = ref("");
const activeTypeId = ref<string | null>(null);
const activeFilters = ref<ActiveFilter[]>([]);
const sortValue = ref("aToZ");
const showAttributeFilters = ref(false);
const showTimeFilter = ref(false);
const isSearching = ref(false);
const currentPage = ref(1);
const selectedFilterOptions = ref<Record<string, string[]>>({});
const graphModels = ref<GraphModel[]>([]);
const resourceTypes = ref<ResourceType[]>([]);
const timeFilterClause = ref<LiteralClause | null>(null);

const emptyResults: SearchResultsType = {
    resources: [],
    aggregations: {},
    pagination: {
        page: 1,
        page_size: 25,
        total_results: 0,
        total_pages: 0,
        has_next: false,
        has_previous: false,
    },
};
const searchResults = ref<SearchResultsType>({ ...emptyResults });

const sortOptions: SortOption[] = [
    { label: $gettext("A to Z"), value: "aToZ" },
    { label: $gettext("Z to A"), value: "zToA" },
    { label: $gettext("Newest first"), value: "newest" },
    { label: $gettext("Oldest first"), value: "oldest" },
];

/**
 * Attribute filter sections are populated from search aggregations in practice.
 * These defaults show the panel structure; options are filled in after a search.
 */
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

const activeTypeLabel = computed<string>(() => {
    if (!activeTypeId.value) return $gettext("Items");
    const match = resourceTypes.value.find(
        (resourceType) => resourceType.id === activeTypeId.value,
    );
    return match ? match.label : $gettext("Items");
});

const activeGraphSlug = computed<string | null>(() => {
    if (!activeTypeId.value) {
        return null;
    }

    const matchingGraph = graphModels.value.find((graphModel) => {
        return graphModel.graphid === activeTypeId.value;
    });

    return matchingGraph?.slug ?? null;
});

const hasTimeFilter = computed<boolean>(() => {
    return timeFilterClause.value !== null;
});

function buildGroupPayload(): GroupPayload | null {
    const slug = activeGraphSlug.value;
    if (!slug) return null;

    const groups: GroupPayload[] = [];

    if (timeFilterClause.value) {
        groups.push({
            graph_slug: slug,
            scope: GraphScopeToken.RESOURCE,
            logic: LogicToken.AND,
            clauses: [timeFilterClause.value],
            groups: [],
            aggregations: [],
            relationship: null,
        });
    }

    return {
        graph_slug: slug,
        scope: GraphScopeToken.RESOURCE,
        logic: LogicToken.AND,
        clauses: [],
        groups,
        aggregations: [],
        relationship: null,
    };
}

async function performSearch() {
    isSearching.value = true;
    try {
        const payload = buildGroupPayload();

        if (payload) {
            const raw = await getSearchResults(payload, {
                page: currentPage.value,
            });
            searchResults.value = {
                resources: raw.resources ?? [],
                aggregations: raw.aggregations ?? {},
                pagination: {
                    page: raw.pagination.page,
                    page_size: raw.pagination.page_size,
                    total_results: raw.pagination.total_results,
                    total_pages: raw.pagination.num_pages ?? 1,
                    has_next: raw.pagination.has_next,
                    has_previous: raw.pagination.has_previous,
                },
            };
        } else {
            const terms = activeFilters.value.map((filter: ActiveFilter) => ({
                type: "term" as const,
                value: filter.id,
                text: filter.label,
                inverted: false,
            }));
            searchResults.value = await fetchSimpleSearchResults({
                terms,
                graphId: activeTypeId.value,
                page: currentPage.value,
            });
        }
    } catch (error) {
        toast.add({
            severity: "error",
            life: 5000,
            summary: $gettext("Search failed"),
            detail: error instanceof Error ? error.message : undefined,
        });
    } finally {
        isSearching.value = false;
    }
}

function onSearch(term: string) {
    const trimmed = term.trim();
    if (
        !trimmed ||
        activeFilters.value.some(
            (filter: ActiveFilter) => filter.id === trimmed,
        )
    ) {
        performSearch();
        return;
    }

    activeFilters.value.push({
        id: trimmed,
        label: trimmed,
        clear: () => removeFilter(trimmed),
    });

    currentPage.value = 1;
    performSearch();
}

function removeFilter(filterId: string) {
    activeFilters.value = activeFilters.value.filter(
        (filter: ActiveFilter) => filter.id !== filterId,
    );
    if (searchText.value === filterId) searchText.value = "";
    currentPage.value = 1;
    performSearch();
}

function clearAllFilters() {
    activeFilters.value = [];
    searchText.value = "";
    currentPage.value = 1;
    selectedFilterOptions.value = {};
    timeFilterClause.value = null;
    showTimeFilter.value = false;
    performSearch();
}

function onSelectResourceType(typeId: string | null) {
    activeTypeId.value = typeId;
    if (timeFilterClause.value && typeId) {
        const matchingGraph = graphModels.value.find((graphModel) => {
            return graphModel.graphid === typeId;
        });

        if (matchingGraph) {
            timeFilterClause.value = {
                ...timeFilterClause.value,
                subject: {
                    ...timeFilterClause.value.subject,
                    graph_slug: matchingGraph.slug,
                },
            };
        }
    }

    if (typeId === null) {
        timeFilterClause.value = null;
    }
    currentPage.value = 1;
    performSearch();
}

function onRequestPage(page: number) {
    currentPage.value = page;
    performSearch();
}

async function loadResourceTypes() {
    try {
        graphModels.value = await getGraphs();
        resourceTypes.value = graphModels.value
            .filter((g) => g.isresource && g.is_active)
            .map((g) => ({
                id: g.graphid,
                label: g.name,
                icon: g.iconclass || "fa fa-archive",
            }));
    } catch {
        // Non-fatal: page still works without type tabs
    }
}

function onToggleTimeFilter() {
    showTimeFilter.value = !showTimeFilter.value;
}

function onTimeFilterUpdate(clause: LiteralClause) {
    timeFilterClause.value = clause;
    performSearch();
}

function onRemoveTimeFilter() {
    timeFilterClause.value = null;
    showTimeFilter.value = false;
    performSearch();
}

onMounted(async () => {
    await loadResourceTypes();
    performSearch();
});
</script>

<template>
    <div class="simple-search">
        <!-- Search input -->
        <SearchBar
            v-model="searchText"
            @search="onSearch"
        />

        <!-- Resource type tabs -->
        <ResourceTypeFilter
            :resource-types="resourceTypes"
            :active-type-id="activeTypeId"
            @select="onSelectResourceType"
        />

        <!-- Active filter chips + result count -->
        <ActiveFilters
            :count="searchResults.pagination.total_results"
            :resource-type-label="activeTypeLabel"
            :filters="activeFilters"
            @clear-all="clearAllFilters"
        />

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

    <Toast />
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
