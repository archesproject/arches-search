<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Chip from "primevue/chip";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

const { $gettext } = useGettext();
const { activeFilters, activeGraph, searchResults } = useSearchFilters();

function clearAllFilters() {
    for (const filter of activeFilters.value) {
        filter.clear();
    }
}
</script>

<template>
    <div class="active-filters">
        <span class="results-count">
            {{ searchResults.pagination?.total_results ?? 0 }}
            {{ activeGraph ? activeGraph.label : $gettext("Items") }}
            {{ $gettext("match") }}
        </span>

        <div
            v-if="activeFilters.length > 0"
            class="filter-chips"
        >
            <Chip
                v-for="filter in activeFilters"
                :key="filter.id"
                :label="filter.label"
                removable
                class="filter-chip"
                :style="filter.options?.style"
                @remove="filter.clear()"
            />
        </div>

        <button
            v-if="activeFilters.length > 0"
            class="clear-all-btn"
            @click="clearAllFilters"
        >
            {{ $gettext("Clear all") }}
        </button>
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

.results-count {
    font-weight: 600;
    white-space: nowrap;
}

.filter-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
}

.filter-chip {
    border-radius: 0.4rem;
}

.clear-all-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    text-decoration: underline;
}

.clear-all-btn:hover {
    color: var(--p-surface-400);
}
</style>
