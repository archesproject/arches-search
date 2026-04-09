<script setup lang="ts">
import { ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import AutoComplete from "primevue/autocomplete";
import type { AutoCompleteCompleteEvent } from "primevue/autocomplete";
import Button from "primevue/button";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import { fetchSearchTermSuggestions } from "@/arches_search/SimpleSearch/api.ts";

const { $gettext } = useGettext();

const props = defineProps<{
    config: Record<string, unknown>;
    filterKey: string;
}>();

const { setTerm, clearTerm, search } = useSearchFilters();

type Suggestion = { text: string; datatype: string; value: string };

const suggestions = ref<Suggestion[]>([]);

const selectedTerms = ref<Suggestion[]>([]);

const inputText = ref("");

function termKey(termValue: string) {
    return `${props.filterKey}:${termValue}`;
}

function removeTerm(termValue: string) {
    selectedTerms.value = selectedTerms.value.filter(
        (t) => t.value !== termValue,
    );
}

watch(
    selectedTerms,
    (val, prev) => {
        // clearTerm any terms that were removed
        const oldTerms = new Set(prev.map((t) => t.value));
        const newTerms = new Set(val.map((t) => t.value));
        for (const oldTerm of prev) {
            if (!newTerms.has(oldTerm.value)) clearTerm(termKey(oldTerm.value));
        }
        // Register any terms that were added
        for (const newTerm of val) {
            if (!oldTerms.has(newTerm.value)) {
                setTerm(
                    termKey(newTerm.value),
                    newTerm.value,
                    () => removeTerm(newTerm.value),
                    {
                        style: "background-color: var(--p-sky-500);",
                    },
                );
            }
        }
    },
    { deep: true },
);

async function onComplete(event: AutoCompleteCompleteEvent) {
    if (!event.query.trim()) {
        suggestions.value = [];
        return;
    }
    suggestions.value = await fetchSearchTermSuggestions(event.query);
}

function onSelect(event: { value: Suggestion }) {
    selectedTerms.value = [...selectedTerms.value, event.value];
    inputText.value = "";
}

function onKeydown(e: KeyboardEvent) {
    if (e.key === "Enter") search();
}
</script>

<template>
    <div class="search-bar">
        <span class="search-bar-inner">
            <i class="pi pi-search search-icon" />
            <AutoComplete
                v-model="inputText"
                :suggestions="suggestions"
                option-label="text"
                :placeholder="$gettext('Find an item, sample, supplier\u2026')"
                class="search-input"
                fluid
                @complete="onComplete"
                @item-select="onSelect"
                @keydown="onKeydown"
            >
                <template #option="{ option }">
                    <div class="suggestion-option">
                        <span
                            v-if="option.datatype === 'reference'"
                            class="suggestion-icon suggestion-icon--concept"
                            >C</span
                        >
                        <i
                            v-else-if="option.datatype === 'term'"
                            class="pi pi-hashtag suggestion-icon suggestion-icon--term"
                        />
                        <i
                            v-else
                            class="pi pi-search suggestion-icon suggestion-icon--string"
                        />
                        <div class="suggestion-content">
                            <span class="suggestion-label">{{
                                option.value
                            }}</span>
                            <span
                                v-if="
                                    option.addtional_info &&
                                    option.addtional_info.path &&
                                    option.addtional_info.path.length > 0
                                "
                                class="suggestion-path"
                                >{{
                                    option.addtional_info.path.join(" > ")
                                }}</span
                            >
                        </div>
                    </div>
                </template>
            </AutoComplete>
        </span>
        <Button
            :label="$gettext('Search')"
            class="search-button"
            @click="() => search()"
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

.search-bar-inner {
    display: flex;
    align-items: center;
    flex: 1;
    border: 0.125rem solid var(--p-surface-300);
    border-radius: 0.4rem;
    padding: 0 1rem;
}

.search-icon {
    font-size: var(--p-arches-search-font-size);
    margin-right: 0.8rem;
    flex-shrink: 0;
}

.search-input {
    flex: 1;
}

:deep(.search-input .p-autocomplete-input) {
    border: none;
    box-shadow: none;
    padding: 1rem 2rem;
    font-size: var(--p-arches-search-font-size);
    width: 100%;
    background-color: var(--p-content-background);
}

:deep(.search-input .p-autocomplete-input:focus) {
    outline: none;
    box-shadow: none;
}

.search-button {
    font-size: var(--p-arches-search-font-size);
    padding: 1rem 2rem;
    border-radius: 0.4rem;
    white-space: nowrap;
}

.suggestion-option {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
}

.suggestion-icon {
    flex-shrink: 0;
    width: 1.75rem;
    height: 1.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    font-size: 0.8rem;
    font-weight: 700;
    margin-top: 0.1rem;
}

.suggestion-icon--concept {
    background-color: var(--p-primary-color);
    color: white;
}

.suggestion-icon--term {
    background-color: var(--p-surface-200);
    color: var(--p-surface-700);
}

.suggestion-icon--string {
    background-color: var(--p-surface-200);
    color: var(--p-surface-700);
}

.suggestion-content {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.suggestion-label {
    font-weight: 500;
    color: var(--p-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.suggestion-path {
    font-size: 1.1rem;
    color: var(--p-text-muted-color, var(--p-surface-500));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
