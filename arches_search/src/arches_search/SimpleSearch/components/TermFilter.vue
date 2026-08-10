<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import AutoComplete from "primevue/autocomplete";
import Button from "primevue/button";

import { fetchSearchTermSuggestions } from "@/arches_search/SimpleSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type { AutoCompleteCompleteEvent } from "primevue/autocomplete";
import {
    TERM_KIND_CONTROLLED_TERM,
    TERM_KIND_RECORD,
} from "@/arches_search/SimpleSearch/types.ts";
import type {
    TermKind,
    TermSuggestion,
} from "@/arches_search/SimpleSearch/types.ts";

interface TermSuggestionSelectEvent {
    value: TermSuggestion;
}

interface TermSuggestionAdditionalInfo {
    path?: unknown;
}

const props = defineProps<{
    filterKey: string;
}>();

const { $gettext } = useGettext();
const { setTermFilter, clearTermFilter } = useSearchFilters();

type TypeaheadPanel = "records" | "vocab";

interface HighlightSegment {
    text: string;
    matched: boolean;
}

const suggestions = ref<Array<TermSuggestion>>([]);
const selectedTerms = ref<Array<TermSuggestion>>([]);
const inputText = ref("");
const isOverlayShown = ref(false);
const hasSuggestionLoadError = ref(false);
const typeaheadPanel = ref<TypeaheadPanel>("records");
const recordsTabButton = ref<HTMLButtonElement | null>(null);
const vocabTabButton = ref<HTMLButtonElement | null>(null);

let latestSuggestionRequestId = 0;

const emptySearchMessage = computed(() =>
    hasSuggestionLoadError.value
        ? $gettext("Search suggestions are unavailable.")
        : undefined,
);

const recordSuggestions = computed<Array<TermSuggestion>>(() =>
    suggestions.value.filter(
        (suggestion) => suggestion.datatype !== "reference",
    ),
);

const vocabSuggestions = computed<Array<TermSuggestion>>(() =>
    suggestions.value.filter(
        (suggestion) => suggestion.datatype === "reference",
    ),
);

const activeSuggestions = computed<Array<TermSuggestion>>(() =>
    typeaheadPanel.value === "records"
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
                datatype: "string",
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
    typeaheadPanel.value = "records";
}

function isConceptSuggestion(suggestion: TermSuggestion): boolean {
    return suggestion.datatype === "reference";
}

function getTermKind(suggestion: TermSuggestion): TermKind | undefined {
    if (isConceptSuggestion(suggestion)) {
        return TERM_KIND_CONTROLLED_TERM;
    }
    if (suggestion.resourceinstanceid) {
        return TERM_KIND_RECORD;
    }
    return undefined;
}

function escapeRegExp(value: string): string {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function getHighlightSegments(text: string, query: string): HighlightSegment[] {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
        return [{ text, matched: false }];
    }

    const matchPattern = new RegExp(`(${escapeRegExp(trimmedQuery)})`, "gi");
    return text
        .split(matchPattern)
        .map((segment, index) => ({ text: segment, matched: index % 2 === 1 }))
        .filter((segment) => segment.text !== "");
}

function switchTypeaheadPanel(panel: TypeaheadPanel): void {
    typeaheadPanel.value = panel;
}

function handleTabChipKeydown(
    event: KeyboardEvent,
    currentPanel: TypeaheadPanel,
): void {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
        return;
    }

    event.preventDefault();
    const nextPanel: TypeaheadPanel =
        currentPanel === "records" ? "vocab" : "records";
    switchTypeaheadPanel(nextPanel);
    (nextPanel === "records"
        ? recordsTabButton
        : vocabTabButton
    ).value?.focus();
}

function getNoResultsMessage(): string {
    return typeaheadPanel.value === "records"
        ? $gettext("No matching records for “%{query}”", {
              query: inputText.value,
          })
        : $gettext("No matching controlled terms for “%{query}”", {
              query: inputText.value,
          });
}

