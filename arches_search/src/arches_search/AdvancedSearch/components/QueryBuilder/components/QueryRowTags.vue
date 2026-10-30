<script setup lang="ts">
import { computed, inject } from "vue";

import Tag from "openvue/tag";
import ToggleButton from "openvue/togglebutton";

import type { Ref } from "vue";
import type { GraphModel } from "@/arches_search/AdvancedSearch/types.ts";

const TOGGLE_NOT_EVENT = "toggle-not" as const;

const { graphSlug, badgeLabel, badgeIcon, badgeKind, isNegated } = defineProps<{
    graphSlug: string;
    badgeLabel: string;
    badgeIcon: string;
    badgeKind: string;
    isNegated: boolean;
}>();

const emit = defineEmits<{
    (event: typeof TOGGLE_NOT_EVENT): void;
}>();

const graphs = inject<Ref<GraphModel[]>>("graphs")!;

const graphName = computed<string>(
    () =>
        graphs.value.find((graph) => graph.slug === graphSlug)?.name ??
        graphSlug,
);

const badgeKindClass = computed<string>(
    () => `query-row-tags-badge-${badgeKind}`,
);
</script>

<template>
    <span class="query-row-tags">
        <Tag
            class="query-row-tags-model"
            icon="pi pi-database"
            :value="graphName"
            :rounded="true"
        />
        <Tag
            class="query-row-tags-badge"
            :class="badgeKindClass"
            :icon="badgeIcon"
            :value="badgeLabel"
            :rounded="true"
        />
        <ToggleButton
            class="query-row-tags-not"
            :model-value="isNegated"
            :on-label="$gettext('NOT')"
            :off-label="$gettext('NOT')"
            :title="$gettext('Match records where this is not true')"
            @update:model-value="emit(TOGGLE_NOT_EVENT)"
        />
    </span>
</template>

<style scoped>
.query-row-tags {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 0.6rem;
}

.query-row-tags .query-row-tags-model,
.query-row-tags .query-row-tags-badge {
    --p-tag-gap: 0.4rem;
    --p-tag-icon-size: 1rem;
    white-space: nowrap;
}

.query-row-tags .query-row-tags-model {
    --p-tag-primary-background: var(--arches-search-query-model-pill-bg);
    --p-tag-primary-color: var(--p-text-muted-color);
    --p-tag-padding: 0.3rem 0.8rem;
    --p-tag-font-size: 1rem;
    --p-tag-font-weight: 600;
    border: 0.1rem solid var(--arches-search-chip-border);
}

.query-row-tags .query-row-tags-badge {
    --p-tag-primary-background: var(--arches-search-chip-search-bg);
    --p-tag-primary-color: var(--arches-search-chip-search-text);
    --p-tag-padding: 0.4rem 1rem;
    --p-tag-font-size: 1.1rem;
    --p-tag-font-weight: 700;
}

.query-row-tags .query-row-tags-badge.query-row-tags-badge-attribute {
    --p-tag-primary-background: var(--arches-search-filter-attribute-bg);
    --p-tag-primary-color: var(--arches-search-filter-attribute-text);
}

.query-row-tags .query-row-tags-badge.query-row-tags-badge-time {
    --p-tag-primary-background: var(--arches-search-filter-time-bg);
    --p-tag-primary-color: var(--arches-search-filter-time-text);
}

.query-row-tags .query-row-tags-badge.query-row-tags-badge-map {
    --p-tag-primary-background: var(--arches-search-filter-map-bg);
    --p-tag-primary-color: var(--arches-search-filter-map-text);
}

.query-row-tags .query-row-tags-badge.query-row-tags-badge-related {
    --p-tag-primary-background: var(--arches-search-filter-related-bg);
    --p-tag-primary-color: var(--arches-search-filter-related-text);
}

.query-row-tags .query-row-tags-not {
    --p-togglebutton-padding: 0;
    --p-togglebutton-content-padding: 0.3rem 0.8rem;
    --p-togglebutton-content-checked-background: var(
        --arches-search-query-negate-bg
    );
    --p-togglebutton-content-checked-shadow: none;
    --p-togglebutton-checked-background: var(--arches-search-query-negate-bg);
    --p-togglebutton-checked-border-color: var(
        --arches-search-query-negate-border
    );
    --p-togglebutton-checked-color: var(--arches-search-query-negate-text);
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.04rem;
}
</style>
