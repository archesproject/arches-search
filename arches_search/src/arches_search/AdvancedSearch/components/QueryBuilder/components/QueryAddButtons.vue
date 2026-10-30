<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import { QUERY_BUILDER_ROW_KIND_ATTRIBUTE } from "@/arches_search/AdvancedSearch/types.ts";

const { containerId, isNested = false } = defineProps<{
    containerId: string;
    isNested?: boolean;
}>();

const { $gettext } = useGettext();
const queryBuilder = useQueryBuilder();

const attributeLabel = computed<string>(() => {
    if (isNested) {
        return $gettext("Attribute");
    }
    return $gettext("Add attribute filter");
});

const groupLabel = computed<string>(() => {
    if (isNested) {
        return $gettext("Sub-group");
    }
    return $gettext("Add group");
});

function onAddAttribute(): void {
    queryBuilder.addRow(containerId, QUERY_BUILDER_ROW_KIND_ATTRIBUTE);
}

function onAddGroup(): void {
    queryBuilder.addGroup(containerId);
}
</script>

<template>
    <div
        class="query-add-buttons"
        :class="{ 'query-add-buttons-nested': isNested }"
    >
        <span
            v-if="isNested"
            class="query-add-buttons-label"
        >
            {{ $gettext("Add:") }}
        </span>
        <Button
            icon="pi pi-plus"
            class="query-add-button"
            size="small"
            variant="outlined"
            severity="secondary"
            :label="attributeLabel"
            @click="onAddAttribute"
        />
        <Button
            icon="pi pi-th-large"
            class="query-add-button"
            size="small"
            variant="outlined"
            severity="secondary"
            :label="groupLabel"
            @click="onAddGroup"
        />
    </div>
</template>

<style scoped>
.query-add-buttons {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.8rem;
}

.query-add-buttons.query-add-buttons-nested {
    padding-block-start: 0.8rem;
    border-block-start: 0.1rem dashed var(--p-content-border-color);
}

.query-add-buttons .query-add-buttons-label {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 600;
}

.query-add-buttons .query-add-button {
    border-style: dashed;
    font-size: 1.2rem;
}
</style>
