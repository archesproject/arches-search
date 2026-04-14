<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Select from "primevue/select";

import type { SortOption } from "@/arches_search/SimpleSearch/types.ts";

const { $gettext } = useGettext();

defineProps<{
    sortValue: string;
    showFilters: boolean;
    showTime: boolean;
    hasTimeFilter: boolean;
    hideFiltersButton?: boolean;
}>();

const sortOptions = computed<SortOption[]>(() => [
    { label: $gettext("A to Z"), value: "aToZ" },
    { label: $gettext("Z to A"), value: "zToA" },
    { label: $gettext("Newest first"), value: "newest" },
    { label: $gettext("Oldest first"), value: "oldest" },
]);

defineEmits<{
    (event: "update:sortValue", value: string): void;
    (event: "toggle-filters"): void;
    (event: "toggle-map"): void;
    (event: "toggle-time"): void;
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
                class="sort-select"
                @update:model-value="$emit('update:sortValue', $event)"
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
                :label="$gettext('Show Map')"
                icon="pi pi-map"
                icon-pos="left"
                size="small"
                class="toolbar-btn"
                @click="$emit('toggle-map')"
            />
            <Button
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
                :label="$gettext('Export')"
                icon="pi pi-upload"
                icon-pos="left"
                size="small"
                class="toolbar-btn"
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
    padding: 6px 16px;
}

.toolbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.results-label {
    font-weight: 600;
    white-space: nowrap;
}

:deep(.p-select-label) {
    font-size: var(--p-arches-search-font-size);
}

:deep(.sort-select .p-select) {
    padding: 4px 8px;
}

.toolbar-right {
    display: flex;
    align-items: center;
    gap: 6px;
}

.toolbar-btn {
    font-size: var(--p-arches-search-font-size);
}

.toolbar-btn.active {
    background-color: var(--p-button-primary-hover-background);
    border-color: var(--p-button-primary-hover-border-color);
    color: var(--p-button-primary-hover-color);
}
</style>
