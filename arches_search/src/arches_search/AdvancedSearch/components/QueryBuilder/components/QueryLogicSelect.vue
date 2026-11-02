<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import SelectButton from "openvue/selectbutton";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import { LogicToken } from "@/arches_search/AdvancedSearch/types.ts";

const { containerId, logic } = defineProps<{
    containerId: string;
    logic: LogicToken;
}>();

const { $gettext } = useGettext();
const queryBuilder = useQueryBuilder();

const logicOptions = computed<{ label: string; value: LogicToken }[]>(() => [
    { label: $gettext("ALL"), value: LogicToken.AND },
    { label: $gettext("ANY"), value: LogicToken.OR },
]);

function onLogicChange(nextLogic: LogicToken | null): void {
    if (nextLogic && nextLogic !== logic) {
        queryBuilder.toggleGroupLogic(containerId);
    }
}
</script>

<template>
    <SelectButton
        option-label="label"
        option-value="value"
        :model-value="logic"
        :options="logicOptions"
        :allow-empty="false"
        @update:model-value="onLogicChange"
    />
</template>
