<script setup lang="ts">
import { computed } from "vue";

import Checkbox from "openvue/checkbox";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";

const { itemId } = defineProps<{
    itemId: string;
}>();

const queryBuilder = useQueryBuilder();
const { isSelecting, selectedItemIds } = queryBuilder;

const isSelected = computed<boolean>(() =>
    selectedItemIds.value.includes(itemId),
);

function onToggle(): void {
    queryBuilder.toggleItemSelected(itemId);
}
</script>

<template>
    <Checkbox
        v-if="isSelecting"
        class="query-select-checkbox"
        :model-value="isSelected"
        :binary="true"
        :aria-label="$gettext('Select for grouping')"
        @update:model-value="onToggle"
    />
</template>

<style scoped>
.query-select-checkbox {
    flex-shrink: 0;
}
</style>
