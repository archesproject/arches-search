<script setup lang="ts">
import { defineProps, provide, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";

import QueryGroup from "@/arches_search/AdvancedSearch/components/QueryGroup.vue";
import SearchResultsView from "@/arches_search/AdvancedSearch/components/SearchResults/SearchResultsView.vue";

import {
    getAdvancedSearchFacets,
    getGraphs,
    getNodesForGraphId as fetchNodesForGraphId,
    getSearchResults,
} from "@/arches_search/AdvancedSearch/api.ts";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/utils/query-tree";
import type {
    AdvancedSearchFacet,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types";

const { $gettext } = useGettext();

const { query } = defineProps<{ query?: GroupPayload }>();

const isLoading = ref(true);
const fetchError = ref<Error | null>(null);

const rootGroupPayload = ref<GroupPayload>();

const datatypesToAdvancedSearchFacets = ref<{ [datatype: string]: unknown[] }>(
    {},
);
const graphs = ref([]);

const graphIdsToNodes = ref<{ [graphId: string]: unknown[] }>({});
const inflightLoads: Map<string, Promise<unknown[]>> = new Map();
const searchResults = ref<SearchResults>({
    aggregations: {},
    resources: [],
});
provide("datatypesToAdvancedSearchFacets", datatypesToAdvancedSearchFacets);
provide("graphs", graphs);
provide("getNodesForGraphId", getNodesForGraphId);

watchEffect(async () => {
    try {
        isLoading.value = true;
        fetchError.value = null;

        seedRootGroup();

        await Promise.all([fetchGraphs(), fetchFacets()]);
    } catch (error) {
        fetchError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
});

async function getNodesForGraphId(graphId: string): Promise<unknown[]> {
    const cachedNodes = graphIdsToNodes.value[graphId];
    if (cachedNodes) {
        return cachedNodes;
    }

    const isAlreadyRequested = Boolean(inflightLoads.get(graphId));
    if (isAlreadyRequested) {
        return await inflightLoads.get(graphId)!;
    }

    const pendingNodesRequest = fetchNodesForGraphId(graphId)
        .then((nodesMap) => {
            const nodes = Object.values(nodesMap);

            graphIdsToNodes.value = {
                ...graphIdsToNodes.value,
                [graphId]: nodes,
            };
            inflightLoads.delete(graphId);

            return nodes;
        })
        .catch((error) => {
            inflightLoads.delete(graphId);
            fetchError.value = error as Error;

            throw error;
        });

    inflightLoads.set(graphId, pendingNodesRequest);
    return await pendingNodesRequest;
}

async function fetchFacets() {
    const facets = await getAdvancedSearchFacets();

    datatypesToAdvancedSearchFacets.value = facets.reduce(
        (
            datatypeToAdvancedSearchFacets: Record<
                string,
                AdvancedSearchFacet[]
            >,
            advancedSearchFacet: AdvancedSearchFacet,
        ) => {
            const existingFacetsForDatatype =
                datatypeToAdvancedSearchFacets[
                    advancedSearchFacet.datatype_id
                ] ?? [];
            datatypeToAdvancedSearchFacets[advancedSearchFacet.datatype_id] =
                existingFacetsForDatatype.concat([advancedSearchFacet]);

            return datatypeToAdvancedSearchFacets;
        },
        {},
    );
}

async function fetchGraphs() {
    graphs.value = await getGraphs();
}

function seedRootGroup() {
    if (query) {
        rootGroupPayload.value = structuredClone(query);
    } else {
        rootGroupPayload.value = {
            graph_slug: undefined,
            logic: "AND",
            clauses: [],
            groups: [],
            aggregations: [],
        };
    }
}

async function search() {
    const results = await getSearchResults(rootGroupPayload.value!);
    console.log("Search results:", results);
}
</script>

<template>
    <div class="advanced-search">
        <Skeleton
            v-if="isLoading"
            style="height: 100%"
        />

        <Message
            v-else-if="fetchError"
            severity="error"
        >
            {{ fetchError.message }}
        </Message>

        <div v-else>
            <QueryGroup :group-payload="rootGroupPayload!" />

            <Button
                icon="pi pi-search"
                size="large"
                :label="$gettext('Search')"
                style="margin-top: 1rem; align-self: flex-start"
                @click="search"
            />
            <SearchResultsView :results="searchResults"></SearchResultsView>
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
.advanced-search > div {
    height: 100%;
    display: flex;
    flex-direction: column;
}
</style>
