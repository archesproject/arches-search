<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import GroupBuilder from "./components/GroupBuilder/GroupBuilder.vue";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { modelValue, isSearching, totalResults } = defineProps<{
    modelValue?: GroupPayload;
    isSearching: boolean;
    totalResults: number | null;
}>();

const emit = defineEmits<{
    "update:modelValue": [payload: GroupPayload];
    search: [];
    describe: [];
}>();

const matchCountLabel = computed(() => {
    if (totalResults === null) {
        return null;
    }
    return $gettext("%{count} items match your filter", {
        count: totalResults.toLocaleString(),
    });
});
</script>

<template>
    <div class="payload-builder">
        <div class="payload-builder-body">
            <GroupBuilder
                :model-value="modelValue"
                :is-root="true"
                @update:model-value="emit('update:modelValue', $event)"
            />
        </div>

        <div class="payload-builder-footer">
            <Button
                icon="pi pi-search"
                size="large"
                :label="$gettext('Search')"
                :loading="isSearching"
                :disabled="!modelValue || isSearching"
                @click="emit('search')"
            />

            <Button
                icon="pi pi-info-circle"
                size="large"
                :label="$gettext('Describe Query')"
                :disabled="!modelValue"
                @click="emit('describe')"
            />

            <span
                v-if="matchCountLabel"
                class="match-count"
            >
                {{ matchCountLabel }}
            </span>
        </div>
    </div>
</template>

<style scoped>
.payload-builder {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

.payload-builder-body {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    min-height: 0;
}

.payload-builder-body > :first-child {
    padding-inline: 3rem;
    border: 0;
}

.payload-builder-footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: var(--p-content-hover-background);
    border-top: 0.125rem solid var(--p-content-border-color);
}

.match-count {
    margin-inline-start: 1rem;
}
</style>
