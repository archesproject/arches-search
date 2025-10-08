<script setup lang="ts">
import { ref, watch, defineProps } from "vue";
import Button from "primevue/button";

import GraphSelection from "@/arches_search/AdvancedSearch/components/GraphSelection/GraphSelection.vue";
import QueryGroup from "@/arches_search/AdvancedSearch/components/QueryGroup.vue";

import {
    getSearchResults,
    getNodes,
} from "@/arches_search/AdvancedSearch/api.ts";
import {
    initializeQueryTree,
    updateGraphSlug,
    type QueryPayload,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

const props = defineProps<{
    initialQuery?: QueryPayload;
}>();

const selectedGraph = ref<{ [key: string]: unknown } | null>(null);
const selectedGraphNodes = ref<{ [key: string]: unknown }[]>([]);
const queryTree = ref<QueryPayload>(initializeQueryTree(null));

watch(
    () => props.initialQuery,
    (_newInitialQuery) => {
        queryTree.value = {
            graph_slug: "new_resource_model",
            query: {
                logic: "AND",
                clauses: [
                    {
                        node_alias: "toenail_length",
                        search_table: null,
                        datatype: null,
                        operator: null,
                        params: [],
                    },
                ],
                groups: [
                    {
                        logic: "OR",
                        clauses: [
                            {
                                node_alias: "fingernail_length",
                                search_table: null,
                                datatype: null,
                                operator: null,
                                params: [],
                            },
                        ],
                        groups: [],
                    },
                ],
            },
            aggregations: [],
        };
    },
    { immediate: true },
);

watch(selectedGraph, async (newSelectedGraph) => {
    if (!newSelectedGraph) {
        return;
    }

    const fetchedGraphNodes = await getNodes(
        newSelectedGraph.graphid as string,
    );
    selectedGraphNodes.value = Object.values(fetchedGraphNodes);

    queryTree.value = updateGraphSlug(
        queryTree.value ?? initializeQueryTree(null),
        newSelectedGraph.slug as string,
    );
});

function search() {
    if (!queryTree.value.graph_slug) {
        return;
    }
    getSearchResults(queryTree.value).then((results) => {
        console.log("Search results:", results);
    });
}
</script>

<template>
    <div class="advanced-search">
        <GraphSelection
            :initial-graph-slug="queryTree.graph_slug"
            @graph-selected="selectedGraph = $event"
        />

        <QueryGroup
            :group="queryTree.query"
            :nodes="selectedGraphNodes"
            :config="{ nodeLabelKey: 'name', nodeValueKey: 'alias' }"
            :is-root="true"
            @reset-all="
                queryTree = initializeQueryTree(queryTree.graph_slug ?? null)
            "
        />

        <div>
            <Button
                size="large"
                label="Search"
                icon="pi pi-search"
                :disabled="!queryTree.graph_slug"
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
