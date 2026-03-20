<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Chip from "primevue/chip";

import type { ActiveFilter } from "@/arches_search/SimpleSearch/types.ts";

const { $gettext } = useGettext();

defineProps<{
    count: number;
    resourceTypeLabel: string;
    filters: ActiveFilter[];
}>();

defineEmits<{
    (event: "clear-all"): void;
}>();
</script>

<template>
    <div
        v-if="count > 0 || filters.length > 0"
        class="active-filters"
    >
        <span class="results-count">
            {{ count }}
            {{ resourceTypeLabel }}
            {{ $gettext("match") }}
        </span>

        <div
            v-if="filters.length > 0"
            class="filter-chips"
        >
            <Chip
                v-for="filter in filters"
                :key="filter.id"
                :label="filter.label"
                removable
                class="filter-chip"
                @remove="filter.clear()"
            />
        </div>

        <button
            v-if="filters.length > 0"
            class="clear-all-btn"
            @click="$emit('clear-all')"
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
