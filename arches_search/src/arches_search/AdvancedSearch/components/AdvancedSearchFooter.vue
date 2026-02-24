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
    "update:filter-text": [nextFilterText: string];
}>();

const hasSearchResults = computed(
    () => (searchResults?.resources.length ?? 0) > 0,
);

const summaryLabel = computed(() => {
    if (!hasSearchResults.value) {
        return null;
    }

    const resources = searchResults!.resources;

    let loadedResultsCount;
    if (filterText) {
        loadedResultsCount = resources.filter((resource) =>
            resource.name?.includes(filterText),
        ).length;
    } else {
        loadedResultsCount = resources.length;
    }

    const totalResultsCount = searchResults!.pagination.total_results;

    return $gettext("Showing %{loaded} of %{total} results", {
        loaded: loadedResultsCount.toLocaleString(),
        total: totalResultsCount.toLocaleString(),
    });
});

function onUpdateFilterText(value: string | undefined) {
    emit("update:filter-text", value ?? "");
}
</script>

<template>
    <div class="advanced-search-footer">
        <InputText
            :model-value="filterText"
            :placeholder="$gettext('Filter')"
            :disabled="!hasSearchResults"
            @update:model-value="onUpdateFilterText"
        />

        <span v-if="summaryLabel">{{ summaryLabel }}</span>
    </div>
</template>

<style scoped>
.advanced-search-footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-top: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    font-size: 1.2rem;
}
</style>
