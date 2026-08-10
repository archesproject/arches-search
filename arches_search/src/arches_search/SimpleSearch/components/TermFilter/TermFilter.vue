<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import AutoComplete from "primevue/autocomplete";
import Button from "primevue/button";
import Tab from "primevue/tab";
import TabList from "primevue/tablist";
import Tabs from "primevue/tabs";

import { fetchSearchTermSuggestions } from "@/arches_search/SimpleSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import SuggestionOption from "@/arches_search/SimpleSearch/components/TermFilter/components/SuggestionOption.vue";
import {
    SUGGESTION_DATATYPE_STRING,
    getTermKind,
    isConceptSuggestion,
} from "@/arches_search/SimpleSearch/components/TermFilter/suggestion-utils.ts";

import type { AutoCompleteCompleteEvent } from "primevue/autocomplete";
import { TERM_KIND_RECORD } from "@/arches_search/SimpleSearch/types.ts";
import type { TermSuggestion } from "@/arches_search/SimpleSearch/types.ts";

interface TermSuggestionSelectEvent {
    value: TermSuggestion;
}

const props = defineProps<{
    filterKey: string;
}>();

const { $gettext } = useGettext();
const { setTermFilter, clearTermFilter } = useSearchFilters();

const TYPEAHEAD_PANEL_RECORDS = "records";
const TYPEAHEAD_PANEL_VOCAB = "vocab";

type TypeaheadPanel =
    | typeof TYPEAHEAD_PANEL_RECORDS
    | typeof TYPEAHEAD_PANEL_VOCAB;

interface TypeaheadPanelDefinition {
    id: TypeaheadPanel;
    icon: string;
    label: string;
}

const suggestions = ref<Array<TermSuggestion>>([]);
const selectedTerms = ref<Array<TermSuggestion>>([]);
const inputText = ref("");
const isOverlayShown = ref(false);
const hasSuggestionLoadError = ref(false);
const typeaheadPanel = ref<TypeaheadPanel>(TYPEAHEAD_PANEL_RECORDS);

let latestSuggestionRequestId = 0;

const emptySearchMessage = computed(() =>
    hasSuggestionLoadError.value
        ? $gettext("Search suggestions are unavailable.")
        : undefined,
);

const recordSuggestions = computed<Array<TermSuggestion>>(() =>
    suggestions.value.filter((suggestion) => !isConceptSuggestion(suggestion)),
);

const vocabSuggestions = computed<Array<TermSuggestion>>(() =>
    suggestions.value.filter(isConceptSuggestion),
);

const typeaheadPanels = computed<TypeaheadPanelDefinition[]>(() => [
    {
        id: TYPEAHEAD_PANEL_RECORDS,
        icon: "pi pi-database",
        label: $gettext("Records (%{count})", {
            count: String(recordSuggestions.value.length),
        }),
    },
    {
        id: TYPEAHEAD_PANEL_VOCAB,
        icon: "pi pi-tag",
        label: $gettext("Controlled Terms (%{count})", {
            count: String(vocabSuggestions.value.length),
        }),
    },
]);

const activeSuggestions = computed<Array<TermSuggestion>>(() =>
    typeaheadPanel.value === TYPEAHEAD_PANEL_RECORDS
        ? recordSuggestions.value
        : vocabSuggestions.value,
);

watch(
    selectedTerms,
    (selectedTermValues, previousSelectedTerms) => {
        const previousTermTexts = new Set(
            previousSelectedTerms.map((term) => term.text),
        );
        const selectedTermTexts = new Set(
            selectedTermValues.map((term) => term.text),
        );

        for (const previousTerm of previousSelectedTerms) {
            if (!selectedTermTexts.has(previousTerm.text)) {
                clearTermFilter(termKey(previousTerm.text));
            }
        }

        for (const selectedTerm of selectedTermValues) {
            if (!previousTermTexts.has(selectedTerm.text)) {
                const termKind = getTermKind(selectedTerm);
                const isRecordTerm = termKind === TERM_KIND_RECORD;
                setTermFilter(
                    termKey(selectedTerm.text),
                    selectedTerm.text,
                    () => removeTerm(selectedTerm.text),
                    undefined,
                    termKind,
                    isRecordTerm ? selectedTerm.graph_icon : undefined,
                );
            }
        }
    },
    { deep: true },
);

function termKey(termValue: string): string {
    return `${props.filterKey}:${termValue}`;
}

function removeTerm(termValue: string): void {
    selectedTerms.value = selectedTerms.value.filter(
        (term) => term.text !== termValue,
    );
}

async function onComplete(event: AutoCompleteCompleteEvent): Promise<void> {
    const trimmedQuery = event.query.trim();
    const requestId = ++latestSuggestionRequestId;

    if (!trimmedQuery) {
        suggestions.value = [];
        hasSuggestionLoadError.value = false;
        return;
    }

    try {
        hasSuggestionLoadError.value = false;
        const results = await fetchSearchTermSuggestions(trimmedQuery);
        if (requestId !== latestSuggestionRequestId) {
            return;
        }
        suggestions.value = results;
    } catch (error) {
        if (requestId !== latestSuggestionRequestId) {
            return;
        }
        console.error(error);
        suggestions.value = [];
        hasSuggestionLoadError.value = true;
    }
}

