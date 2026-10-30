<script setup lang="ts">
import { computed, inject } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import { QUERY_BUILDER_ITEM_RELATED_GROUP } from "@/arches_search/AdvancedSearch/types.ts";

import type { Ref } from "vue";
import type {
    GraphModel,
    QueryBuilderItem,
} from "@/arches_search/AdvancedSearch/types.ts";

const { item } = defineProps<{
    item: QueryBuilderItem;
}>();

const graphs = inject<Ref<GraphModel[]>>("graphs")!;

const { $gettext } = useGettext();
const queryBuilder = useQueryBuilder();

const summaryText = computed<string>(() => {
    if (item.itemType !== QUERY_BUILDER_ITEM_RELATED_GROUP) {
        return $gettext("This condition can't be edited here.");
    }
    const targetGraphName =
        graphs.value.find((graph) => graph.slug === item.targetGraphSlug)
            ?.name ?? item.targetGraphSlug;
    return $gettext("Related to %{model} via %{field}", {
        model: targetGraphName,
        field: item.relationship.path.node_alias,
    });
});

function onRemove(): void {
    queryBuilder.removeItem(item.id);
}
</script>

<template>
    <div class="query-read-only-item">
        <i
            aria-hidden="true"
            class="pi pi-lock"
        />
        <span class="query-read-only-item-summary">{{ summaryText }}</span>
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

.query-read-only-item .query-read-only-item-summary {
    flex: 1;
    font-size: 1.3rem;
}
</style>
