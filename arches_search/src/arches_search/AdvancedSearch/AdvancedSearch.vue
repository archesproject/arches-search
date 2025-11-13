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
} from "@/arches_search/AdvancedSearch/api.ts";

import GroupPayloadBuilder from "@/arches_search/AdvancedSearch/components/GroupPayloadBuilder/GroupPayloadBuilder.vue";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import type { AdvancedSearchFacet } from "@/arches_search/AdvancedSearch/types";

type NodeCacheEntry =
    | { status: typeof PENDING; pending: Promise<Record<string, unknown>[]> }
    | { status: typeof READY; nodes: Record<string, unknown>[] };

const PENDING = "pending";
const READY = "ready";

const { $gettext } = useGettext();
const props = defineProps<{ query?: GroupPayload }>();

const isLoading = ref(true);
const fetchError = ref<Error | null>(null);

const rootPayload = ref<GroupPayload | undefined>(props.query);

const datatypesToAdvancedSearchFacets = ref<
    Record<string, AdvancedSearchFacet[]>
>({});
const graphs = ref([]);
const graphIdToNodeCache = ref<Record<string, NodeCacheEntry>>({});

provide("datatypesToAdvancedSearchFacets", datatypesToAdvancedSearchFacets);
provide("graphs", graphs);
provide("getNodesForGraphId", getNodesForGraphId);

onMounted(async () => {
    try {
        isLoading.value = true;
        fetchError.value = null;

        await Promise.all([fetchGraphs(), fetchFacets()]);
    } catch (possibleError) {
        fetchError.value = possibleError as Error;
    } finally {
        isLoading.value = false;
    }
});

function onUpdateRoot(updatedGroupPayload: GroupPayload): void {
    rootPayload.value = updatedGroupPayload;
}

async function getNodesForGraphId(
    graphId: string,
): Promise<Record<string, unknown>[]> {
    const existingEntry = graphIdToNodeCache.value[graphId];

    if (existingEntry?.status === PENDING) {
        return await existingEntry.pending;
    }

    if (existingEntry?.status === READY) {
        return existingEntry.nodes;
    }

    const pendingRequest = fetchNodesForGraphId(graphId)
        .then((nodesMap: Record<string, Record<string, unknown>>) => {
            const nodesArray = Object.values(nodesMap);

            graphIdToNodeCache.value = {
                ...graphIdToNodeCache.value,
                [graphId]: { status: READY, nodes: nodesArray },
            };

            return nodesArray;
        })
        .catch((error) => {
            fetchError.value = error as Error;
            throw error;
        });

    graphIdToNodeCache.value = {
        ...graphIdToNodeCache.value,
        [graphId]: { status: PENDING, pending: pendingRequest },
    };

    return await pendingRequest;
}

async function fetchFacets(): Promise<void> {
    const advancedSearchFacets = await getAdvancedSearchFacets();

    datatypesToAdvancedSearchFacets.value = advancedSearchFacets.reduce(
        (
            acc: Record<string, AdvancedSearchFacet[]>,
            facet: AdvancedSearchFacet,
        ) => {
            const currentList = acc[facet.datatype_id] ?? [];

            acc[facet.datatype_id] = [...currentList, facet];
            return acc;
        },
        {},
    );
}

async function fetchGraphs(): Promise<void> {
    graphs.value = await getGraphs();
}

async function search(): Promise<void> {
    console.log(
        "Search payload:",
        JSON.stringify(rootPayload.value ?? {}, null, 2),
    );
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
                <template #content>
                    <GroupPayloadBuilder
                        :model-value="rootPayload"
                        :is-root="true"
                        @update:model-value="onUpdateRoot"
                    />
                    <Button
                        class="search-btn"
                        icon="pi pi-search"
                        size="large"
                        :label="$gettext('Search')"
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
    font-size: 1.2rem;
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

:deep(.p-card-body) {
    gap: 0;
}

:deep(.p-inputtext),
:deep(.p-button),
:deep(.p-select),
:deep(.p-select-label),
:deep(.p-select-option),
:deep(.p-select-filter-input),
:deep(.p-selectbutton .p-button),
:deep(.p-tag),
:deep(.p-message),
:deep(.p-dropdown),
:deep(.p-dropdown-label),
:deep(.p-togglebutton-label),
:deep(.p-dropdown-item) {
    font-size: 1.2rem;
}
</style>
