<script setup lang="ts">
import { defineProps, provide, ref, onMounted } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import Card from "primevue/card";

import {
    getAdvancedSearchFacets,
    getGraphs,
    getNodesForGraphId as fetchNodesForGraphId,
    getSearchResults,
} from "@/arches_search/AdvancedSearch/api.ts";

import GroupPayloadBuilder from "@/arches_search/AdvancedSearch/components/GroupPayloadBuilder/GroupPayloadBuilder.vue";

import {
    makeEmptyGroupPayload,
    type GroupPayload,
} from "@/arches_search/AdvancedSearch/advanced-search-payload-builder.ts";

import type { AdvancedSearchFacet } from "@/arches_search/AdvancedSearch/types";

const PENDING = "pending";
const READY = "ready";

const { $gettext } = useGettext();
const props = defineProps<{ query?: GroupPayload }>();

const isLoading = ref(true);
const fetchError = ref<Error | null>(null);

const rootGroupPayload = ref<GroupPayload>(makeEmptyGroupPayload());

const datatypesToAdvancedSearchFacets = ref<
    Record<string, AdvancedSearchFacet[]>
>({});
const graphs = ref<Record<string, unknown>[]>([]);

type NodeSummary = Record<string, unknown>;
type NodeCacheEntry =
    | { status: typeof PENDING; pending: Promise<NodeSummary[]> }
    | { status: typeof READY; nodes: NodeSummary[] };

const graphIdToNodeCache = ref<Record<string, NodeCacheEntry>>({});

provide("datatypesToAdvancedSearchFacets", datatypesToAdvancedSearchFacets);
provide("graphs", graphs);
provide("getNodesForGraphId", getNodesForGraphId);

onMounted(async () => {
    try {
        isLoading.value = true;
        fetchError.value = null;
        seedRootGroup();
        await Promise.all([fetchGraphs(), fetchFacets()]);
    } catch (possibleError) {
        fetchError.value = possibleError as Error;
    } finally {
        isLoading.value = false;
    }
});

async function getNodesForGraphId(graphId: string): Promise<NodeSummary[]> {
    const existingEntry = graphIdToNodeCache.value[graphId];
    if (existingEntry?.status === PENDING) return await existingEntry.pending;
    if (existingEntry?.status === READY) return existingEntry.nodes;

    const pending = fetchNodesForGraphId(graphId)
        .then((nodesMap: Record<string, NodeSummary>) => {
            const nodesArray = Object.values(nodesMap);
            graphIdToNodeCache.value = {
                ...graphIdToNodeCache.value,
                [graphId]: { status: READY, nodes: nodesArray },
            };
            return nodesArray;
        })
        .catch((error) => {
            const { [graphId]: _omit, ...rest } = graphIdToNodeCache.value;
            graphIdToNodeCache.value = rest;
            fetchError.value = error as Error;
            throw error;
        });

    graphIdToNodeCache.value = {
        ...graphIdToNodeCache.value,
        [graphId]: { status: PENDING, pending },
    };

    return await pending;
}

async function fetchFacets(): Promise<void> {
    const facets = await getAdvancedSearchFacets();
    datatypesToAdvancedSearchFacets.value = facets.reduce(
        (
            byDatatype: Record<string, AdvancedSearchFacet[]>,
            facet: AdvancedSearchFacet,
        ) => {
            const currentList = byDatatype[facet.datatype_id] ?? [];
            byDatatype[facet.datatype_id] = [...currentList, facet];
            return byDatatype;
        },
        {},
    );
}

async function fetchGraphs(): Promise<void> {
    graphs.value = await getGraphs();
}

function seedRootGroup(): void {
    rootGroupPayload.value = props.query
        ? structuredClone(props.query)
        : makeEmptyGroupPayload();
}

async function search(): Promise<void> {
    const results = await getSearchResults(rootGroupPayload.value);

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

        <div
            v-else
            class="content"
        >
            <Card>
                <template #title>{{ $gettext("Advanced Search") }}</template>
                <template #content>
                    <GroupPayloadBuilder
                        v-model="rootGroupPayload"
                        :is-root="true"
                    />
                    <Button
                        icon="pi pi-search"
                        size="large"
                        :label="$gettext('Search')"
                        class="search-btn"
                        @click="search"
                    />
                </template>
            </Card>
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
.content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
.search-btn {
    margin-top: 1rem;
    align-self: flex-start;
}
</style>
