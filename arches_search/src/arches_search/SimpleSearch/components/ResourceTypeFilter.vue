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
    flex-wrap: wrap;
    gap: 0.4rem;
    padding: 0.8rem 1.6rem;
    background-color: var(--p-content-background);
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.resource-type-filter .type-btn {
    font-size: var(--p-arches-search-font-size);
}

.resource-type-filter .type-btn.active,
.resource-type-filter .type-btn.active:hover,
.resource-type-filter .p-button-outlined.p-button-secondary.type-btn:hover {
    background-color: var(--p-button-primary-background);
}

.resource-type-filter .load-error {
    color: var(--p-surface-500);
    font-size: var(--p-arches-search-font-size);
}
</style>
