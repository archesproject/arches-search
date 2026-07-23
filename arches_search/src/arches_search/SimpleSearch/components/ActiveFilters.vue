<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import type { ActiveFilter } from "@/arches_search/SimpleSearch/types.ts";

const CLEAR_ALL_EVENT = "clear-all" as const;

const { activeFilters } = defineProps<{
    activeFilters: ActiveFilter[];
}>();

const emit = defineEmits<{
    (event: typeof CLEAR_ALL_EVENT): void;
}>();

const { $gettext } = useGettext();

const hasActiveFilters = computed(() => activeFilters.length > 0);

function editTitle(activeFilter: ActiveFilter): string | undefined {
    if (!activeFilter.onEdit) {
        return undefined;
    }

    return $gettext("Click to edit %{category} filter", {
        category: activeFilter.category,
    });
}

function removeLabel(activeFilter: ActiveFilter): string {
    return $gettext("Remove %{category} filter", {
        category: activeFilter.category,
    });
}

function onChipClick(activeFilter: ActiveFilter): void {
    activeFilter.onEdit?.();
}

function clearFilter(activeFilter: ActiveFilter): void {
    activeFilter.clear();
}

function clearAllFilters(): void {
    for (const activeFilter of activeFilters) {
        clearFilter(activeFilter);
    }

    emit(CLEAR_ALL_EVENT);
}
</script>

<template>
    <div
        v-if="hasActiveFilters"
        class="active-filters"
    >
        <span class="filter-tag-label">{{ $gettext("Filters:") }}</span>

        <button
            v-for="activeFilter in activeFilters"
            :key="activeFilter.id"
            type="button"
            class="filter-chip"
            :class="[
                'filter-chip--' + activeFilter.kind,
                { 'filter-chip--editable': !!activeFilter.onEdit },
            ]"
            :title="editTitle(activeFilter)"
            @click="onChipClick(activeFilter)"
        >
            <span class="fc-body">
                <i :class="[activeFilter.icon, 'fc-icon']" />
                <span class="fc-category">{{ activeFilter.category }}</span>
                <span class="fc-sep">·</span>
                <span class="fc-value">{{ activeFilter.text }}</span>
            </span>
            <span
                class="fc-dismiss"
                :aria-label="removeLabel(activeFilter)"
                @click.stop="clearFilter(activeFilter)"
            >
                <i class="pi pi-times" />
            </span>
        </button>

        <Button
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

.filter-tag-label {
    font-size: 1.1rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--p-text-muted-color);
    white-space: nowrap;
}

.filter-chip {
    display: inline-flex;
    align-items: center;
    border-radius: 999rem;
    font-size: 1.2rem;
    font-weight: 500;
    border: 0.15rem solid transparent;
    cursor: default;
    user-select: none;
    background: transparent;
    padding: 0;
    overflow: hidden;
    font-family: inherit;
    transition: box-shadow 0.12s;
}

.filter-chip--editable {
    cursor: pointer;
}

.filter-chip--editable:hover {
    box-shadow: 0 0 0 0.2rem rgba(0, 0, 0, 0.08);
}

.filter-chip:focus-visible {
    outline: 0.2rem solid var(--p-primary-color);
    outline-offset: 0.2rem;
}

.fc-body {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.8rem 0.4rem 1rem;
    font-size: 1.2rem;
    font-weight: 500;
    line-height: 1;
}

.fc-icon {
    font-size: 1rem;
    flex-shrink: 0;
}

.fc-category {
    font-size: 1rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    opacity: 0.7;
}

.fc-sep {
    opacity: 0.4;
    margin: 0 0.1rem;
}

.fc-value {
    font-weight: 600;
}

.fc-dismiss {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.4rem 0.8rem 0.4rem 0.4rem;
    font-size: 1rem;
    opacity: 0.6;
    background: transparent;
    border: none;
    cursor: pointer;
    color: inherit;
    transition: opacity 0.12s;
}

.fc-dismiss:hover {
    opacity: 1;
}

.filter-chip--term {
    background: var(--arches-search-chip-search-bg);
    border-color: var(--arches-search-chip-search-border);
    color: var(--arches-search-chip-search-text);
}

.filter-chip--resource-type {
    background: var(--arches-search-filter-resource-type-bg);
    border-color: var(--arches-search-filter-resource-type-border);
    color: var(--arches-search-filter-resource-type-text);
}

.filter-chip--time {
    background: var(--arches-search-filter-time-bg);
    border-color: var(--arches-search-filter-time-border);
    color: var(--arches-search-filter-time-text);
}

.filter-chip--map {
    background: var(--arches-search-filter-map-bg);
    border-color: var(--arches-search-filter-map-border);
    color: var(--arches-search-filter-map-text);
}

.filter-chip--attribute {
    background: var(--arches-search-filter-attribute-bg);
    border-color: var(--arches-search-filter-attribute-border);
    color: var(--arches-search-filter-attribute-text);
}

.clear-all-button {
    padding: 0;
    margin-inline-start: 0.6rem;
    font-size: 1.1rem;
    color: var(--p-primary-color);
    text-decoration: underline;
}
</style>
