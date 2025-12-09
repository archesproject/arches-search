<script setup lang="ts">
import { ref, computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import InputText from "primevue/inputtext";

import PayloadAnalyzer from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/PayloadAnalyzer.vue";

import type {
    AdvancedSearchFacet,
    GroupPayload,
    SearchResults as SearchResultsPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type GraphSummary = {
    graphid?: string;
    slug?: string;
    name?: string;
    label?: string;
    [key: string]: unknown;
};

const {
    filterText,
    isSearching,
    searchPayload,
    searchResults,
    graphs,
    datatypesToAdvancedSearchFacets,
} = defineProps<{
    filterText: string;
    isSearching: boolean;
    searchPayload?: GroupPayload;
    searchResults: SearchResultsPayload | null;
    graphs: GraphSummary[];
    datatypesToAdvancedSearchFacets: Record<string, AdvancedSearchFacet[]>;
}>();

const emit = defineEmits<{
    (event: "update:filter-text", nextFilterText: string): void;
    (event: "search"): void;
}>();

const shouldShowPayloadAnalyzer = ref(false);

const hasSearchResults = computed<boolean>(() => {
    const loadedResultsCount = searchResults?.resources?.length ?? 0;
    return loadedResultsCount > 0;
});

const filteredResultsCount = computed<number>(() => {
    const resources = searchResults?.resources ?? [];

    if (!filterText) {
        return resources.length;
    }

    return resources.filter((resource) => {
        if (resource.name?.includes(filterText)) {
            return true;
        }
    }).length;
});

const resultsSummaryLabelForFooter = computed<string>(() => {
    if (!hasSearchResults.value) {
        return "";
    }

    const totalResults = searchResults?.pagination.total_results ?? 0;
    const loadedLabel = filteredResultsCount.value.toLocaleString();
    const totalLabel = totalResults.toLocaleString();

    return $gettext("Showing %{loaded} of %{total} results", {
        loaded: loadedLabel,
        total: totalLabel,
    });
});

function onFilterInputChange(nextFilterText: string | undefined): void {
    emit("update:filter-text", nextFilterText ?? "");
}

function onSearchButtonClick(): void {
    emit("search");
}

function onAnalyzePayloadButtonClick(): void {
    if (!searchPayload) {
        return;
    }

    shouldShowPayloadAnalyzer.value = true;
}
</script>

<template>
    <div class="advanced-search-footer">
        <div class="advanced-search-footer-controls">
            <Button
                icon="pi pi-search"
                severity="primary"
                size="large"
                :label="$gettext('Search')"
                :loading="isSearching"
                :disabled="!searchPayload || isSearching"
                @click="onSearchButtonClick"
            />

            <Button
                icon="pi pi-info-circle"
                severity="secondary"
                size="large"
                :label="$gettext('Describe Query')"
                :disabled="!searchPayload"
                @click="onAnalyzePayloadButtonClick"
            />
        </div>

        <div class="advanced-search-footer-controls">
            <InputText
                :model-value="filterText"
                :placeholder="$gettext('Filter')"
                :disabled="!hasSearchResults"
                @update:model-value="onFilterInputChange"
            />

            <div v-if="hasSearchResults">
                {{ resultsSummaryLabelForFooter }}
            </div>
        </div>

        <PayloadAnalyzer
            v-if="searchPayload"
            :datatypes-to-advanced-search-facets="
                datatypesToAdvancedSearchFacets
            "
            :graphs="graphs"
            :payload="searchPayload"
            :visible="shouldShowPayloadAnalyzer"
            @update:visible="shouldShowPayloadAnalyzer = $event"
        />
    </div>
</template>

<style scoped>
.advanced-search-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.5rem;
    border-top: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    font-size: 1.2rem;
}

.advanced-search-footer-controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
</style>
