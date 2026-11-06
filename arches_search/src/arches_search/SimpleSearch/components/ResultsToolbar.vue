<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Select from "openvue/select";
import ToggleSwitch from "openvue/toggleswitch";

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

const UPDATE_SORT_FIELD_EVENT = "update:sortField" as const;
const UPDATE_SORT_DIRECTION_EVENT = "update:sortDirection" as const;
const TOGGLE_FILTERS_EVENT = "toggle-filters" as const;
const TOGGLE_MAP_EVENT = "toggle-map" as const;
const TOGGLE_TIME_EVENT = "toggle-time" as const;
const TOGGLE_SAVED_SEARCHES_EVENT = "toggle-saved-searches" as const;
const TOGGLE_EXPORT_RESULTS_EVENT = "toggle-export-results" as const;

const {
    totalResults,
    sortField,
    sortDirection,
    sortableNodes = [],
    showFilters = false,
    showMap = false,
    hasMapFilter = false,
    showTime = false,
    hasTimeFilter = false,
} = defineProps<{
    totalResults: number;
    sortField: ResultsSortField | null;
    sortDirection: ResultsSortDirection;
    sortableNodes?: NodeFilterConfigNode[];
    showFilters?: boolean;
    showMap?: boolean;
    hasMapFilter?: boolean;
    showTime?: boolean;
    hasTimeFilter?: boolean;
    showSavedSearches: boolean;
    showExportResults: boolean;
    hideFiltersButton?: boolean;
    hideTimeButton?: boolean;
    hideMapButton?: boolean;
    hideIncludeRelated?: boolean;
}>();

const emit = defineEmits<{
    (
        event: typeof UPDATE_SORT_FIELD_EVENT,
        value: ResultsSortField | null,
    ): void;
    (
        event: typeof UPDATE_SORT_DIRECTION_EVENT,
        value: ResultsSortDirection,
    ): void;
    (event: typeof TOGGLE_FILTERS_EVENT): void;
    (event: typeof TOGGLE_MAP_EVENT): void;
    (event: typeof TOGGLE_TIME_EVENT): void;
    (event: typeof TOGGLE_SAVED_SEARCHES_EVENT): void;
    (event: typeof TOGGLE_EXPORT_RESULTS_EVENT): void;
}>();

const { $gettext } = useGettext();
const { includeRelated, setIncludeRelated } = useSearchFilters();

const resultsLabelText = computed<string>(() =>
    $gettext("%{count} results", { count: String(totalResults) }),
);

const sortFieldOptions = computed<SortOption[]>(() => {
    const options: SortOption[] = [
        { label: $gettext("Relevance"), value: RESULTS_SORT_RELEVANCE },
        { label: $gettext("Title"), value: RESULTS_SORT_NAME },
        { label: $gettext("Date created"), value: RESULTS_SORT_CREATED_TIME },
    ];

    for (const node of sortableNodes) {
        options.push({
            label: node.label,
            value: `${RESULTS_SORT_NODE_PREFIX}${node.node_alias}`,
        });
    }

    return options;
});

const directionIcon = computed<string>(() => {
    if (sortDirection === "asc") {
        return "pi pi-sort-amount-down-alt";
    }
    return "pi pi-sort-amount-up-alt";
});

const directionLabel = computed<string>(() => {
    if (sortDirection === "asc") {
        return $gettext("Sort ascending");
    }
    return $gettext("Sort descending");
});

const showDirectionToggle = computed<boolean>(
    () => sortField !== null && sortField !== RESULTS_SORT_RELEVANCE,
);
</script>

<template>
    <div class="results-toolbar">
        <div class="toolbar-left">
            <span class="results-label">{{ resultsLabelText }}</span>
            <Select
                option-label="label"
                option-value="value"
                class="sort-select"
                overlay-class="sort-select-overlay"
                :model-value="sortField"
                :options="sortFieldOptions"
                :placeholder="$gettext('Sort by...')"
                :show-clear="true"
                @update:model-value="emit(UPDATE_SORT_FIELD_EVENT, $event)"
            />
            <Button
                v-if="showDirectionToggle"
                class="sort-direction-btn"
                variant="text"
                :rounded="true"
                :icon="directionIcon"
                :aria-label="directionLabel"
                @click="
                    emit(
                        UPDATE_SORT_DIRECTION_EVENT,
                        sortDirection === 'asc' ? 'desc' : 'asc',
                    )
                "
            />
            <div
                v-if="!hideIncludeRelated"
                class="include-related"
            >
                <ToggleSwitch
                    input-id="include-related-toggle"
                    :model-value="includeRelated"
                    @update:model-value="setIncludeRelated"
                />
                <label for="include-related-toggle">
                    {{ $gettext("Include Related") }}
                </label>
            </div>
        </div>

        <div class="toolbar-right">
            <Button
                v-if="!hideFiltersButton"
                icon="pi pi-filter"
                icon-pos="left"
                size="small"
                :label="$gettext('Filters')"
                :class="['toolbar-btn', { active: showFilters }]"
                @click="emit(TOGGLE_FILTERS_EVENT)"
            />
            <Button
                v-if="!hideTimeButton"
                icon="pi pi-clock"
                icon-pos="left"
                size="small"
                :label="$gettext('Time')"
                :class="['toolbar-btn', { active: showTime || hasTimeFilter }]"
                @click="emit(TOGGLE_TIME_EVENT)"
            />
            <Button
                v-if="!hideMapButton"
                icon="pi pi-map"
                icon-pos="left"
                size="small"
                :label="$gettext('Map')"
                :class="['toolbar-btn', { active: showMap || hasMapFilter }]"
                @click="emit(TOGGLE_MAP_EVENT)"
            />
            <Button
                icon-pos="left"
                size="small"
                :label="$gettext('Save Search')"
                :icon="
                    showSavedSearches ? 'pi pi-bookmark-fill' : 'pi pi-bookmark'
                "
                :class="['toolbar-btn', { active: showSavedSearches }]"
                @click="emit(TOGGLE_SAVED_SEARCHES_EVENT)"
            />
            <Button
                icon="pi pi-download"
                icon-pos="left"
                size="small"
                :label="$gettext('Export Results')"
                :class="['toolbar-btn', { active: showExportResults }]"
                @click="emit(TOGGLE_EXPORT_RESULTS_EVENT)"
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
    border-block-end: 0.15rem solid var(--p-content-border-color);
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

.include-related {
    display: inline-flex;
    align-items: center;
    gap: 0.8rem;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 600;
    white-space: nowrap;
}

.include-related label {
    margin: 0;
    line-height: 1;
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
