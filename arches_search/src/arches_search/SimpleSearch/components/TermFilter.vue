<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import AutoComplete from "primevue/autocomplete";
import Button from "primevue/button";

import { fetchSearchTermSuggestions } from "@/arches_search/SimpleSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type { AutoCompleteCompleteEvent } from "primevue/autocomplete";
import type { TermSuggestion } from "@/arches_search/SimpleSearch/types.ts";

interface TermSuggestionSelectEvent {
    value: TermSuggestion;
}

interface TermSuggestionAdditionalInfo {
    path?: unknown;
}

const props = defineProps<{
    config: Record<string, unknown>;
    filterKey: string;
}>();

const { $gettext } = useGettext();
const { setTermFilter, clearTermFilter } = useSearchFilters();

const suggestions = ref<Array<TermSuggestion>>([]);
const selectedTerms = ref<Array<TermSuggestion>>([]);
const inputText = ref("");
const isOverlayShown = ref(false);
const hasSuggestionLoadError = ref(false);

const emptySearchMessage = computed(() =>
    hasSuggestionLoadError.value
        ? $gettext("Search suggestions are unavailable.")
        : undefined,
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
                setTermFilter(
                    termKey(selectedTerm.text),
                    selectedTerm.text,
                    () => removeTerm(selectedTerm.text),
                    {
                        style: "background-color: var(--p-sky-500);",
                    },
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

    if (!trimmedQuery) {
        suggestions.value = [];
        hasSuggestionLoadError.value = false;
        return;
    }

    try {
        hasSuggestionLoadError.value = false;
        suggestions.value = await fetchSearchTermSuggestions(trimmedQuery);
    } catch (error) {
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
}

function isConceptSuggestion(suggestion: TermSuggestion): boolean {
    return suggestion.datatype === "reference";
}

function isTermSuggestion(suggestion: TermSuggestion): boolean {
    return suggestion.datatype === "term";
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
            <i class="pi pi-search search-icon" />
            <AutoComplete
                v-model="inputText"
                class="search-input"
                option-label="text"
                :auto-option-focus="true"
                :empty-search-message="emptySearchMessage"
                :fluid="true"
                :placeholder="$gettext('Find an item, sample, supplier\u2026')"
                :suggestions="suggestions"
                @complete="onComplete"
                @option-select="onSelect"
                @keydown="onKeydown"
                @before-show="showOverlay"
                @before-hide="hideOverlay"
            >
                <template #option="{ option }">
                    <div class="suggestion-option">
                        <span
                            v-if="isConceptSuggestion(option)"
                            class="suggestion-icon suggestion-icon--concept"
                        >
                            C
                        </span>
                        <i
                            v-else-if="isTermSuggestion(option)"
                            class="pi pi-hashtag suggestion-icon suggestion-icon--term"
                        />
                        <i
                            v-else
                            class="pi pi-search suggestion-icon suggestion-icon--string"
                        />
                        <div class="suggestion-content">
                            <span class="suggestion-label">
                                {{ option.text }}
                            </span>
                            <span
                                v-if="getSuggestionPath(option)"
                                class="suggestion-path"
                            >
                                {{ getSuggestionPath(option) }}
                            </span>
                        </div>
                    </div>
                </template>
            </AutoComplete>
        </span>
        <Button
            :label="$gettext('Search')"
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
    gap: 0.8rem;
    padding: 1.2rem 1.6rem;
    background-color: var(--p-content-background);
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.search-bar .search-bar-inner {
    display: flex;
    align-items: center;
    flex: 1;
    border: 0.125rem solid var(--p-surface-300);
    border-radius: 0.4rem;
    padding: 0 1rem;
}

.search-bar .search-icon {
    font-size: var(--p-arches-search-font-size);
    margin-inline-end: 0.8rem;
    flex-shrink: 0;
}

.search-bar .search-input {
    flex: 1;
}

.search-bar :deep(.search-input .p-autocomplete-input) {
    border: none;
    box-shadow: none;
    padding: 1rem 2rem;
    font-size: var(--p-arches-search-font-size);
    width: 100%;
    background-color: var(--p-content-background);
}

.search-bar :deep(.search-input .p-autocomplete-input:focus) {
    outline: none;
    box-shadow: none;
}

.search-bar .search-button {
    font-size: var(--p-arches-search-font-size);
    padding: 1rem 2rem;
    border-radius: 0.4rem;
    white-space: nowrap;
}

.search-bar .suggestion-option {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
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

.search-bar .suggestion-icon--term {
    background-color: var(--p-surface-200);
    color: var(--p-surface-700);
}

.search-bar .suggestion-icon--string {
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
    color: var(--p-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.search-bar .suggestion-path {
    font-size: 1.1rem;
    color: var(--p-text-muted-color, var(--p-surface-500));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
