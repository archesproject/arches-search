<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Select from "primevue/select";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import {
    RESULTS_SORT_CREATED_TIME,
    RESULTS_SORT_NAME,
    RESULTS_SORT_NODE_PREFIX,
    RESULTS_SORT_RELEVANCE,
} from "@/arches_search/SimpleSearch/types.ts";
import type {
    NodeFilterConfigNode,
    ResultsSortDirection,
    ResultsSortField,
    SortOption,
} from "@/arches_search/SimpleSearch/types.ts";

const { $gettext } = useGettext();
const { searchResults } = useSearchFilters();

const totalResults = computed<number>(
    () => searchResults.value.pagination?.total_results ?? 0,
);
const resultsLabelText = computed(() =>
    $gettext("%{count} results", { count: String(totalResults.value) }),
);

const props = defineProps<{
    sortField: ResultsSortField | null;
    sortDirection: ResultsSortDirection;
    sortableNodes: NodeFilterConfigNode[];
    showFilters: boolean;
    showMap: boolean;
    hasMapFilter: boolean;
    showTime: boolean;
    hasTimeFilter: boolean;
    showSavedSearches: boolean;
    hideFiltersButton?: boolean;
    hideTimeButton?: boolean;
}>();

defineEmits<{
    (event: "update:sortField", value: ResultsSortField | null): void;
    (event: "update:sortDirection", value: ResultsSortDirection): void;
    (event: "toggle-filters"): void;
    (event: "toggle-map"): void;
    (event: "toggle-time"): void;
    (event: "toggle-saved-searches"): void;
}>();

const sortFieldOptions = computed<SortOption[]>(() => {
    const options: SortOption[] = [
        { label: $gettext("Relevance"), value: RESULTS_SORT_RELEVANCE },
        { label: $gettext("Title"), value: RESULTS_SORT_NAME },
        { label: $gettext("Date created"), value: RESULTS_SORT_CREATED_TIME },
    ];

    for (const node of props.sortableNodes) {
        options.push({
            label: node.label,
            value: `${RESULTS_SORT_NODE_PREFIX}${node.node_alias}`,
        });
    }

    return options;
});

const directionIcon = computed<string>(() =>
    props.sortDirection === "asc"
        ? "pi pi-sort-amount-down-alt"
        : "pi pi-sort-amount-up-alt",
);

const directionLabel = computed<string>(() =>
    props.sortDirection === "asc"
        ? $gettext("Sort ascending")
        : $gettext("Sort descending"),
);

const showDirectionToggle = computed<boolean>(
    () =>
        Boolean(props.sortField) && props.sortField !== RESULTS_SORT_RELEVANCE,
);
</script>

<template>
    <div class="results-toolbar">
        <div class="toolbar-left">
            <span class="results-label">{{ resultsLabelText }}</span>
            <Select
                :model-value="sortField"
                :options="sortFieldOptions"
                option-label="label"
                option-value="value"
                :placeholder="$gettext('Sort by...')"
                :show-clear="true"
                class="sort-select"
                overlay-class="sort-select-overlay"
                @update:model-value="$emit('update:sortField', $event)"
            />
            <Button
                v-if="showDirectionToggle"
                text
                rounded
                class="sort-direction-btn"
                :icon="directionIcon"
                :aria-label="directionLabel"
                @click="
                    $emit(
                        'update:sortDirection',
                        sortDirection === 'asc' ? 'desc' : 'asc',
                    )
                "
            />
        </div>

        <div class="toolbar-right">
            <Button
                v-if="!hideFiltersButton"
                :label="$gettext('Facets')"
                icon="pi pi-filter"
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showFilters }]"
                @click="$emit('toggle-filters')"
            />
            <Button
                v-if="!hideTimeButton"
                :label="$gettext('Time')"
                icon="pi pi-clock"
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showTime || hasTimeFilter }]"
                @click="$emit('toggle-time')"
            />
            <Button
                :label="$gettext('Map')"
                icon="pi pi-map"
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showMap || hasMapFilter }]"
                @click="$emit('toggle-map')"
            />
            <Button
                :label="$gettext('Save/Export Search')"
                :icon="
                    showSavedSearches ? 'pi pi-bookmark-fill' : 'pi pi-bookmark'
                "
                icon-pos="left"
                size="small"
                :class="['toolbar-btn', { active: showSavedSearches }]"
                @click="$emit('toggle-saved-searches')"
            />
        </div>
    </div>
</template>

<style scoped>
.results-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap-reverse;
    flex-shrink: 0;
    gap: 1.2rem;
    padding: 1rem;
    padding-inline-start: 1.4rem;
    border-bottom: 0.15rem solid var(--p-content-border-color);
    background: var(--arches-search-page-bg);
    min-height: 5.5rem;
}

.toolbar-left {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

.results-label {
    display: inline-flex;
    align-items: center;
    padding-inline: 1rem;
    background: var(--arches-search-page-bg);
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 600;
    white-space: nowrap;
}

:deep(.p-select-label) {
    font-size: 1.2rem;
}

:deep(.sort-select .p-select) {
    padding: 0.4rem 0.8rem;
}

.sort-direction-btn :deep(.p-button-icon) {
    font-size: 2rem;
}

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
    font-size: 1.2rem;
    font-weight: 600;
    border: none;
    border-inline-end: 0.1rem solid var(--p-content-border-color);
    border-radius: 0;
    background: transparent;
    color: var(--arches-search-sec-btn-text);
    transition:
        background 0.12s,
        color 0.12s;
}

.toolbar-right .toolbar-btn :deep(.p-button-icon) {
    font-size: 1.2rem;
}

.toolbar-right .toolbar-btn :deep(.p-button-label) {
    font-weight: 600;
}

.toolbar-right .toolbar-btn:last-child {
    border-inline-end: none;
}

.toolbar-right .toolbar-btn:hover {
    background: var(--arches-search-sec-btn-hover-bg) !important;
    border-block-start: none !important;
    border-block-end: none !important;
    border-inline-start: none !important;
    border-inline-end: 0.1rem solid var(--p-content-border-color) !important;
    color: var(--arches-search-sec-btn-text) !important;
}

.toolbar-right .toolbar-btn:last-child:hover {
    border-inline-end: none !important;
}

.toolbar-btn.active {
    background-color: var(--arches-search-highlight-bg);
    border-color: var(--arches-search-highlight-bg);
    color: var(--arches-search-highlight-text);
}

.toolbar-right .toolbar-btn.active:hover {
    background-color: var(--arches-search-highlight-bg) !important;
    border-block-start: none !important;
    border-block-end: none !important;
    border-inline-start: none !important;
    border-inline-end: 0.1rem solid var(--arches-search-highlight-bg) !important;
    color: var(--arches-search-highlight-text) !important;
}

.toolbar-right .toolbar-btn.active:last-child:hover {
    border-inline-end: none !important;
}
</style>
