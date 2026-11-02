<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import MultiSelect from "openvue/multiselect";

import { fetchControlledListReferenceValues } from "@/arches_search/SimpleSearch/api.ts";
import {
    isLabelList,
    referenceValueLabel,
    referenceValuesWithLabels,
} from "@/arches_search/AdvancedSearch/utils/reference-labels.ts";

import type { ReferenceSelectNodeValue } from "@/arches_controlled_lists/datatypes/reference-select/types.ts";
import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";
import type { ReferenceFilterValue } from "@/arches_search/SimpleSearch/components/attribute-filters/types.ts";

const { $gettext } = useGettext();

const { node, modelValue } = defineProps<{
    node: NodeFilterConfigNode;
    modelValue: ReferenceFilterValue | null;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", value: ReferenceSelectNodeValue[]): void;
}>();

const options = ref<ReferenceSelectNodeValue[]>([]);
const isLoading = ref(false);

const controlledListId = computed<string | null>(() => {
    const listId = node.config?.controlledList;
    return typeof listId === "string" ? listId : null;
});

const selectedReferenceValues = computed<ReferenceSelectNodeValue[]>(() => {
    if (isLabelList(modelValue)) {
        return referenceValuesWithLabels(options.value, modelValue);
    }
    return modelValue ?? [];
});

watch(
    controlledListId,
    async (listId) => {
        if (!listId) {
            options.value = [];
            return;
        }
        isLoading.value = true;
        try {
            options.value = await fetchControlledListReferenceValues(listId);
        } catch (error) {
            console.error(
                "[ReferenceFilterMultiSelect] failed to load controlled list items:",
                error,
            );
            options.value = [];
        } finally {
            isLoading.value = false;
        }
    },
    { immediate: true },
);

function onSelectionChange(value: ReferenceSelectNodeValue[]): void {
    emit("update:modelValue", value);
}
</script>

<template>
    <div class="reference-filter">
        <MultiSelect
            class="reference-filter-select"
            data-key="uri"
            :input-id="node.node_alias"
            :model-value="selectedReferenceValues"
            :options="options"
            :option-label="referenceValueLabel"
            :loading="isLoading"
            :filter="true"
            :filter-placeholder="$gettext('Search options...')"
            :placeholder="$gettext('Select options...')"
            :show-clear="true"
            :fluid="true"
            :disabled="options.length === 0 && !isLoading"
            :aria-label="node.label"
            @update:model-value="onSelectionChange"
        />
        <span
            v-if="options.length === 0 && !isLoading"
            class="status"
        >
            {{ $gettext("No options available.") }}
        </span>
    </div>
</template>

<style scoped>
.reference-filter {
    padding: 0.4rem 0 0.8rem 0;
}

.reference-filter .reference-filter-select {
    padding-block: 0.4rem;
    padding-inline: 0.8rem;
}

.reference-filter :deep(.p-multiselect-label) {
    font-size: var(--p-arches-search-font-size);
}

.reference-filter .status {
    display: block;
    font-size: var(--p-arches-search-font-size);
    color: var(--p-text-muted-color);
    padding: 0.4rem 0 0 0;
    line-height: 1.5;
}
</style>
