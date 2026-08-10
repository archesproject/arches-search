<script setup lang="ts">
import { computed } from "vue";

import {
    getHighlightSegments,
    getSuggestionPath,
    isConceptSuggestion,
} from "@/arches_search/SimpleSearch/components/TermFilter/suggestion-utils.ts";

import type { TermSuggestion } from "@/arches_search/SimpleSearch/types.ts";

const { suggestion, query } = defineProps<{
    suggestion: TermSuggestion;
    query: string;
}>();

const isConcept = computed(() => isConceptSuggestion(suggestion));

const highlightSegments = computed(() =>
    getHighlightSegments(suggestion.text, query),
);

const suggestionPath = computed(() => getSuggestionPath(suggestion));
</script>

<template>
    <div
        class="suggestion-option"
        :class="{ 'suggestion-option--vocab': isConcept }"
    >
        <span
            v-if="isConcept"
            class="suggestion-icon suggestion-icon--concept"
        >
            C
        </span>
        <i
            v-else
            :class="[
                'suggestion-icon',
                'suggestion-icon--record',
                suggestion.graph_icon || 'pi pi-search',
            ]"
        />

        <div
            class="suggestion-content"
            :class="{ 'suggestion-content--record': !isConcept }"
        >
            <span
                class="suggestion-label"
                :class="{ 'suggestion-label--record': !isConcept }"
            >
                <template
                    v-for="(segment, segmentIndex) in highlightSegments"
                    :key="segmentIndex"
                >
                    <mark v-if="segment.matched">{{ segment.text }}</mark>
                    <span v-else>{{ segment.text }}</span>
                </template>
            </span>
            <span
                v-if="isConcept && suggestionPath"
                class="suggestion-path"
            >
                {{ suggestionPath }}
            </span>
            <span
                v-else-if="!isConcept && suggestion.graph_name"
                class="suggestion-type"
            >
                {{ suggestion.graph_name }}
            </span>
        </div>
    </div>
</template>

<style scoped>
.suggestion-option {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
}

.suggestion-option--vocab {
    align-items: flex-start;
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
    margin-block-start: 0.1rem;
}

.suggestion-icon--concept {
    background-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color, var(--p-surface-0));
}

.suggestion-icon--record {
    background-color: var(--p-surface-200);
    color: var(--p-surface-700);
}

.suggestion-content {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.suggestion-content--record {
    flex-direction: row;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
}

.suggestion-label {
    font-weight: 500;
    font-size: 1.3rem;
    color: var(--p-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.suggestion-label--record {
    flex: 1;
    min-width: 0;
}

.suggestion-label mark {
    background: none;
    color: var(--p-primary-color);
    font-weight: 700;
}

.suggestion-type {
    font-size: 1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04rem;
    color: var(--p-text-muted-color, var(--p-surface-500));
    flex-shrink: 0;
    white-space: nowrap;
    margin-inline-start: auto;
}

.suggestion-path {
    font-size: 1.1rem;
    color: var(--p-text-muted-color, var(--p-surface-500));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
