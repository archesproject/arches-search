<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import InputText from "openvue/inputtext";

import QueryLogicSelect from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryLogicSelect.vue";
import QuerySelectCheckbox from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QuerySelectCheckbox.vue";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";

import type { LogicToken } from "@/arches_search/AdvancedSearch/types.ts";

const { groupId, label, logic, isRelated } = defineProps<{
    groupId: string;
    label: string;
    logic: LogicToken;
    isRelated: boolean;
}>();

const { $gettext } = useGettext();
const queryBuilder = useQueryBuilder();

const iconClass = computed<string>(() => {
    if (isRelated) {
        return "pi pi-share-alt";
    }
    return "pi pi-th-large";
});

const labelPlaceholder = computed<string>(() => {
    if (isRelated) {
        return $gettext("Related records");
    }
    return $gettext("Group label (optional)");
});

function onLabelChange(nextLabel: string | undefined): void {
    queryBuilder.setGroupLabel(groupId, nextLabel ?? "");
}

function onRemove(): void {
    queryBuilder.removeItem(groupId);
}
</script>

<template>
    <div
        class="query-group-header"
        :class="{ 'query-group-header-related': isRelated }"
    >
        <QuerySelectCheckbox :item-id="groupId" />
        <i
            aria-hidden="true"
            class="query-group-header-icon"
            :class="iconClass"
        />
        <InputText
            class="query-group-header-label"
            size="small"
            :model-value="label"
            :placeholder="labelPlaceholder"
            :aria-label="$gettext('Group label')"
            @update:model-value="onLabelChange"
        />
        <QueryLogicSelect
            size="small"
            :container-id="groupId"
            :logic="logic"
            :aria-label="$gettext('Match all or any conditions in this group')"
        />
        <span class="query-group-header-match">
            {{ $pgettext("Query group: '[ALL/ANY] match'", "match") }}
        </span>
        <Button
            icon="pi pi-times"
            severity="secondary"
            variant="text"
            size="small"
            :aria-label="$gettext('Remove group')"
            @click="onRemove"
        />
    </div>
</template>

<style scoped>
.query-group-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.8rem 1.2rem;
    border-block-end: 0.1rem solid;
}

.query-group-header .query-group-header-icon {
    flex-shrink: 0;
    color: var(--p-primary-color);
    font-size: 1.3rem;
}

.query-group-header.query-group-header-related .query-group-header-icon {
    color: var(--arches-search-query-related-accent);
    font-size: 1.4rem;
}

.query-group-header .query-group-header-label {
    flex: 1;
    min-inline-size: 8rem;
    border-color: transparent;
    background: transparent;
    box-shadow: none;
    font-size: 1.2rem;
    font-weight: 600;
}

.query-group-header .query-group-header-label:focus {
    background: var(--p-content-background);
}

.query-group-header.query-group-header-related .query-group-header-label {
    color: var(--arches-search-query-related-accent);
    font-size: 1.3rem;
    font-weight: 700;
}

.query-group-header .query-group-header-match {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    font-weight: 500;
    white-space: nowrap;
}
</style>
