<script setup lang="ts">
import { defineProps, provide, ref, onMounted } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import GroupBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/GroupBuilder.vue";
import SearchResults from "@/arches_search/AdvancedSearch/components/SearchResults/SearchResults.vue";

import {
    getAdvancedSearchFacets,
    getGraphs,
    getNodesForGraphId as fetchNodesForGraphId,
    getSearchResults as fetchSearchResults,
} from "@/arches_search/AdvancedSearch/api.ts";

import type {
    AdvancedSearchFacet,
    GroupPayload,
    SearchResults as SearchResultsPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

const PENDING = "pending";
const READY = "ready";

type NodeCacheEntry =
    | { status: typeof PENDING; pending: Promise<Record<string, unknown>[]> }
    | { status: typeof READY; nodes: Record<string, unknown>[] };

const { $gettext } = useGettext();

const props = defineProps<{
    query?: GroupPayload;
}>();

const isLoading = ref(true);
const isSearching = ref(false);
const fetchError = ref<Error | null>(null);

const rootPayload = ref<GroupPayload | undefined>(props.query);

const datatypesToAdvancedSearchFacets = ref<
    Record<string, AdvancedSearchFacet[]>
>({});

const graphs = ref<Record<string, unknown>[]>([]);
const graphIdToNodeCache = ref<Record<string, NodeCacheEntry>>({});
const searchResults = ref<SearchResultsPayload | null>(null);

const searchButtonLabel = $gettext("Search");

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
            facetsByDatatypeId: Record<string, AdvancedSearchFacet[]>,
            facet: AdvancedSearchFacet,
        ) => {
            const currentFacetList =
                facetsByDatatypeId[facet.datatype_id] ?? [];

            facetsByDatatypeId[facet.datatype_id] = [
                ...currentFacetList,
                facet,
            ];
            return facetsByDatatypeId;
        },
        {},
    );
}

async function fetchGraphs(): Promise<void> {
    graphs.value = await getGraphs();
}

async function search(): Promise<void> {
    if (!rootPayload.value) {
        fetchError.value = new Error(
            $gettext("Cannot perform search: no search query defined."),
        );
        return;
    }

    try {
        fetchError.value = null;
        isSearching.value = true;

        const searchResultsResponse = await fetchSearchResults(
            rootPayload.value,
        );

        searchResults.value = searchResultsResponse;
    } catch (possibleError) {
        fetchError.value = possibleError as Error;
        searchResults.value = null;
    } finally {
        isSearching.value = false;
    }
}
</script>

<template>
    <div
        class="advanced-search"
        :class="{ 'advanced-search--has-results': !!searchResults }"
    >
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
            <Splitter
                layout="vertical"
                class="search-splitter"
            >
                <SplitterPanel
                    style="overflow: auto"
                    :size="30"
                    :min-size="20"
                >
                    <div class="query-panel">
                        <GroupBuilder
                            :model-value="rootPayload"
                            :is-root="true"
                            @update:model-value="onUpdateRoot"
                        />

                        <Button
                            class="search-button"
                            icon="pi pi-search"
                            size="large"
                            :label="searchButtonLabel"
                            @click="search"
                        />
                    </div>
                </SplitterPanel>

                <SplitterPanel
                    style="overflow: auto"
                    :size="70"
                    :min-size="10"
                >
                    <div class="results-panel">
                        <SearchResults
                            v-if="searchResults"
                            :results="searchResults"
                            :is-searching="isSearching"
                        />
                    </div>
                </SplitterPanel>
            </Splitter>
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
    overflow: hidden;
}

.advanced-search-card {
    flex: 1;
    display: flex;
    flex-direction: column;
}

:deep(.p-card-body) {
    display: flex;
    flex-direction: column;
    flex: 1;
    gap: 0;
}

:deep(.p-card-content) {
    display: flex;
    flex-direction: column;
    flex: 1;
}

.content {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
}

.query-panel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-height: 0;
    overflow: auto;
}

.search-button {
    align-self: flex-start;
}

.search-splitter {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
}

.results-panel {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

.advanced-search:not(.advanced-search--has-results) .results-panel {
    display: none;
}

.advanced-search:not(.advanced-search--has-results) :deep(.p-splitter-gutter) {
    display: none;
}

.advanced-search:not(.advanced-search--has-results) :deep(.p-splitter-panel) {
    flex: 1 !important;
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
:deep(.p-button-icon),
:deep(.p-dropdown-item) {
    font-size: 1.2rem;
}
</style>
