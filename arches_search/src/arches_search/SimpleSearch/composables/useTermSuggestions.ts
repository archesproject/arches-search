import { computed, onMounted, ref, useTemplateRef } from "vue";
import { useGettext } from "vue3-gettext";

import AutoComplete from "primevue/autocomplete";

import { fetchSearchTermSuggestions } from "@/arches_search/SimpleSearch/api.ts";
import { SUGGESTION_DATATYPE_STRING } from "@/arches_search/SimpleSearch/components/TermFilter/constants.ts";
import { isConceptSuggestion } from "@/arches_search/SimpleSearch/components/TermFilter/suggestion-utils.ts";

import type { AutoCompleteCompleteEvent } from "primevue/autocomplete";
import type { TermSuggestion } from "@/arches_search/SimpleSearch/types.ts";

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

export function useTermSuggestions() {
    const { $gettext } = useGettext();

    const autoCompleteRef =
        useTemplateRef<InstanceType<typeof AutoComplete>>("autoCompleteRef");

    const inputText = ref("");
    const suggestions = ref<Array<TermSuggestion>>([]);
    const suggestionsQuery = ref<string | null>(null);
    const hasSuggestionLoadError = ref(false);
    const isOverlayShown = ref(false);
    const typeaheadPanel = ref<TypeaheadPanel>(TYPEAHEAD_PANEL_RECORDS);

    let latestSuggestionRequestId = 0;

    const emptySearchMessage = computed(() => {
        if (hasSuggestionLoadError.value) {
            return $gettext("Search suggestions are unavailable.");
        }
        return undefined;
    });

    const recordSuggestions = computed<Array<TermSuggestion>>(() =>
        suggestions.value.filter(
            (suggestion) => !isConceptSuggestion(suggestion),
        ),
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

    const activeSuggestions = computed<Array<TermSuggestion>>(() => {
        if (typeaheadPanel.value === TYPEAHEAD_PANEL_RECORDS) {
            return recordSuggestions.value;
        }
        return vocabSuggestions.value;
    });

    onMounted(() => {
        const autoCompleteElement = autoCompleteRef.value as unknown as {
            $el?: HTMLElement;
        } | null;

        autoCompleteElement?.$el
            ?.querySelector<HTMLInputElement>("input")
            ?.focus();
    });

    function stopStrayLoadingIndicator(): void {
        if (autoCompleteRef.value) {
            (
                autoCompleteRef.value as unknown as { searching: boolean }
            ).searching = false;
        }
    }

    async function onComplete(event: AutoCompleteCompleteEvent): Promise<void> {
        const trimmedQuery = event.query.trim();

        if (trimmedQuery !== inputText.value.trim()) {
            stopStrayLoadingIndicator();
            return;
        }

        const requestId = ++latestSuggestionRequestId;

        if (!trimmedQuery) {
            suggestions.value = [];
            suggestionsQuery.value = null;
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
            suggestionsQuery.value = trimmedQuery;
        } catch (error) {
            if (requestId !== latestSuggestionRequestId) {
                return;
            }
            console.error(error);
            suggestions.value = [];
            suggestionsQuery.value = null;
            hasSuggestionLoadError.value = true;
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
        if (typeaheadPanel.value === TYPEAHEAD_PANEL_RECORDS) {
            return $gettext("No matching records for “%{query}”", {
                query: inputText.value,
            });
        }
        return $gettext("No matching controlled terms for “%{query}”", {
            query: inputText.value,
        });
    }

    function resolveSubmitCandidate(): TermSuggestion | null {
        const trimmedInputText = inputText.value.trim();
        const suggestionsMatchInput =
            suggestionsQuery.value === trimmedInputText;

        if (suggestionsMatchInput && suggestions.value.length > 1) {
            return suggestions.value[0];
        }

        if (trimmedInputText) {
            return {
                id: Date.now(),
                datatype: SUGGESTION_DATATYPE_STRING,
                text: trimmedInputText,
            };
        }

        return null;
    }

    function markSuggestionHandled(): void {
        suggestionsQuery.value = null;
        latestSuggestionRequestId += 1;
        stopStrayLoadingIndicator();
    }

    return {
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
    };
}
