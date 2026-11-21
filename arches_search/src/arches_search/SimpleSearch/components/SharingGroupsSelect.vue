<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import MultiSelect from "openvue/multiselect";

import type { SharingGroup } from "@/arches_search/SimpleSearch/types.ts";

const UPDATE_SHARED_GROUP_IDS_EVENT = "update:sharedGroupIds" as const;

const { sharedGroupIds, inputId, groups } = defineProps<{
    sharedGroupIds: number[];
    inputId: string;
    groups: SharingGroup[];
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_SHARED_GROUP_IDS_EVENT, value: number[]): void;
}>();

const { $gettext } = useGettext();

function onSelectionChange(value: number[]): void {
    emit(UPDATE_SHARED_GROUP_IDS_EVENT, value);
}
</script>

<template>
    <MultiSelect
        class="sharing-groups-input"
        option-label="name"
        option-value="id"
        display="chip"
        :input-id="inputId"
        :model-value="sharedGroupIds"
        :options="groups"
        :filter="true"
        :fluid="true"
        :placeholder="$gettext('Not shared')"
        :empty-message="$gettext('No groups available')"
        @update:model-value="onSelectionChange"
    />
</template>

<style scoped>
.sharing-groups-input,
.sharing-groups-input :deep(.p-multiselect-label) {
    font-size: var(--p-arches-search-font-size);
}
</style>
