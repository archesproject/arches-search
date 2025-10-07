<script setup lang="ts">
import { ref, watch } from "vue";

import Button from "primevue/button";

import GraphSelection from "@/arches_search/AdvancedSearch/components/GraphSelection/GraphSelection.vue";

import {
    getSearchResults,
    getNodes,
} from "@/arches_search/AdvancedSearch/api.ts";

import {
    initializeQueryTree,
    updateGraphSlug,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

const selectedGraph = ref<{ [key: string]: unknown } | null>(null);
const selectedGraphNodes = ref<{ [key: string]: unknown }[]>([]);

const queryTree = ref(initializeQueryTree());

watch(selectedGraph, async (newGraph) => {
    if (newGraph) {
        selectedGraphNodes.value = await getNodesForGraph(
            newGraph.graphid as string,
        );
        queryTree.value = updateGraphSlug(
            initializeQueryTree(),
            newGraph.slug as string,
        );
    }
});

async function getNodesForGraph(graphId: string) {
    return await getNodes(graphId);
}

function search() {
    if (selectedGraph.value) {
        getSearchResults(queryTree.value).then((results) => {
            console.log("Search results:", results);
        });
    }
}
</script>

<template>
    <div class="advanced-search">
        <GraphSelection @graph-selected="selectedGraph = $event" />

        <Button
            style="margin-top: 1rem"
            size="large"
            label="Search"
            icon="pi pi-search"
            :disabled="!selectedGraph"
            @click="search"
        />
    </div>
</template>

<style scoped>
.advanced-search {
    width: 100%;
    height: 100%;
    background: var(--p-content-background);
    color: var(--p-text-color);
}
</style>
