<script setup lang="ts">
import { ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import MultiSelect from "openvue/multiselect";

import { getSharingGroups } from "@/arches_search/SimpleSearch/api.ts";

import type { SharingGroup } from "@/arches_search/SimpleSearch/types.ts";

const UPDATE_MODEL_VALUE_EVENT = "update:modelValue" as const;

const { modelValue, inputId } = defineProps<{
    // The ids of the selected groups.
    modelValue: number[];
    inputId: string;
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_MODEL_VALUE_EVENT, value: number[]): void;
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
    emit(UPDATE_MODEL_VALUE_EVENT, value);
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
            :model-value="modelValue"
            :options="groups"
            :loading="isLoading"
            :filter="true"
            :fluid="true"
            :placeholder="$gettext('Not shared')"
            :empty-message="$gettext('No groups available')"
            @update:model-value="onSelectionChange"
        />
        <small
            v-if="hasLoadError"
            class="sharing-groups-error"
        >
            {{ $gettext("Groups could not be loaded.") }}
        </small>
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

.sharing-groups-select .sharing-groups-error {
    color: var(--p-red-500);
}
</style>
