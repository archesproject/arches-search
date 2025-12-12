<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import InputText from "primevue/inputtext";

import type { SearchResults as SearchResultsPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { filterText, searchResults } = defineProps<{
    filterText: string;
    searchResults: SearchResultsPayload | null;
}>();

const emit = defineEmits<{
    (event: "update:filter-text", nextFilterText: string): void;
}>();

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
</script>

<template>
    <div class="advanced-search-footer">
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
