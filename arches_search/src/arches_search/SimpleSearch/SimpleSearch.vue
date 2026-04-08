<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import ActiveFilters from "@/arches_search/SimpleSearch/components/ActiveFilters.vue";
import AttributeFilters from "@/arches_search/SimpleSearch/components/AttributeFilters.vue";
import ResourceTypeFilter from "@/arches_search/SimpleSearch/components/ResourceTypeFilter.vue";
import ResultsToolbar from "@/arches_search/SimpleSearch/components/ResultsToolbar.vue";
import TermFilter from "@/arches_search/SimpleSearch/components/TermFilter.vue";
import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";

import { provideSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type {
    AttributeFilterSection,
    SortOption,
} from "@/arches_search/SimpleSearch/types.ts";

const { $gettext } = useGettext();

defineEmits<{
    (event: "switch-to-advanced"): void;
}>();

const { searchResults, isSearching, search } = provideSearchFilters();

const activeTypeId = ref<string | null>(null);
const sortValue = ref("aToZ");
const showAttributeFilters = ref(false);
const selectedFilterOptions = ref<Record<string, string[]>>({});

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

function onRequestPage(page: number) {
    search(page);
}

onMounted(() => {
    search();
});
</script>

<template>
    <div class="simple-search">
        <!-- Search input -->
        <TermFilter
            :graph-slug="activeTypeId"
            :config="{}"
            filter-key="termfilter"
        />

        <!-- Resource type tabs -->
        <ResourceTypeFilter />

        <!-- Active filter chips + result count -->
        <ActiveFilters :count="searchResults.pagination.total_results" />

        <!-- Sort + action buttons -->
        <ResultsToolbar
            :sort-options="sortOptions"
            :sort-value="sortValue"
            :show-filters="showAttributeFilters"
            @update:sort-value="sortValue = $event"
            @toggle-filters="showAttributeFilters = !showAttributeFilters"
            @toggle-map="() => {}"
            @toggle-time="() => {}"
            @export="() => {}"
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