function getSuggestionPath(suggestion: TermSuggestion): string | null {
    const additionalInfo = suggestion.addtional_info as
        | TermSuggestionAdditionalInfo
        | undefined;
    const suggestionPath = additionalInfo?.path;

    if (
        !Array.isArray(suggestionPath) ||
        suggestionPath.length === 0 ||
        !suggestionPath.every((pathItem) => typeof pathItem === "string")
    ) {
        return null;
    }

    return suggestionPath.join(" > ");
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
                scroll-height="32.2581rem"
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
                        <button
                            ref="recordsTabButton"
                            type="button"
                            class="suggestion-tab-chip"
                            :class="{ active: typeaheadPanel === 'records' }"
                            @mousedown.prevent
                            @click="switchTypeaheadPanel('records')"
                            @keydown="handleTabChipKeydown($event, 'records')"
                        >
                            <i class="pi pi-database"></i>
                            {{
                                $gettext("Records (%{count})", {
                                    count: String(recordSuggestions.length),
                                })
                            }}
                        </button>
                        <button
                            ref="vocabTabButton"
                            type="button"
                            class="suggestion-tab-chip"
                            :class="{ active: typeaheadPanel === 'vocab' }"
                            @mousedown.prevent
                            @click="switchTypeaheadPanel('vocab')"
                            @keydown="handleTabChipKeydown($event, 'vocab')"
                        >
                            <i class="pi pi-tag"></i>
                            {{
                                $gettext("Controlled Terms (%{count})", {
                                    count: String(vocabSuggestions.length),
                                })
                            }}
                        </button>
                    </div>
                </template>

                <template #option="{ option }">
                    <div
                        class="suggestion-option"
                        :class="{
                            'suggestion-option--vocab':
                                isConceptSuggestion(option),
                        }"
                    >
                        <span
                            v-if="isConceptSuggestion(option)"
                            class="suggestion-icon suggestion-icon--concept"
                        >
                            C
                        </span>
                        <i
                            v-else
                            :class="[
                                'suggestion-icon',
                                'suggestion-icon--record',
                                option.graph_icon || 'pi pi-search',
                            ]"
                        />

                        <div
                            v-if="isConceptSuggestion(option)"
                            class="suggestion-content"
                        >
                            <span class="suggestion-label">
                                <template
                                    v-for="(
                                        segment, segmentIndex
                                    ) in getHighlightSegments(
                                        option.text,
                                        inputText,
                                    )"
                                    :key="segmentIndex"
                                >
                                    <mark v-if="segment.matched">{{
                                        segment.text
                                    }}</mark>
                                    <span v-else>{{ segment.text }}</span>
                                </template>
                            </span>
                            <span
                                v-if="getSuggestionPath(option)"
                                class="suggestion-path"
                            >
                                {{ getSuggestionPath(option) }}
                            </span>
                        </div>
                        <template v-else>
                            <span
                                class="suggestion-label suggestion-label--record"
                            >
                                <template
                                    v-for="(
                                        segment, segmentIndex
                                    ) in getHighlightSegments(
                                        option.text,
                                        inputText,
                                    )"
                                    :key="segmentIndex"
                                >
                                    <mark v-if="segment.matched">{{
                                        segment.text
                                    }}</mark>
                                    <span v-else>{{ segment.text }}</span>
                                </template>
                            </span>
                            <span
                                v-if="option.graph_name"
                                class="suggestion-type"
                            >
                                {{ option.graph_name }}
                            </span>
                        </template>
                    </div>
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
    gap: 1.0081rem;
    padding: 1.2rem 1.6rem;
    background-color: var(--p-content-background);
}

.search-bar .search-icon {
    font-size: 1.5121rem;
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
    padding: 1.2097rem 0;
    font-size: 1.4113rem;
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
    border-width: 0.1512rem;
    border-radius: 0.8065rem;
    box-shadow:
        0 0.8065rem 2.4194rem rgba(0, 0, 0, 0.12),
        0 0.2016rem 0.6048rem rgba(0, 0, 0, 0.07);
    max-width: 80vw;
    margin-inline-start: calc(-1 * (0.1512rem + 1.4rem + 1.5121rem + 1rem));
}

.search-bar :deep(.term-filter-overlay .p-autocomplete-list) {
    gap: 0;
    padding: 0;
}

.search-bar :deep(.term-filter-overlay .p-autocomplete-option) {
    border-radius: 0;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    padding: 0.8065rem 1.4113rem;
}

.search-bar :deep(.term-filter-overlay .p-autocomplete-option:last-child) {
    border-block-end: none;
}

.search-bar :deep(.term-filter-overlay .p-autocomplete-option:hover),
.search-bar :deep(.term-filter-overlay .p-autocomplete-option.p-focus) {
    background: var(--p-highlight-background) !important;
}

.search-bar :deep(.term-filter-overlay .p-autocomplete-empty-message) {
    padding: 1.2097rem 1.4113rem;
    font-size: 1.3105rem;
    color: var(--p-text-muted-color, var(--p-surface-500));
    text-align: center;
}

.search-bar .suggestion-option {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
}

.search-bar .suggestion-option--vocab {
    align-items: flex-start;
}

.search-bar .suggestion-icon {
    flex-shrink: 0;
    width: 1.75rem;
    height: 1.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    font-size: 0.8rem;
    font-weight: 700;
    margin-block-start: 0.1rem;
}

.search-bar .suggestion-icon--concept {
    background-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color, var(--p-surface-0));
}

.search-bar .suggestion-icon--record {
    background-color: var(--p-surface-200);
    color: var(--p-surface-700);
}

.search-bar .suggestion-content {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.search-bar .suggestion-label {
    font-weight: 500;
    font-size: 1.3105rem;
    color: var(--p-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.search-bar .suggestion-label--record {
    flex: 1;
    min-width: 0;
}

.search-bar .suggestion-label mark {
    background: none;
    color: var(--p-primary-color);
    font-weight: 700;
}

.search-bar .suggestion-type {
    font-size: 1.0081rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--p-text-muted-color, var(--p-surface-500));
    flex-shrink: 0;
    white-space: nowrap;
    margin-inline-start: auto;
}

.search-bar .suggestion-tab-bar {
    display: flex;
    align-items: center;
    gap: 0.6048rem;
    padding: 0.8065rem 1.0081rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--arches-search-page-bg);
}

.search-bar .suggestion-tab-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.504rem;
    padding: 0.4032rem 1.0081rem;
    border-radius: 999rem;
    font-size: 1.2097rem;
    font-weight: 500;
    white-space: nowrap;
    cursor: pointer;
    border: 0.1512rem solid var(--arches-search-chip-border);
    background: var(--p-content-background);
    color: var(--arches-search-sec-btn-text);
    font-family: inherit;
}

.search-bar .suggestion-tab-chip:hover {
    background: var(--arches-search-sec-btn-hover-bg);
}

.search-bar .suggestion-tab-chip:focus-visible {
    outline: 0.2016rem solid var(--p-primary-color);
    outline-offset: 0.2016rem;
}

.search-bar .suggestion-tab-chip.active {
    background: var(--p-primary-color);
    border-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color, var(--p-surface-0));
}

.search-bar .suggestion-path {
    font-size: 1.1rem;
    color: var(--p-text-muted-color, var(--p-surface-500));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
