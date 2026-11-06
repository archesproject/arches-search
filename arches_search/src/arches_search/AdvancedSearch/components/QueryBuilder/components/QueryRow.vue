<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import ClauseBuilder from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/ClauseBuilder/ClauseBuilder.vue";
import QueryRowTags from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryRowTags.vue";
import QuerySelectCheckbox from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QuerySelectCheckbox.vue";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import { getClauseOperandComponent } from "@/arches_search/AdvancedSearch/utils/query-builder.ts";
import {
    ClauseSubjectTypeToken,
    QUANTIFIER_ALL,
    QUANTIFIER_NONE,
} from "@/arches_search/AdvancedSearch/types.ts";

import type {
    AdvancedSearchOperandComponent,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";

const ATTRIBUTE_BADGE_KIND = "attribute";
const ATTRIBUTE_BADGE_ICON = "pi pi-tag";
const TEXT_SEARCH_BADGE_KIND = "text";
const TEXT_SEARCH_BADGE_ICON = "pi pi-search";

const { rowId, clause } = defineProps<{
    rowId: string;
    clause: LiteralClause;
}>();

const { $gettext } = useGettext();
const queryBuilder = useQueryBuilder();
const { selectedItemIds, panelRowId } = queryBuilder;

const operandComponent = computed<AdvancedSearchOperandComponent | null>(() =>
    getClauseOperandComponent(clause, queryBuilder.lookups),
);

const isTextSearch = computed<boolean>(
    () =>
        clause.subject.type === ClauseSubjectTypeToken.SEARCH_MODELS &&
        operandComponent.value === null,
);

const badge = computed<{ label: string; icon: string; kind: string }>(() => {
    if (operandComponent.value) {
        return {
            label: operandComponent.value.label,
            icon: operandComponent.value.icon,
            kind: operandComponent.value.slug,
        };
    }
    if (isTextSearch.value) {
        return {
            label: $gettext("Text search"),
            icon: TEXT_SEARCH_BADGE_ICON,
            kind: TEXT_SEARCH_BADGE_KIND,
        };
    }
    return {
        label: $gettext("Attribute"),
        icon: ATTRIBUTE_BADGE_ICON,
        kind: ATTRIBUTE_BADGE_KIND,
    };
});

const isNegated = computed<boolean>(
    () => clause.quantifier === QUANTIFIER_NONE,
);

const canNegate = computed<boolean>(() => clause.quantifier !== QUANTIFIER_ALL);

const isSelected = computed<boolean>(() =>
    selectedItemIds.value.includes(rowId),
);

const isEditingInPanel = computed<boolean>(() => panelRowId.value === rowId);

function onUpdateClause(updatedClause: LiteralClause): void {
    queryBuilder.setRowClause(rowId, updatedClause);
}

function onOpenPanel(): void {
    queryBuilder.openRowPanel(rowId);
}

function onToggleNot(): void {
    queryBuilder.toggleRowNot(rowId);
}

function onRemove(): void {
    queryBuilder.removeItem(rowId);
}
</script>

<template>
    <div
        class="query-row"
        :class="{ 'query-row-selected': isSelected }"
    >
        <QuerySelectCheckbox :item-id="rowId" />
        <QueryRowTags
            :graph-slug="clause.subject.graph_slug"
            :badge-label="badge.label"
            :badge-icon="badge.icon"
            :badge-kind="badge.kind"
            :is-negated="isNegated"
            :can-negate="canNegate"
            @toggle-not="onToggleNot"
        />
        <ClauseBuilder
            :model-value="clause"
            :operand-component="operandComponent"
            :is-editing-in-panel="isEditingInPanel"
            @update:model-value="onUpdateClause"
            @open-panel="onOpenPanel"
        />
        <Button
            class="query-row-remove"
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
.query-row {
    display: flex;
    flex: 1;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.8rem;
    min-inline-size: 0;
    padding: 0.9rem 1.2rem;
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 0.8rem;
    background: var(--p-content-background);
    transition:
        border-color 0.15s,
        box-shadow 0.15s;
}

.query-row:hover {
    border-color: var(--p-primary-color);
}

.query-row.query-row-selected {
    border-color: var(--p-primary-color);
    box-shadow: 0 0 0 0.3rem var(--arches-search-primary-muted-bg);
}

.query-row .query-row-remove {
    margin-inline-start: auto;
}
</style>
