<script setup lang="ts">
import { computed } from "vue";

import Button from "openvue/button";

import QuerySelectCheckbox from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QuerySelectCheckbox.vue";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";

const { itemId } = defineProps<{
    itemId: string;
}>();

const queryBuilder = useQueryBuilder();
const { selectedItemIds } = queryBuilder;

const isSelected = computed<boolean>(() =>
    selectedItemIds.value.includes(itemId),
);

function onRemove(): void {
    queryBuilder.removeItem(itemId);
}
</script>

<template>
    <div
        class="query-read-only-item"
        :class="{ 'query-read-only-item-selected': isSelected }"
    >
        <QuerySelectCheckbox :item-id="itemId" />
        <i
            aria-hidden="true"
            class="pi pi-lock"
        />
        <span class="query-read-only-item-summary">
            {{ $gettext("This condition can't be edited here.") }}
        </span>
        <Button
            icon="pi pi-times"
            severity="secondary"
            variant="text"
            size="small"
            :aria-label="$gettext('Remove condition')"
            @click="onRemove"
        />
    </div>
</template>

<style scoped>
.query-read-only-item {
    display: flex;
    flex: 1;
    align-items: center;
    gap: 0.8rem;
    min-inline-size: 0;
    padding: 0.9rem 1.2rem;
    border: 0.15rem dashed var(--p-content-border-color);
    border-radius: 0.8rem;
    background: var(--p-content-background);
    color: var(--p-text-muted-color);
}

.query-read-only-item.query-read-only-item-selected {
    border-color: var(--p-primary-color);
    box-shadow: 0 0 0 0.3rem var(--arches-search-primary-muted-bg);
}

.query-read-only-item .query-read-only-item-summary {
    flex: 1;
    font-size: 1.3rem;
}
</style>
