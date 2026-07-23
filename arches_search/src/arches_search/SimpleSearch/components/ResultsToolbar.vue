<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Select from "primevue/select";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type { SortOption } from "@/arches_search/SimpleSearch/types.ts";

const { $gettext } = useGettext();
const { searchResults } = useSearchFilters();

const totalResults = computed<number>(
    () => searchResults.value.pagination?.total_results ?? 0,
);
const resultsLabelText = computed(() =>
    $gettext("%{count} results", { count: String(totalResults.value) }),
);

defineProps<{
    sortValue: string | null;
    showFilters: boolean;
    showMap: boolean;
    hasMapFilter: boolean;
    showTime: boolean;
    hasTimeFilter: boolean;
    showSavedSearches: boolean;
    hideFiltersButton?: boolean;
    hideTimeButton?: boolean;
}>();

const sortOptions = computed<SortOption[]>(() => [
    { label: $gettext("A to Z"), value: "aToZ" },
    { label: $gettext("Z to A"), value: "zToA" },
]);

defineEmits<{
    (event: "update:sortValue", value: string | null): void;
    (event: "toggle-filters"): void;
    (event: "toggle-map"): void;
    (event: "toggle-time"): void;
    (event: "toggle-saved-searches"): void;
}>();
</script>

<template>
    <div class="results-toolbar">
        <div class="toolbar-left">
            <span class="results-label">{{ resultsLabelText }}</span>
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

/* Fixed 1.2rem (not --p-arches-search-font-size), matching the results-label
   and toolbar-btn text right next to it — that shared token now drives the
   search button specifically and no longer matches this toolbar's own
   scale. */
:deep(.p-select-label) {
    font-size: 1.2rem;
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

/* font-size (and the icon rule below) must live on this 2-class selector,
   not the bare .toolbar-btn above — PrimeVue's own .p-button-sm has the same
   single-class specificity for font-size, and its stylesheet is injected at
   runtime, after this component's own styles, so on a specificity tie it
   wins by source order, silently shrinking the label back down to Aura's
   "sm" scale. Same reasoning as the border/color !important rules below. */
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

/* Matches the label's own font-size for the same reason — PrimeVue's
   .p-button-sm .p-button-icon otherwise renders the icon at Aura's smaller
   "sm" scale, noticeably out of step with the label text next to it. */
.toolbar-right .toolbar-btn :deep(.p-button-icon) {
    font-size: 1.2rem;
}

/* PrimeVue's Aura button preset sets font-weight directly on .p-button-label
   (500), which wins over the inherited value from .toolbar-btn above since
   inheritance loses to any explicit same-specificity rule — same root cause
   as the icon rule above and the color/border !important rules below. */
.toolbar-right .toolbar-btn :deep(.p-button-label) {
    font-weight: 600;
}

.toolbar-right .toolbar-btn:last-child {
    border-inline-end: none;
}

/* !important + explicit border shorthands (not just border-color) because
   PrimeVue's own default-button :hover styling otherwise wins on properties
   this rule doesn't pin — including border-style/width on the three sides
   that should stay borderless, which was rendering an unwanted border AND
   making the buttons visibly grow on hover. border-inline-end is reasserted
   at its resting width/color so the segmented-group divider between buttons
   neither disappears nor shifts. Same reasoning as .type-btn:hover in
   ResourceTypeFilter.vue. */
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

/* Higher specificity than .toolbar-right .toolbar-btn:hover above, so
   hovering an already-active button keeps its highlight instead of
   falling back to the plain grey hover background. */
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
