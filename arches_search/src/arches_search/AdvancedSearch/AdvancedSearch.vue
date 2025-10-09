<script setup lang="ts">
import { defineProps, provide, ref, watch, watchEffect } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";

import GraphSelection from "@/arches_search/AdvancedSearch/components/GraphSelection/GraphSelection.vue";
import QueryGroup from "@/arches_search/AdvancedSearch/components/QueryGroup.vue";

import {
    getAdvancedSearchFacets,
    getSearchResults,
    getNodes,
} from "@/arches_search/AdvancedSearch/api.ts";
import { initializeQueryTree } from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

import type { QueryPayload } from "@/arches_search/AdvancedSearch/utils/query-tree.ts";
import type { AdvancedSearchFacet } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { query } = defineProps<{
    query?: QueryPayload;
}>();

const isLoading = ref(false);
const configurationError = ref<Error>();

const advancedSearchFacets = ref();
const queryTree = ref<QueryPayload>(initializeQueryTree());
const selectedGraph = ref<{ [key: string]: unknown } | null>(null);
const selectedGraphNodes = ref<{ [key: string]: unknown }[]>([]);

provide("advancedSearchFacets", advancedSearchFacets);
provide("selectedGraph", selectedGraph);

watchEffect(() => {
    fetchAdvancedSearchFacets();
});

watch(
    () => query,
    (newInitialQuery) => {
        if (newInitialQuery) {
            queryTree.value = newInitialQuery;
        }
    },
    { immediate: true },
);

watch(selectedGraph, async (newSelectedGraph, previousSelectedGraph) => {
    if (!newSelectedGraph) {
        selectedGraphNodes.value = [];
        queryTree.value = initializeQueryTree(null);

        return;
    }

    await fetchNodes(newSelectedGraph.graphid as string);

    if (
        previousSelectedGraph ||
        queryTree.value.graph_slug !== newSelectedGraph.slug
    ) {
        queryTree.value = initializeQueryTree(newSelectedGraph.slug as string);
    }
});

function onGraphSelected(graph: { [key: string]: unknown } | null) {
    selectedGraph.value = graph;
}

async function fetchNodes(graphId: string) {
    try {
        const fetchedGraphNodes = await getNodes(graphId);
        selectedGraphNodes.value = Object.values(fetchedGraphNodes);
    } catch (error) {
        configurationError.value = error as Error;
    }
}

async function fetchAdvancedSearchFacets() {
    isLoading.value = true;
    try {
        const fetchedFacets = await getAdvancedSearchFacets();

        advancedSearchFacets.value = fetchedFacets.reduce(
            (
                acc: { [key: string]: AdvancedSearchFacet[] },
                facet: AdvancedSearchFacet,
            ) => {
                if (facet.datatype_id) {
                    acc[facet.datatype_id] = acc[facet.datatype_id] || [];
                    acc[facet.datatype_id].push(facet);
                }
                return acc;
            },
            {},
        );
    } catch (error) {
        configurationError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
}

async function search() {
    const results = await getSearchResults(queryTree.value!);
    console.log("Search results:", results);
}
</script>

<template>
    <div class="advanced-search">
        <Skeleton
            v-if="isLoading"
            style="height: 10rem"
        />
        <Message
            v-else-if="configurationError"
            severity="error"
        >
            {{ configurationError.message }}
        </Message>
        <div v-else>
            <GraphSelection
                :initial-graph-slug="queryTree.graph_slug"
                @update:selected-graph="onGraphSelected"
            />

            <QueryGroup
                v-if="selectedGraph"
                :group="queryTree.query"
                :nodes="selectedGraphNodes"
            />

            <Button
                icon="pi pi-search"
                size="large"
                :disabled="!queryTree.graph_slug"
                :label="$gettext('Search')"
                @click="search"
            />
        </div>
    </div>
</template>

<style scoped>
.advanced-search {
    width: 100%;
    height: 100%;
    background: var(--p-content-background);
    color: var(--p-text-color);
    display: flex;
    flex-direction: column;
}
</style>
