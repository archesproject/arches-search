<script setup lang="ts">
import { ref } from "vue";
import { useGettext } from "vue3-gettext";

import AutoComplete from "primevue/autocomplete";
import type { AutoCompleteCompleteEvent } from "primevue/autocomplete";
import Button from "primevue/button";

import { fetchSearchTermSuggestions } from "@/arches_search/SimpleSearch/api.ts";

const { $gettext } = useGettext();

const props = defineProps<{
    modelValue: string;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", value: string): void;
    (event: "search", term: string): void;
}>();

const suggestions = ref<Array<{ text: string; type: string; value: string }>>(
    [],
);

async function onComplete(event: AutoCompleteCompleteEvent) {
    if (!event.query.trim()) {
        suggestions.value = [];
        return;
    }
    suggestions.value = await fetchSearchTermSuggestions(event.query);
}

function onSearch() {
    emit("search", props.modelValue);
}

function onSelect(event: { value: { text: string } }) {
    emit("update:modelValue", event.value.text);
    emit("search", event.value.text);
}

function onKeydown(e: KeyboardEvent) {
    if (e.key === "Enter") onSearch();
}
</script>

<template>
    <div class="search-bar">
        <span class="search-bar-inner">
            <i class="pi pi-search search-icon" />
            <AutoComplete
                :model-value="modelValue"
                :suggestions="suggestions"
                option-label="text"
                :placeholder="$gettext('Find an item, sample, supplier\u2026')"
                class="search-input"
                fluid
                @update:model-value="$emit('update:modelValue', $event)"
                @complete="onComplete"
                @item-select="onSelect"
                @keydown="onKeydown"
            >
                <template #option="{ option }">
                    <span>{{ option.text }}</span>
                </template>
            </AutoComplete>
        </span>
        <Button
            :label="$gettext('Search')"
            class="search-button"
            @click="onSearch"
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
</style>
