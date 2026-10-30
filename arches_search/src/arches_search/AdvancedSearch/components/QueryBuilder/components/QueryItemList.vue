<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import InputText from "openvue/inputtext";
import SelectButton from "openvue/selectbutton";

import QueryAddButtons from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryAddButtons.vue";
import QueryReadOnlyItem from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryReadOnlyItem.vue";
import QueryRow from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryRow.vue";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import {
    LogicToken,
    QUERY_BUILDER_ITEM_GROUP,
    QUERY_BUILDER_ITEM_ROW,
} from "@/arches_search/AdvancedSearch/types.ts";

import type { QueryBuilderItem } from "@/arches_search/AdvancedSearch/types.ts";

const GROUP_DEPTH_COLOR_COUNT = 3;

const { containerId, items, logic, depth } = defineProps<{
    containerId: string;
    items: QueryBuilderItem[];
    logic: LogicToken;
    depth: number;
}>();

const { $gettext, $pgettext } = useGettext();
const queryBuilder = useQueryBuilder();

const isAllLogic = computed<boolean>(() => logic === LogicToken.AND);

const connectorLabel = computed<string>(() => {
    if (isAllLogic.value) {
        return $gettext("AND");
    }
    return $gettext("OR");
});

const leadText = computed<string>(() => {
    if (depth === 0) {
        return "";
    }
    return $pgettext("Query group: 'where [first condition]'", "where");
});

const emptyHint = computed<string>(() => {
    if (depth === 0) {
        return $gettext(
            "No conditions yet. Add one below, or click Search to return every record of this model.",
        );
    }
    return $gettext("Empty group. Add conditions with the buttons below.");
});

const logicOptions = computed(() => [
    { label: $gettext("ALL"), value: LogicToken.AND },
    { label: $gettext("ANY"), value: LogicToken.OR },
]);

const groupDepthClass = computed<string>(
    () => `query-group-depth-${depth % GROUP_DEPTH_COLOR_COUNT}`,
);

function onToggleLogic(): void {
    queryBuilder.toggleGroupLogic(containerId);
}

function onGroupLogicChange(
    groupId: string,
    currentLogic: LogicToken,
    nextLogic: LogicToken | null,
): void {
    if (nextLogic && nextLogic !== currentLogic) {
        queryBuilder.toggleGroupLogic(groupId);
    }
}

function onGroupLabelChange(groupId: string, label: string | undefined): void {
    queryBuilder.setGroupLabel(groupId, label ?? "");
}

function onRemoveItem(itemId: string): void {
    queryBuilder.removeItem(itemId);
}
</script>

<template>
    <div class="query-item-list">
        <span
            v-if="items.length === 0"
            class="query-item-list-hint"
        >
            <i
                aria-hidden="true"
                class="pi pi-info-circle"
            />
            <span>{{ emptyHint }}</span>
        </span>

        <div
            v-for="(item, itemIndex) in items"
            :key="item.id"
            class="query-item"
        >
            <Button
                v-if="itemIndex > 0"
                class="query-item-connector"
                size="small"
                :class="{ 'query-item-connector-or': !isAllLogic }"
                :label="connectorLabel"
                :title="$gettext('Switch this group between ALL and ANY')"
                @click="onToggleLogic"
            />
            <span
                v-else
                class="query-item-lead"
            >
                {{ leadText }}
            </span>

            <QueryRow
                v-if="item.itemType === QUERY_BUILDER_ITEM_ROW"
                :row-id="item.id"
                :clause="item.clause"
            />
            <div
                v-else-if="item.itemType === QUERY_BUILDER_ITEM_GROUP"
                class="query-group"
                :class="groupDepthClass"
            >
                <div class="query-group-header">
                    <i
                        aria-hidden="true"
                        class="pi pi-th-large"
                    />
                    <InputText
                        class="query-group-label"
                        size="small"
                        :model-value="item.label"
                        :placeholder="$gettext('Group label (optional)')"
                        :aria-label="$gettext('Group label')"
                        @update:model-value="
                            onGroupLabelChange(item.id, $event)
                        "
                    />
                    <SelectButton
                        size="small"
                        option-label="label"
                        option-value="value"
                        :model-value="item.logic"
                        :options="logicOptions"
                        :allow-empty="false"
                        @update:model-value="
                            onGroupLogicChange(item.id, item.logic, $event)
                        "
                    />
                    <span class="query-group-match">
                        {{ $pgettext("Query group: 'ALL/ANY match'", "match") }}
                    </span>
                    <Button
                        icon="pi pi-times"
                        severity="secondary"
                        variant="text"
                        size="small"
                        :aria-label="$gettext('Remove group')"
                        @click="onRemoveItem(item.id)"
                    />
                </div>
                <div class="query-group-body">
                    <QueryItemList
                        :container-id="item.id"
                        :items="item.items"
                        :logic="item.logic"
                        :depth="depth + 1"
                    />
                    <QueryAddButtons
                        :container-id="item.id"
                        :is-nested="true"
                    />
                </div>
            </div>
            <QueryReadOnlyItem
                v-else
                :item="item"
            />
        </div>
    </div>
</template>

<style scoped>
.query-item-list {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}

.query-item-list .query-item-list-hint {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding-block: 0.8rem 0.4rem;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
}

.query-item-list .query-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}

.query-item-list .query-item-lead,
.query-item-list .query-item-connector {
    flex-shrink: 0;
    inline-size: 4.9rem;
    margin-block-start: 1.1rem;
}

.query-item-list .query-item-lead {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 600;
    text-align: end;
}

.query-item-list .query-item-connector {
    padding-block: 0.4rem;
    border: none;
    background: var(--arches-search-logic-and-bg);
    color: var(--arches-search-logic-and-text);
    font-size: 1rem;
    font-weight: 800;
    letter-spacing: 0.06rem;
}

.query-item-list .query-item-connector.query-item-connector-or {
    background: var(--arches-search-logic-or-bg);
    color: var(--arches-search-logic-or-text);
}

.query-item-list .query-group {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
    overflow: hidden;
    border: 0.2rem solid var(--query-group-border);
    border-radius: 1rem;
    background: var(--query-group-bg);
}

.query-item-list .query-group.query-group-depth-0 {
    --query-group-bg: var(--arches-search-query-group-0-bg);
    --query-group-border: var(--arches-search-query-group-0-border);
    --query-group-header: var(--arches-search-query-group-0-header);
}

.query-item-list .query-group.query-group-depth-1 {
    --query-group-bg: var(--arches-search-query-group-1-bg);
    --query-group-border: var(--arches-search-query-group-1-border);
    --query-group-header: var(--arches-search-query-group-1-header);
}

.query-item-list .query-group.query-group-depth-2 {
    --query-group-bg: var(--arches-search-query-group-2-bg);
    --query-group-border: var(--arches-search-query-group-2-border);
    --query-group-header: var(--arches-search-query-group-2-header);
}

.query-item-list .query-group-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.8rem 1.2rem;
    border-block-end: 0.1rem solid var(--query-group-border);
    background: var(--query-group-header);
}

.query-item-list .query-group-label {
    flex: 1;
    min-inline-size: 0;
}

.query-item-list .query-group-match {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    font-weight: 500;
}

.query-item-list .query-group-body {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    padding: 1rem 1.2rem;
}
</style>