function onSelect(event: TermSuggestionSelectEvent): void {
    selectedTerms.value = [...selectedTerms.value, event.value];
    inputText.value = "";
}

function onKeydown(event: KeyboardEvent): void {
    if (event.key !== "Enter" || isOverlayShown.value) {
        return;
    }

    submitSearch();
}

function submitSearch(): void {
    const trimmedInputText = inputText.value.trim();

    if (suggestions.value.length > 1) {
        onSelect({ value: suggestions.value[0] });
        return;
    }

    if (trimmedInputText) {
        onSelect({
            value: {
                id: Date.now(),
                datatype: SUGGESTION_DATATYPE_STRING,
                text: trimmedInputText,
            },
        });
    }
}

function showOverlay(): void {
    isOverlayShown.value = true;
}

function hideOverlay(): void {
    isOverlayShown.value = false;
    typeaheadPanel.value = TYPEAHEAD_PANEL_RECORDS;
}

function getNoResultsMessage(): string {
    return typeaheadPanel.value === TYPEAHEAD_PANEL_RECORDS
        ? $gettext("No matching records for “%{query}”", {
              query: inputText.value,
          })
        : $gettext("No matching controlled terms for “%{query}”", {
              query: inputText.value,
          });
}
</script>

<template>
    <div class="search-bar">
        <span class="search-bar-inner">
            <i
                aria-hidden="true"
                class="pi pi-search search-icon"
            ></i>
            <AutoComplete
                v-model="inputText"
                class="search-input"
                overlay-class="term-filter-overlay"
                option-label="text"
                scroll-height="32rem"
                append-to="self"
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
                                    <i :class="panel.icon"></i>
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
    gap: 1rem;
    padding: 1.2rem 1.6rem;
    background-color: var(--p-content-background);
}

.search-bar .search-icon {
    font-size: 1.5rem;
    color: var(--p-text-muted-color, var(--p-surface-500));
    flex-shrink: 0;
}

.search-bar .search-bar-inner {
    display: flex;
    align-items: center;
    flex: 1;
    max-width: 40%;
    gap: 1rem;
    background-color: var(--arches-search-page-bg);
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 0.8rem;
    padding: 0 1.4rem;
    transition:
        border-color 0.15s,
        box-shadow 0.15s;
}

@media (max-width: 900px) {
    .search-bar .search-bar-inner {
        max-width: 100%;
    }
}

.search-bar .search-bar-inner:focus-within {
    border-color: var(--p-primary-color);
    box-shadow: 0 0 0 0.3rem var(--p-primary-100);
}

.search-bar .search-input {
    flex: 1;
}

.search-bar :deep(.search-input .p-autocomplete-input) {
    border: none;
    box-shadow: none;
    padding: 1.2rem 0;
    font-size: 1.4rem;
    width: 100%;
    background-color: transparent;
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
    font-size: var(--p-arches-search-font-size);
    font-weight: 700;
    padding: 1rem 2rem;
    border-radius: 0.8rem;
    white-space: nowrap;
}

.search-bar .search-button :deep(.p-button-icon) {
    display: inline-flex;
    align-items: center;
    font-size: 1.4rem;
}

.search-bar :deep(.term-filter-overlay) {
    overflow: hidden;
    border-width: 0.15rem;
    border-radius: 0.8rem;
    box-shadow:
        0 0.8rem 2.4rem rgba(0, 0, 0, 0.12),
        0 0.2rem 0.6rem rgba(0, 0, 0, 0.07);
    max-width: 80vw;
    margin-inline-start: -4.05rem;
}

.search-bar :deep(.term-filter-overlay .p-autocomplete-list) {
    gap: 0;
    padding: 0;
}

.search-bar :deep(.term-filter-overlay .p-autocomplete-option) {
    border-radius: 0;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    padding: 0.8rem 1.4rem;
}

.search-bar :deep(.term-filter-overlay .p-autocomplete-option:last-child) {
    border-block-end: none;
}

.search-bar :deep(.term-filter-overlay .p-autocomplete-option:hover),
.search-bar :deep(.term-filter-overlay .p-autocomplete-option.p-focus) {
    background: var(--p-highlight-background) !important;
}

.search-bar :deep(.term-filter-overlay .p-autocomplete-empty-message) {
    padding: 1.2rem 1.4rem;
    font-size: 1.3rem;
    color: var(--p-text-muted-color, var(--p-surface-500));
    text-align: center;
}

.search-bar .suggestion-tab-bar {
    display: flex;
    align-items: center;
    padding: 0.8rem 1rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--arches-search-page-bg);
}

.search-bar .suggestion-tab-bar :deep(.p-tablist-tab-list) {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.search-bar .suggestion-tab-bar :deep(.p-tablist-active-bar) {
    display: none;
}

.search-bar .suggestion-tab-bar :deep(.p-tab) {
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

.search-bar .suggestion-tab-bar :deep(.p-tab:hover) {
    background: var(--arches-search-sec-btn-hover-bg);
}

.search-bar .suggestion-tab-bar :deep(.p-tab:focus-visible) {
    outline: 0.2rem solid var(--p-primary-color);
    outline-offset: 0.2rem;
}

.search-bar .suggestion-tab-bar :deep(.p-tab-active) {
    background: var(--p-primary-color);
    border-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color, var(--p-surface-0));
}
</style>
