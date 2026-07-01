<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Checkbox from "primevue/checkbox";

import { fetchControlledListItems } from "@/arches_search/SimpleSearch/api.ts";

import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";
import type {
    ReferenceFilterOption,
    ReferenceFilterValue,
} from "@/arches_search/SimpleSearch/components/attribute-filters/types.ts";

const { $gettext } = useGettext();

const props = defineProps<{
    node: NodeFilterConfigNode;
    modelValue: ReferenceFilterValue | null;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", value: ReferenceFilterValue): void;
}>();

const options = ref<ReferenceFilterOption[]>([]);
const isLoading = ref(false);

const selectedIds = computed(
    () => new Set((props.modelValue ?? []).map((option) => option.id)),
);

const controlledListId = computed<string | null>(() => {
    const listId = props.node.config?.controlledList;
    return typeof listId === "string" ? listId : null;
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
            const items = await fetchControlledListItems(listId);
            options.value = items.map((item) => ({
                id: item.uri,
                label: item.label,
            }));
        } catch (error) {
            console.error(
                "[ReferenceFilter] failed to load controlled list items:",
                error,
            );
            options.value = [];
        } finally {
            isLoading.value = false;
        }
    },
    { immediate: true },
);

function isChecked(optionId: string): boolean {
    return selectedIds.value.has(optionId);
}

function toggleOption(option: ReferenceFilterOption): void {
    const current = props.modelValue ?? [];
    const next = isChecked(option.id)
        ? current.filter((selected) => selected.id !== option.id)
        : [...current, option];
    emit("update:modelValue", next);
}
</script>

<template>
    <div
        v-if="isLoading"
        class="status"
    >
        {{ $gettext("Loading…") }}
    </div>
    <div
        v-else-if="options.length === 0"
        class="no-options"
    >
        {{ $gettext("No options available") }}
    </div>
    <div
        v-else
        class="filter-options"
    >
        <label
            v-for="option in options"
            :key="option.id"
            :for="`${node.node_alias}-${option.id}`"
            class="filter-option"
        >
            <Checkbox
                :input-id="`${node.node_alias}-${option.id}`"
                :model-value="isChecked(option.id)"
                binary
                @update:model-value="toggleOption(option)"
            />
            <span class="option-label">{{ option.label }}</span>
        </label>
    </div>
</template>

<style scoped>
.filter-options {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    padding: 0.4rem 0 0.8rem 0;
}

.filter-option {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    cursor: pointer;
    font-size: var(--p-arches-search-font-size);
}

.option-label {
    flex: 1;
    color: var(--p-surface-800);
}

.no-options,
.status {
    font-size: var(--p-arches-search-font-size);
    color: var(--p-surface-400);
    padding: 0.4rem 0 0.8rem 0;
}
</style>
