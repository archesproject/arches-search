<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Chip from "primevue/chip";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type { ActiveFilter } from "@/arches_search/SimpleSearch/types.ts";

const CLEAR_ALL_EVENT = "clear-all" as const;

const emit = defineEmits<{
    (event: typeof CLEAR_ALL_EVENT): void;
}>();

const { $gettext } = useGettext();
const { activeFilters, resultsGraph, searchResults } = useSearchFilters();

const hasActiveFilters = computed(() => activeFilters.value.length > 0);
const totalResults = computed(
    () => searchResults.value.pagination?.total_results ?? 0,
);
const resourceTypeLabel = computed(
    () => resultsGraph.value?.label ?? $gettext("Items"),
);
const resultsCountText = computed(() =>
    $gettext("%{totalResults} %{resourceType} match", {
        totalResults: String(totalResults.value),
        resourceType: resourceTypeLabel.value,
    }),
);

function clearFilter(activeFilter: ActiveFilter): void {
    activeFilter.clear();
}

function clearAllFilters(): void {
    for (const activeFilter of activeFilters.value) {
        clearFilter(activeFilter);
    }

    emit(CLEAR_ALL_EVENT);
}
</script>

<template>
    <div class="active-filters">
        <span class="results-count">
            {{ resultsCountText }}
        </span>

        <div
            v-if="hasActiveFilters"
            class="filter-chips"
        >
            <Chip
                v-for="activeFilter in activeFilters"
                :key="activeFilter.id"
                class="filter-chip"
                :label="activeFilter.text"
                :removable="true"
                :style="activeFilter.options?.style"
                @remove="clearFilter(activeFilter)"
            />
        </div>

        <Button
            v-if="hasActiveFilters"
            class="clear-all-button"
            type="button"
            variant="text"
            :label="$gettext('Clear all')"
            @click="clearAllFilters"
        />
    </div>
</template>

<style scoped>
.active-filters {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.8rem;
    padding: 0.8rem 1.6rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.active-filters .results-count {
    font-weight: 600;
    white-space: nowrap;
}

.active-filters .filter-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
}

.active-filters .filter-chip {
    border-radius: 0.4rem;
}

.active-filters .clear-all-button {
    padding: 0;
}
</style>
