<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Chip from "primevue/chip";
import MultiSelect from "primevue/multiselect";

import type { Node } from "@/arches_search/AdvancedSearch/types.ts";

const UPDATE_EVENT = "update:modelValue" as const;

const props = defineProps<{
    graphLabel: string | null;
    dateNodes: Node[];
    modelValue: string[];
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_EVENT, value: string[]): void;
}>();

const { $gettext, interpolate } = useGettext();
const NODE_SELECT_ID = "simple-search-time-filter-node-selection" as const;

const selectedNodeAliases = computed<string[]>({
    get(): string[] {
        return props.modelValue;
    },
    set(value: string[]): void {
        emit(UPDATE_EVENT, value);
    },
});

const selectionSummary = computed<string>(() => {
    if (selectedNodeAliases.value.length === 0) {
        return $gettext("Select an attribute");
    }

    if (selectedNodeAliases.value.length === 1) {
        return getNodeLabel(selectedNodeAliases.value[0]);
    }

    return interpolate($gettext("%{count} date nodes selected"), {
        count: String(selectedNodeAliases.value.length),
    });
});

function getNodeLabel(alias: string): string {
    return props.dateNodes.find((node) => node.alias === alias)?.name ?? alias;
}

function removeNode(alias: string): void {
    emit(
        UPDATE_EVENT,
        props.modelValue.filter((value) => value !== alias),
    );
}
</script>

<template>
    <div class="node-selection">
        <div class="node-selection__attribute-row">
            <label
                class="node-selection__attribute-label"
                :for="NODE_SELECT_ID"
            >
                {{
                    interpolate($gettext("%{graphLabel} Time attribute:"), {
                        graphLabel: props.graphLabel ?? $gettext("Resource"),
                    })
                }}
            </label>

            <MultiSelect
                v-model="selectedNodeAliases"
                :input-id="NODE_SELECT_ID"
                :options="dateNodes"
                option-label="name"
                option-value="alias"
                :placeholder="$gettext('Select an attribute')"
                :filter="true"
                :filter-placeholder="$gettext('Search date nodes...')"
                :reset-filter-on-clear="true"
                :show-toggle-all="false"
                :max-selected-labels="0"
                overlay-class="node-selection__select-overlay"
                class="node-selection__select"
            >
                <template #value="valueSlotProps">
                    <span
                        class="node-selection__select-value"
                        :class="{
                            'node-selection__select-value--placeholder':
                                selectedNodeAliases.length === 0,
                        }"
                    >
                        {{
                            selectedNodeAliases.length === 0
                                ? valueSlotProps.placeholder
                                : selectionSummary
                        }}
                    </span>
                </template>
            </MultiSelect>
        </div>

        <div class="node-selection__chips">
            <Chip
                v-if="selectedNodeAliases.length === 0"
                :label="$gettext('All date nodes')"
                class="node-selection__chip"
            />
            <Chip
                v-for="alias in selectedNodeAliases"
                :key="alias"
                :label="getNodeLabel(alias)"
                removable
                remove-icon="pi pi-times"
                class="node-selection__chip"
                @remove="removeNode(alias)"
            />
        </div>
    </div>
</template>

<style scoped>
.node-selection {
    display: flex;
    flex-direction: column;
    gap: 0.9375rem;
}

.node-selection__attribute-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.875rem;
    align-items: baseline;
}

.node-selection__attribute-label {
    font-size: 1.25rem;
    font-weight: 600;
    line-height: 1.35;
    color: var(--p-text-color);
    white-space: nowrap;
}

.node-selection__select {
    flex: 0 1 24rem;
    min-inline-size: 16rem;
    max-inline-size: min(100%, 28rem);
    font-size: var(--time-filter-control-size, 1rem);
}

.node-selection__select :deep(.p-multiselect-label),
.node-selection__select :deep(.p-multiselect-dropdown),
.node-selection__select :deep(.p-multiselect-clear-icon) {
    font-size: var(--time-filter-control-size, 1rem);
}

.node-selection__select :deep(.p-multiselect-label-container) {
    display: flex;
    align-items: center;
}

.node-selection__select :deep(.p-multiselect-label) {
    display: flex;
    align-items: center;
    min-block-size: 3rem;
    padding-block: 0.75rem;
    padding-inline: 0.9375rem;
}

.node-selection__select :deep(.p-multiselect-dropdown) {
    min-inline-size: 3rem;
}

.node-selection__select-value {
    display: inline-flex;
    align-items: center;
    min-block-size: 1.5rem;
    color: var(--p-text-color);
}

.node-selection__select-value--placeholder {
    color: var(--p-text-muted-color);
}

:deep(.node-selection__select-overlay .p-multiselect-header) {
    padding: 0.75rem;
}

:deep(.node-selection__select-overlay .p-inputtext) {
    font-size: var(--time-filter-control-size, 1rem);
}

:deep(.node-selection__select-overlay .p-multiselect-option) {
    padding-block: 0.8125rem;
    padding-inline: 0.9375rem;
    font-size: var(--time-filter-control-size, 1rem);
}

.node-selection__chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.625rem;
}

.node-selection__chip {
    border-radius: 0.4rem;
    min-block-size: 3rem;
    padding-block: 0.6875rem;
    padding-inline: 1.125rem;
    gap: 0.875rem;
    font-size: var(--time-filter-chip-size, 1.125rem);
}

.node-selection__chip :deep(.p-chip-remove-icon) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    inline-size: auto;
    block-size: auto;
    border-radius: 0;
    margin-inline-start: 0.75rem;
    font-size: var(--time-filter-chip-size, 1.125rem);
}

.node-selection__chip :deep(.p-chip-label) {
    font-size: var(--time-filter-chip-size, 1.125rem);
}
</style>
