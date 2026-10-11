<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import arches from "arches";
import MultiSelect from "primevue/multiselect";

import { fetchControlledListItems } from "@/arches_search/SimpleSearch/api.ts";

import type { Language } from "@/arches_controlled_lists/types.ts";
import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";
import type {
    ReferenceFilterOption,
    ReferenceFilterValue,
} from "@/arches_search/SimpleSearch/components/attribute-filters/types.ts";

const DEFAULT_LANGUAGE_CODE = "en";

const { $gettext } = useGettext();

const language = arches.activeLanguage;
const systemLanguage =
    arches.languages.find((lang: Language) => lang.isdefault)?.code ??
    DEFAULT_LANGUAGE_CODE;

const { node, modelValue } = defineProps<{
    node: NodeFilterConfigNode;
    modelValue: ReferenceFilterValue | null;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", value: ReferenceFilterValue): void;
}>();

const options = ref<ReferenceFilterOption[]>([]);
const isLoading = ref(false);

const controlledListId = computed<string | null>(() => {
    const listId = node.config?.controlledList;
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
            const items = await fetchControlledListItems(
                listId,
                language,
                systemLanguage,
            );
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

function onSelectionChange(value: ReferenceFilterValue): void {
    emit("update:modelValue", value);
}
</script>

<template>
    <div class="reference-filter">
        <MultiSelect
            class="reference-filter-select"
            :input-id="node.node_alias"
            :model-value="modelValue ?? []"
            :options="options"
            option-label="label"
            :loading="isLoading"
            :filter="true"
            :filter-placeholder="$gettext('Search options...')"
            :placeholder="$gettext('Select options...')"
            :show-clear="true"
            :fluid="true"
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

:deep(.p-multiselect-label) {
    font-size: 1.2rem;
}

:deep(.reference-filter-select .p-multiselect) {
    padding: 0.4rem 0.8rem;
}

.status {
    display: block;
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
    padding: 0.4rem 0 0 0;
    line-height: 1.5;
}
</style>
