<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Select from "primevue/select";

import type { SortOption } from "@/arches_search/SimpleSearch/types.ts";

const { $gettext } = useGettext();

const props = defineProps<{
    sortValue: string | null;
    showFilters: boolean;
    showMap: boolean;
    hasMapFilter: boolean;
    showTime: boolean;
    hasTimeFilter: boolean;
    showSavedSearches: boolean;
    showExportPanel: boolean;
    hideFiltersButton?: boolean;
    hideTimeButton?: boolean;
}>();

const sortOptions = computed<SortOption[]>(() => [
    { label: $gettext("A to Z"), value: "aToZ" },
    { label: $gettext("Z to A"), value: "zToA" },
]);

const exportButtonLabel = computed(() =>
    props.showExportPanel ? $gettext("Hide Export") : $gettext("Export"),
);

defineEmits<{
    (event: "update:sortValue", value: string | null): void;
    (event: "save-search"): void;
    (event: "toggle-filters"): void;
    (event: "toggle-map"): void;
    (event: "toggle-time"): void;
    (event: "toggle-saved-searches"): void;
    (event: "export"): void;
}>();
</script>

<template>
    <div class="results-toolbar">
        <div class="toolbar-left">
            <span class="results-label">{{ $gettext("Results") }}</span>
            <Select
                :model-value="sortValue"
                :options="sortOptions"
                option-label="label"
                option-value="value"
                :placeholder="$gettext('Sort by...')"
                show-clear
                class="sort-select"
                @update:model-value="$emit('update:sortValue', $event)"
            />
            <Button
                :label="$gettext('Save this search')"
                icon="pi pi-save"
                icon-pos="left"
                size="small"
                class="toolbar-btn save-search-btn"
                @click="$emit('save-search')"
            />
        </div>

        <div class="toolbar-right">
            <Button
                v-if="!hideFiltersButton"
                :label="
                    showFilters
                        ? $gettext('Hide Filters')
                        : $gettext('Show Filters')
                "
                icon="pi pi-filter"
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showFilters }]"
                @click="$emit('toggle-filters')"
            />
            <Button
                v-if="!hideTimeButton"
                :label="
                    showTime ? $gettext('Hide Time') : $gettext('Show Time')
                "
                icon="pi pi-clock"
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showTime || hasTimeFilter }]"
                @click="$emit('toggle-time')"
            />
            <Button
                :label="showMap ? $gettext('Hide Map') : $gettext('Show Map')"
                icon="pi pi-map"
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showMap || hasMapFilter }]"
                @click="$emit('toggle-map')"
            />
            <Button
                :label="$gettext('Saved Searches')"
                icon="pi pi-bookmark"
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showSavedSearches }]"
                @click="$emit('toggle-saved-searches')"
            />
            <Button
                :label="exportButtonLabel"
                icon="pi pi-upload"
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showExportPanel }]"
                @click="$emit('export')"
            />
        </div>
    </div>
</template>

<style scoped>
.results-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.2rem;
    padding: 1rem 2.4rem;
    border-top: 0.1rem solid var(--p-content-border-color);
    border-bottom: 0.1rem solid var(--p-content-border-color);
    background: var(--arches-search-page-bg);
    min-height: 5.5rem;
}

.toolbar-left {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.results-label {
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 1rem;
    background: var(--p-surface-100);
    color: var(--p-text-muted-color);
    border-radius: 999rem;
    font-size: 1.2rem;
    font-weight: 600;
    white-space: nowrap;
}

:deep(.p-select-label) {
    font-size: var(--p-arches-search-font-size);
}

:deep(.sort-select .p-select) {
    padding: 0.4rem 0.8rem;
}

/* segmented view-toggle button bar */
.toolbar-right {
    display: inline-flex;
    align-items: center;
    gap: 0;
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 0.6rem;
    overflow: hidden;
    background: var(--p-content-background);
}

.toolbar-btn {
    font-size: 1.2rem;
}

.toolbar-right .toolbar-btn {
    padding: 0.7rem 1rem;
    font-weight: 500;
    border: none;
    border-inline-end: 0.1rem solid var(--p-content-border-color);
    border-radius: 0;
    background: transparent;
    color: var(--p-text-muted-color);
    transition:
        background 0.12s,
        color 0.12s;
}

.toolbar-right .toolbar-btn:last-child {
    border-inline-end: none;
}

.toolbar-right .toolbar-btn:hover {
    background: var(--p-content-hover-background);
}

.toolbar-btn.active {
    background-color: var(--arches-search-highlight-bg);
    border-color: var(--arches-search-highlight-bg);
    color: var(--arches-search-highlight-text);
}

.save-search-btn {
    background-color: var(--p-primary-color);
    border-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color);
    border-radius: 0.6rem;
}
</style>
