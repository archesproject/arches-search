<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import AutoComplete from "primevue/autocomplete";
import Button from "primevue/button";
import Tab from "primevue/tab";
import TabList from "primevue/tablist";
import Tabs from "primevue/tabs";

import SuggestionOption from "@/arches_search/SimpleSearch/components/TermFilter/components/SuggestionOption.vue";

import { useTermSuggestions } from "@/arches_search/SimpleSearch/composables/useTermSuggestions.ts";
import { getTermKind } from "@/arches_search/SimpleSearch/components/TermFilter/suggestion-utils.ts";

import { TERM_KIND_RECORD } from "@/arches_search/SimpleSearch/types.ts";
import type {
    TermKind,
    TermSuggestion,
} from "@/arches_search/SimpleSearch/types.ts";

interface TermSuggestionSelectEvent {
    value: TermSuggestion;
}

const SUBMIT_EVENT = "submit" as const;

const emit = defineEmits<{
    (
        event: typeof SUBMIT_EVENT,
        payload: { text: string; termKind?: TermKind; icon?: string },
    ): void;
}>();

const { $gettext } = useGettext();

const {
    autoCompleteRef,
    inputText,
    isOverlayShown,
    typeaheadPanel,
    emptySearchMessage,
    typeaheadPanels,
    activeSuggestions,
    onComplete,
    showOverlay,
    hideOverlay,
    getNoResultsMessage,
    resolveSubmitCandidate,
    markSuggestionHandled,
} = useTermSuggestions();

let stagedSuggestion: TermSuggestion | null = null;

function onSelect(event: TermSuggestionSelectEvent): void {
    stagedSuggestion = event.value;
    inputText.value = event.value.text;
    markSuggestionHandled();
}

function onKeydown(event: KeyboardEvent): void {
    if (event.key !== "Enter" || isOverlayShown.value) {
        return;
    }

    submitSearch();
}

function submitSearch(): void {
    const trimmedInputText = inputText.value.trim();
    let suggestionToSubmit: TermSuggestion | null;
    if (stagedSuggestion?.text === trimmedInputText) {
        suggestionToSubmit = stagedSuggestion;
    } else {
        suggestionToSubmit = resolveSubmitCandidate();
    }

    if (!suggestionToSubmit) {
        return;
    }

    emitSubmit(suggestionToSubmit);
}

function emitSubmit(suggestion: TermSuggestion): void {
    const termKind = getTermKind(suggestion);
    const isRecordTerm = termKind === TERM_KIND_RECORD;
    emit(SUBMIT_EVENT, {
        text: suggestion.text,
        termKind,
        icon: isRecordTerm ? suggestion.graph_icon : undefined,
    });
}
</script>

<template>
    <div class="search-bar">
        <span class="search-bar-inner">
            <AutoComplete
                ref="autoCompleteRef"
                v-model="inputText"
                class="search-input"
                overlay-class="term-filter-overlay"
                option-label="text"
                scroll-height="32rem"
                append-to="body"
                :auto-option-focus="true"
                :empty-search-message="emptySearchMessage"
                :fluid="true"
                :placeholder="$gettext('Find an item, sample, supplier…')"
                :suggestions="activeSuggestions"
                @complete="onComplete"
                @option-select="onSelect"
                @keydown="onKeydown"
                @before-show="showOverlay"
                @before-hide="hideOverlay"
            >
                <template #header>
                    <div class="suggestion-tab-bar">
                        <Tabs v-model:value="typeaheadPanel">
                            <TabList>
                                <Tab
                                    v-for="panel in typeaheadPanels"
                                    :key="panel.id"
                                    :value="panel.id"
                                    @mousedown.prevent
                                >
                                    <i :class="panel.icon" />
                                    {{ panel.label }}
                                </Tab>
                            </TabList>
                        </Tabs>
                    </div>
                </template>

                <template #option="{ option }">
                    <SuggestionOption
                        :suggestion="option"
                        :query="inputText"
                    />
                </template>

                <template #empty>
                    <span class="typeahead-no-results">{{
                        getNoResultsMessage()
                    }}</span>
                </template>
            </AutoComplete>
        </span>
        <Button
            :label="$gettext('Search')"
            icon="pi pi-search"
            icon-pos="left"
            class="search-button"
            type="button"
            @click="submitSearch"
        />
    </div>
</template>

<style scoped>
.search-bar {
    display: flex;
    align-items: center;
    gap: 0;
    padding: 0;
    background: var(--arches-search-hero-search-bg);
    border-radius: var(--arches-search-hero-search-radius);
    box-shadow: var(--arches-search-hero-search-shadow);
}

.search-bar .search-bar-inner {
    display: flex;
    align-items: center;
    flex: 1;
    gap: 1rem;
    padding-inline: 2rem 0;
    border: none;
    border-radius: var(--arches-search-hero-search-radius) 0 0
        var(--arches-search-hero-search-radius);
    background: transparent;
    transition:
        border-color 0.15s,
        box-shadow 0.15s;
}

.search-bar .search-bar-inner:focus-within {
    box-shadow: none;
}

.search-bar .search-input {
    flex: 1;
}

.search-bar :deep(.search-input .p-autocomplete-input) {
    border: none;
    box-shadow: none;
    padding: 1.4rem 0;
    font-size: 1.4rem;
    width: 100%;
    background-color: transparent;
    color: var(--p-text-color);
}

.search-bar :deep(.search-input .p-autocomplete-input::placeholder) {
    color: var(--p-text-muted-color, var(--p-surface-500));
}

.search-bar :deep(.search-input .p-autocomplete-input:focus),
.search-bar :deep(.search-input .p-autocomplete-input:focus-visible) {
    outline: none !important;
    box-shadow: none;
}

.search-bar .search-button {
    padding: 1.4rem 2.4rem;
    border-radius: 0 var(--arches-search-hero-search-radius)
        var(--arches-search-hero-search-radius) 0;
    font-size: var(--arches-search-hero-search-btn-font-size);
    font-weight: var(--arches-search-hero-search-btn-font-weight);
    white-space: nowrap;
}

.search-bar .search-button :deep(.p-button-icon) {
    display: inline-flex;
    align-items: center;
    font-size: 1.4rem;
}

.suggestion-tab-bar {
    display: flex;
    align-items: center;
    padding: 0.8rem 1rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--arches-search-page-bg);
}

.suggestion-tab-bar :deep(.p-tablist) {
    background: transparent;
    border-width: 0;
}

.suggestion-tab-bar :deep(.p-tablist-tab-list) {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    border: none;
}

.suggestion-tab-bar :deep(.p-tablist-active-bar) {
    display: none;
}

.suggestion-tab-bar :deep(.p-tab) {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 1rem;
    border-radius: var(--arches-search-radius-pill);
    font-size: 1.2rem;
    font-weight: 500;
    white-space: nowrap;
    cursor: pointer;
    border: 0.15rem solid var(--arches-search-chip-border);
    background: var(--p-content-background);
    color: var(--arches-search-sec-btn-text);
    font-family: inherit;
}

.suggestion-tab-bar :deep(.p-tab:hover) {
    background: var(--arches-search-sec-btn-hover-bg);
}

.suggestion-tab-bar :deep(.p-tab:focus-visible) {
    outline: 0.2rem solid var(--p-primary-color);
    outline-offset: 0.2rem;
}

.suggestion-tab-bar :deep(.p-tab-active) {
    background: var(--p-primary-color);
    border-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color, var(--p-surface-0));
}
</style>
