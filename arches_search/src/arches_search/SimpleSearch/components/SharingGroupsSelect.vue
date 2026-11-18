<script setup lang="ts">
import { ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "openvue/message";
import MultiSelect from "openvue/multiselect";

import { getSharingGroups } from "@/arches_search/SimpleSearch/api.ts";

import type { SharingGroup } from "@/arches_search/SimpleSearch/types.ts";

const UPDATE_SHARED_GROUP_IDS_EVENT = "update:sharedGroupIds" as const;

const { sharedGroupIds, inputId } = defineProps<{
    sharedGroupIds: number[];
    inputId: string;
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_SHARED_GROUP_IDS_EVENT, value: number[]): void;
}>();

const { $gettext } = useGettext();

const groups = ref<SharingGroup[]>([]);
const isLoading = ref(false);
const hasLoadError = ref(false);

watchEffect(async () => {
    isLoading.value = true;
    try {
        groups.value = await getSharingGroups();
        hasLoadError.value = false;
    } catch {
        groups.value = [];
        hasLoadError.value = true;
    } finally {
        isLoading.value = false;
    }
});

function onSelectionChange(value: number[]): void {
    emit(UPDATE_SHARED_GROUP_IDS_EVENT, value);
}
</script>

<template>
    <div class="sharing-groups-select">
        <MultiSelect
            class="sharing-groups-input"
            option-label="name"
            option-value="id"
            display="chip"
            :input-id="inputId"
            :model-value="sharedGroupIds"
            :options="groups"
            :loading="isLoading"
            :filter="true"
            :fluid="true"
            :placeholder="$gettext('Not shared')"
            :empty-message="$gettext('No groups available')"
            @update:model-value="onSelectionChange"
        />
        <Message
            v-if="hasLoadError"
            class="sharing-groups-error"
            severity="error"
            size="small"
            variant="simple"
        >
            {{ $gettext("Groups could not be loaded.") }}
        </Message>
    </div>
</template>

<style scoped>
.sharing-groups-select {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

:deep(.sharing-groups-select .sharing-groups-input),
:deep(.sharing-groups-select .p-multiselect-label) {
    font-size: var(--p-arches-search-font-size);
}
</style>
