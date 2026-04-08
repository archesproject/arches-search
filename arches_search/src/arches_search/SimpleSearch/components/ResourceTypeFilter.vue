<script setup lang="ts">
import { onMounted, ref } from "vue";
import Button from "primevue/button";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import { getGraphs } from "@/arches_search/AdvancedSearch/api.ts";

import type { ResourceType } from "@/arches_search/SimpleSearch/types.ts";
import type { GraphModel } from "@/arches_search/AdvancedSearch/types.ts";

const resourceTypes = ref<ResourceType[]>([]);

async function loadResourceTypes() {
    try {
        const graphs: GraphModel[] = await getGraphs();
        resourceTypes.value = graphs
            .filter((g) => g.isresource && g.is_active)
            .map((g) => ({
                id: g.graphid,
                label: g.name,
                icon: g.iconclass || "fa fa-archive",
            }));
    } catch {
        // Non-fatal: page still works without type tabs
    }
}

const { setGraph, activeGraph } = useSearchFilters();

function selectGraph(graph: { id: string } | null) {
    setGraph(graph);
}

onMounted(async () => {
    await loadResourceTypes();
});

</script>

<template>
    <div class="resource-type-filter">
        <Button
            v-for="type in resourceTypes"
            :key="type.id ?? '__all__'"
            :label="type.label"
            :icon="type.icon"
            icon-pos="left"
            size="large"
            severity="secondary"
            variant="outlined"
            :class="['type-btn', { active: activeGraph?.id === type.id }]"
            @click="selectGraph(type)"
        />
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

.type-btn {
    font-size: var(--p-arches-search-font-size);
}

.type-btn.active,
.type-btn.active:hover,
.p-button-outlined.p-button-secondary.type-btn:hover {
    background-color: var(--p-button-primary-background);
}
</style>
