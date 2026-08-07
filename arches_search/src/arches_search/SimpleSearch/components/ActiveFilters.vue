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
                class="filter-chip filter-chip--search"
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
    gap: 0.6rem;
    padding: 0.8rem 2.4rem;
    border-top: 0.1rem solid var(--p-content-border-color);
    min-height: 4.4rem;
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
    display: inline-flex;
    align-items: center;
    border-radius: 999rem;
    font-size: 1.2rem;
    font-weight: 500;
    border: 0.15rem solid transparent;
    cursor: pointer;
    transition: box-shadow 0.12s;
}

.active-filters .filter-chip:hover {
    box-shadow: 0 0 0 0.2rem rgba(0, 0, 0, 0.08);
}

/* PrimeVue Chip only exposes a single label + remove-icon, so these
   approximate the mockup's fc-body/fc-value and fc-dismiss treatments. */
.active-filters .filter-chip :deep(.p-chip-label) {
    padding-block: 0.4rem;
    padding-inline: 1rem 0.8rem;
    font-weight: 600;
}

.active-filters .filter-chip :deep(.p-chip-remove-icon) {
    margin-inline-end: 0.4rem;
    opacity: 0.6;
    cursor: pointer;
    transition: opacity 0.12s;
}

.active-filters .filter-chip:hover :deep(.p-chip-remove-icon) {
    opacity: 1;
}

/* Only the free-text search-term chip (TermFilter.vue) exists as a real
   active filter today, so it's the only kind wired to a variant class.
   background is !important because TermFilter.vue sets an inline
   background-color via activeFilter.options.style, which otherwise wins. */
.active-filters .filter-chip--search {
    background: var(--arches-search-chip-search-bg) !important;
    border-color: var(--arches-search-chip-search-border);
    color: var(--arches-search-chip-search-text);
}

.active-filters .clear-all-button {
    padding: 0;
    margin-inline-start: 0.6rem;
    font-size: 1.1rem;
    color: var(--p-primary-color);
    text-decoration: underline;
}
</style>
