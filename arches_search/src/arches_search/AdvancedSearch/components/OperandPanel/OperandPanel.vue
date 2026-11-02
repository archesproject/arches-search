<script setup lang="ts">
import { computed, defineAsyncComponent, toRef } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import SelectButton from "openvue/selectbutton";

import { removeVueExtension } from "@/arches_vue_components/generics/GenericWidget/utils.ts";
import { useClauseSubjectNode } from "@/arches_search/AdvancedSearch/composables/useClauseSubjectNode.ts";
import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import {
    findQueryBuilderItem,
    getClauseOperandComponent,
    listQueryBuilderRows,
} from "@/arches_search/AdvancedSearch/utils/query-builder.ts";
import {
    ClauseSubjectTypeToken,
    QUERY_BUILDER_ITEM_ROW,
} from "@/arches_search/AdvancedSearch/types.ts";

import type { Component } from "vue";
import type {
    AdvancedSearchOperandComponent,
    LiteralClause,
    QueryBuilderRow,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();
const queryBuilder = useQueryBuilder();
const { root, panelRowId, lookups } = queryBuilder;

const panelRow = computed<QueryBuilderRow | null>(() => {
    if (!root.value || !panelRowId.value) {
        return null;
    }
    const item = findQueryBuilderItem(root.value, panelRowId.value);
    if (item?.itemType !== QUERY_BUILDER_ITEM_ROW) {
        return null;
    }
    return item;
});

const { subjectNode } = useClauseSubjectNode(
    toRef(() => panelRow.value?.clause.subject),
);

const fieldLabel = computed<string>(() => {
    const subject = panelRow.value?.clause.subject;
    if (!subject) {
        return "";
    }
    if (subject.type !== ClauseSubjectTypeToken.NODE) {
        return $gettext("Any field");
    }
    return (
        subjectNode.value?.card_x_node_x_widget_label ||
        subjectNode.value?.name ||
        ""
    );
});

const panelOperandComponent = computed<AdvancedSearchOperandComponent | null>(
    () => {
        if (!panelRow.value) {
            return null;
        }
        return getClauseOperandComponent(panelRow.value.clause, lookups);
    },
);

const operandEditor = computed<Component | null>(() => {
    const componentPath = panelOperandComponent.value?.component;
    if (!componentPath) {
        return null;
    }
    return defineAsyncComponent(
        () => import(`@/${removeVueExtension(componentPath)}.vue`),
    );
});

const switcherOptions = computed<{ label: string; value: string }[]>(() => {
    const panelSlug = panelOperandComponent.value?.slug;
    if (!root.value || !panelSlug) {
        return [];
    }
    return listQueryBuilderRows(root.value)
        .filter(
            (row) =>
                getClauseOperandComponent(row.clause, lookups)?.slug ===
                panelSlug,
        )
        .map((row, rowIndex) => ({
            label: String(rowIndex + 1),
            value: row.id,
        }));
});

function onSwitchRow(rowId: string | null): void {
    if (rowId) {
        queryBuilder.openRowPanel(rowId);
    }
}

function onUpdateClause(updatedClause: LiteralClause): void {
    if (panelRowId.value) {
        queryBuilder.setRowClause(panelRowId.value, updatedClause);
    }
}

function onClose(): void {
    queryBuilder.closeRowPanel();
}
</script>

<template>
    <section
        v-if="panelRow && panelOperandComponent"
        class="operand-panel"
    >
        <header class="operand-panel-header">
            <i
                aria-hidden="true"
                class="operand-panel-icon"
                :class="panelOperandComponent.icon"
            />
            <div class="operand-panel-title">
                <span class="operand-panel-label">
                    {{ panelOperandComponent.label }}
                </span>
                <span
                    v-if="fieldLabel"
                    class="operand-panel-field"
                >
                    {{ fieldLabel }}
                </span>
            </div>
            <SelectButton
                v-if="switcherOptions.length > 1"
                size="small"
                option-label="label"
                option-value="value"
                :model-value="panelRow.id"
                :options="switcherOptions"
                :allow-empty="false"
                :aria-label="$gettext('Switch between conditions of this kind')"
                @update:model-value="onSwitchRow"
            />
            <Button
                icon="pi pi-times"
                severity="secondary"
                variant="text"
                size="small"
                :label="$gettext('Close')"
                @click="onClose"
            />
        </header>
        <div class="operand-panel-body">
            <component
                :is="operandEditor"
                v-if="operandEditor"
                :key="panelRow.id"
                :clause="panelRow.clause"
                @update:clause="onUpdateClause"
            />
        </div>
    </section>
</template>

<style scoped>
.operand-panel {
    display: flex;
    flex-direction: column;
    block-size: 100%;
    background: var(--p-content-background);
}

.operand-panel .operand-panel-header {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 1rem;
    padding: 1.6rem 2rem 1rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.operand-panel .operand-panel-icon {
    color: var(--p-primary-color);
    font-size: 1.6rem;
}

.operand-panel .operand-panel-title {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
}

.operand-panel .operand-panel-label {
    color: var(--p-text-color);
    font-size: 1.5rem;
    font-weight: 700;
}

.operand-panel .operand-panel-field {
    overflow: hidden;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.operand-panel .operand-panel-body {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
    overflow-y: auto;
}
</style>
