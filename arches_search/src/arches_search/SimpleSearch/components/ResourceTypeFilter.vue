<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import { getGraphs } from "@/arches_search/AdvancedSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type { GraphModel } from "@/arches_search/AdvancedSearch/types.ts";
import type { ResourceType } from "@/arches_search/SimpleSearch/types.ts";

const RESOURCE_TYPE_FALLBACK_KEY = "__all__";

const { $gettext } = useGettext();
const { setGraph, activeGraph } = useSearchFilters();

const resourceTypes = ref<ResourceType[]>([]);
const hasResourceTypeLoadError = ref(false);

const resourceTypeLoadErrorMessage = computed(() =>
    $gettext("Resource type filters are unavailable."),
);

watchEffect(async () => {
    await loadResourceTypes();
});

async function loadResourceTypes(): Promise<void> {
    try {
        hasResourceTypeLoadError.value = false;

        const graphs: GraphModel[] = await getGraphs();
        resourceTypes.value = graphs
            .filter((graph) => graph.isresource && graph.is_active)
            .map((graph) => ({
                id: graph.graphid,
                label: graph.name,
                icon: graph.iconclass,
            }));
    } catch (error) {
        console.error(error);
        resourceTypes.value = [];
        hasResourceTypeLoadError.value = true;
    }
}

function getResourceTypeButtonKey(resourceType: ResourceType): string {
    return resourceType.id ?? RESOURCE_TYPE_FALLBACK_KEY;
}

function isResourceTypeSelected(resourceType: ResourceType): boolean {
    return activeGraph.value?.id === resourceType.id;
}

function selectGraph(graph: ResourceType | null): void {
    if (activeGraph.value?.id === graph?.id) {
        setGraph(null);

        return;
    }

    setGraph(graph);
}
</script>

<template>
    <div class="resource-type-filter">
        <Button
            v-for="resourceType in resourceTypes"
            :key="getResourceTypeButtonKey(resourceType)"
            class="type-btn"
            icon-pos="left"
            severity="secondary"
            size="large"
            type="button"
            variant="outlined"
            :class="{ active: isResourceTypeSelected(resourceType) }"
            :icon="resourceType.icon"
            :label="resourceType.label"
            @click="selectGraph(resourceType)"
        />

        <span
            v-if="hasResourceTypeLoadError"
            aria-live="polite"
            class="load-error"
            role="status"
        >
            {{ resourceTypeLoadErrorMessage }}
        </span>
    </div>
</template>

<style scoped>
.resource-type-filter {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0 0 1.4rem;
    overflow-x: auto;
    scrollbar-width: none;
}

.resource-type-filter::-webkit-scrollbar {
    display: none;
}

.resource-type-filter .type-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1.2rem;
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 999rem;
    background: var(--p-content-background);
    color: var(--p-text-color);
    font-size: 1.2rem;
    font-weight: 500;
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
    transition:
        background 0.12s,
        border-color 0.12s,
        color 0.12s;
}

.resource-type-filter .type-btn:hover {
    background: var(--p-content-hover-background);
    border-color: var(--p-text-muted-color);
}

.resource-type-filter .type-btn.active,
.resource-type-filter .type-btn.active:hover {
    background: var(--p-primary-color);
    border-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color);
}

.resource-type-filter .type-btn :deep(.p-button-icon) {
    font-size: 1.1rem;
}

.resource-type-filter .load-error {
    color: var(--p-surface-500);
    font-size: var(--p-arches-search-font-size);
}
</style>
