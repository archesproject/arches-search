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
    showTime: boolean;
    showSavedSearches: boolean;
    showExportPanel: boolean;
    hideFiltersButton?: boolean;
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
                :label="showMap ? $gettext('Hide Map') : $gettext('Show Map')"
                icon="pi pi-map"
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showMap }]"
                @click="$emit('toggle-map')"
            />
            <Button
                :label="
                    showTime ? $gettext('Hide Time') : $gettext('Show Time')
                "
                icon="pi pi-clock"
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showTime }]"
                @click="$emit('toggle-time')"
            />
            <Button
                :label="
                    showSavedSearches
                        ? $gettext('Hide Saved Searches')
                        : $gettext('Saved Searches')
                "
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
    padding: 0.375rem 1rem;
}

.toolbar-left {
    display: flex;
    align-items: center;
    gap: 0.625rem;
}

.results-label {
    font-weight: 600;
    white-space: nowrap;
}

:deep(.p-select-label) {
    font-size: var(--p-arches-search-font-size);
}

:deep(.sort-select .p-select) {
    padding: 0.25rem 0.5rem;
}

.toolbar-right {
    display: flex;
    align-items: center;
    gap: 0.375rem;
}

.toolbar-btn {
    font-size: var(--p-arches-search-font-size);
}

.toolbar-btn.active {
    background-color: var(--p-button-primary-hover-background);
    border-color: var(--p-button-primary-hover-border-color);
    color: var(--p-button-primary-hover-color);
}

.save-search-btn {
    background-color: var(--p-primary-color);
    border-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color);
}
</style>
