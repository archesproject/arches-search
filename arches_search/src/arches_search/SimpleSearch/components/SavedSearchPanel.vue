<script setup lang="ts">
import { ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import SavedSearchList from "@/arches_search/SimpleSearch/components/SavedSearchList.vue";
import SaveSearchForm from "@/arches_search/SimpleSearch/components/SaveSearchForm.vue";

import type {
    SavedResourceSet,
    SearchDefinition,
    SearchResultsToSave,
} from "@/arches_search/SimpleSearch/types.ts";

const SAVE_TAB = "save" as const;
const MINE_TAB = "mine" as const;
const SHARED_TAB = "shared" as const;

const RUN_QUERY_EVENT = "run-query" as const;
const SHOW_RESOURCE_SET_EVENT = "show-resource-set" as const;
const CLOSE_EVENT = "close" as const;

const {
    shouldShowHeader = true,
    shouldShowSaveTab = true,
    definitionToSave = null,
    resultsToSave = null,
    resultCount = 0,
    canShowResourceSetResults = false,
} = defineProps<{
    shouldShowHeader?: boolean;
    shouldShowSaveTab?: boolean;
    definitionToSave?: SearchDefinition | null;
    // Given, the save tab can also save the results as a resource set.
    resultsToSave?: SearchResultsToSave | null;
    resultCount?: number;
    // Enables a set's "Show results", which emits show-resource-set.
    canShowResourceSetResults?: boolean;
}>();

const emit = defineEmits<{
    (
        event: typeof RUN_QUERY_EVENT,
        queryDefinition: Record<string, unknown>,
        searchName: string,
    ): void;
    (
        event: typeof SHOW_RESOURCE_SET_EVENT,
        resourceSet: SavedResourceSet,
    ): void;
    (event: typeof CLOSE_EVENT): void;
}>();

const { $gettext } = useGettext();

const activeTab = ref<typeof SAVE_TAB | typeof MINE_TAB | typeof SHARED_TAB>(
    shouldShowSaveTab ? SAVE_TAB : MINE_TAB,
);
</script>

<template>
    <div class="saved-search-panel">
        <div
            v-if="shouldShowHeader"
            class="panel-header"
        >
            <span class="panel-header-title">
                <i class="pi pi-bookmark-fill" />
                {{ $gettext("Save Search") }}
            </span>
            <Button
                icon="pi pi-times"
                icon-pos="left"
                class="panel-close-btn"
                :label="$gettext('Close')"
                :text="true"
                @click="emit(CLOSE_EVENT)"
            />
        </div>

        <div class="panel-tabs">
            <Button
                v-if="shouldShowSaveTab"
                :label="$gettext('Save this search')"
                :text="true"
                :class="['panel-tab', { active: activeTab === SAVE_TAB }]"
                @click="activeTab = SAVE_TAB"
            />
            <Button
                :label="$gettext('My Saved Searches')"
                :text="true"
                :class="['panel-tab', { active: activeTab === MINE_TAB }]"
                @click="activeTab = MINE_TAB"
            />
            <Button
                :label="$gettext('Shared Searches')"
                :text="true"
                :class="['panel-tab', { active: activeTab === SHARED_TAB }]"
                @click="activeTab = SHARED_TAB"
            />
        </div>

        <SaveSearchForm
            v-if="activeTab === SAVE_TAB"
            :definition-to-save="definitionToSave"
            :results-to-save="resultsToSave"
            :result-count="resultCount"
        />
        <SavedSearchList
            v-else
            :scope="activeTab"
            :can-show-resource-set-results="canShowResourceSetResults"
            @run-query="
                (queryDefinition, searchName) =>
                    emit(RUN_QUERY_EVENT, queryDefinition, searchName)
            "
            @show-resource-set="
                (resourceSet) => emit(SHOW_RESOURCE_SET_EVENT, resourceSet)
            "
        />
    </div>
</template>

<style scoped>
.saved-search-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    font-size: var(--p-arches-search-font-size);
    background: var(--arches-search-card-bg);
}

.panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    padding-inline: 1.6rem;
    min-height: 5.5rem;
    font-weight: 600;
    color: var(--p-text-color);
    background: var(--arches-search-page-bg);
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.panel-header-title .pi {
    margin-inline-end: 0.6rem;
    color: var(--p-primary-color);
}

.panel-close-btn {
    padding: 0.3rem 0.8rem;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--p-text-muted-color);
    border-radius: 0.4rem;
}

.panel-close-btn:hover {
    background: var(--p-content-hover-background);
    color: var(--p-text-color);
}

.panel-tabs {
    display: flex;
    flex-shrink: 0;
    padding: 0.3125rem 0.75rem;
    border-block-end: 0.0625rem solid var(--p-content-border-color);
}

.panel-tab {
    flex: 1;
    min-inline-size: 0;
    padding: 0.5rem 0.625rem;
    overflow: hidden;
    border-block-end: 0.125rem solid transparent;
    border-radius: 0;
    font-size: 1.2rem;
    font-weight: 500;
    white-space: nowrap;
    text-overflow: ellipsis;
    color: var(--p-text-muted-color);
    transition:
        background-color 0.12s,
        color 0.12s,
        border-color 0.12s;
}

.panel-tab.active {
    border-block-end-color: var(--p-primary-color);
    color: var(--p-text-color);
    font-weight: 600;
}

.panel-tab:hover:not(.active) {
    background-color: var(--p-content-hover-background);
    color: var(--p-text-color);
}
</style>
