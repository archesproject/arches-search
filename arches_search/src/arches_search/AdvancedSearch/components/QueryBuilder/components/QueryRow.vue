<script setup lang="ts">
import { computed, inject } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import ClauseBuilder from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/ClauseBuilder/ClauseBuilder.vue";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import { deriveRowKind } from "@/arches_search/AdvancedSearch/utils/query-builder.ts";
import {
    QUERY_BUILDER_ROW_KIND_ATTRIBUTE,
    QUERY_BUILDER_ROW_KIND_MAP,
    QUERY_BUILDER_ROW_KIND_TIME,
} from "@/arches_search/AdvancedSearch/types.ts";

import type { Ref } from "vue";
import type {
    GraphModel,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";

const { rowId, clause } = defineProps<{
    rowId: string;
    clause: LiteralClause;
}>();

const graphs = inject<Ref<GraphModel[]>>("graphs")!;

const { $gettext } = useGettext();
const queryBuilder = useQueryBuilder();

const rowKind = computed(() => deriveRowKind(clause, queryBuilder.lookups));

const rowGraph = computed<GraphModel | null>(
    () =>
        graphs.value.find(
            (graph) => graph.slug === clause.subject.graph_slug,
        ) ?? null,
);

const isAttributeRow = computed<boolean>(
    () => rowKind.value === QUERY_BUILDER_ROW_KIND_ATTRIBUTE,
);

const summaryText = computed<string>(() => {
    if (rowKind.value === QUERY_BUILDER_ROW_KIND_TIME) {
        return $gettext("Time filter");
    }
    if (rowKind.value === QUERY_BUILDER_ROW_KIND_MAP) {
        return $gettext("Map filter");
    }
    return $gettext("Attribute filter");
});

function onUpdateClause(updatedClause: LiteralClause): void {
    queryBuilder.setRowClause(rowId, updatedClause);
}

function onRemove(): void {
    queryBuilder.removeItem(rowId);
}
</script>

<template>
    <div class="query-row">
        <ClauseBuilder
            v-if="isAttributeRow && rowGraph"
            class="query-row-clause"
            :model-value="clause"
            :anchor-graph="rowGraph"
            @update:model-value="onUpdateClause"
            @request:remove="onRemove"
        />
        <template v-else>
            <span class="query-row-summary">{{ summaryText }}</span>
            <Button
                icon="pi pi-times"
                severity="secondary"
                variant="text"
                size="small"
                :aria-label="$gettext('Remove condition')"
                @click="onRemove"
            />
        </template>
    </div>
</template>

<style scoped>
.query-row {
    display: flex;
    flex: 1;
    align-items: center;
    gap: 0.8rem;
    min-inline-size: 0;
    padding: 0.9rem 1.2rem;
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 0.8rem;
    background: var(--p-content-background);
}

.query-row .query-row-clause {
    flex: 1;
    min-inline-size: 0;
}

.query-row .query-row-summary {
    flex: 1;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    font-weight: 600;
}
</style>
