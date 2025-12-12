<script setup lang="ts">
import { provide, ref, watchEffect, computed } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import AdvancedSearchFooter from "@/arches_search/AdvancedSearch/components/AdvancedSearchFooter.vue";
import GroupBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/GroupBuilder.vue";
import PayloadAnalyzer from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/PayloadAnalyzer.vue";
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

type GraphSummary = {
    graphid?: string;
    slug?: string;
    name?: string;
    label?: string;
    [key: string]: unknown;
};

const { $gettext } = useGettext();

const { query } = defineProps<{
    query?: GroupPayload;
}>();

const isLoading = ref(true);
const isSearching = ref(false);
const fetchError = ref<Error | null>(null);

const searchPayload = ref<GroupPayload | undefined>(query);

const datatypesToAdvancedSearchFacets = ref<
    Record<string, AdvancedSearchFacet[]>
>({});

const graphs = ref<GraphSummary[]>([]);
const graphIdToNodeCache = ref<Record<string, NodeCacheEntry>>({});

const searchResults = ref<SearchResultsPayload | null>(null);
const searchResultsInstanceKey = ref(0);
const searchFilterText = ref("");

const shouldShowPayloadAnalyzer = ref(false);

const searchResultsMatchCountLabel = computed<string>(function () {
    const totalResultsCount =
        searchResults.value?.pagination.total_results ?? 0;

    return $gettext("%{count} items match your filter", {
        count: totalResultsCount.toLocaleString(),
    });
});

provide("datatypesToAdvancedSearchFacets", datatypesToAdvancedSearchFacets);
provide("graphs", graphs);
provide("getNodesForGraphId", getNodesForGraphId);

watchEffect(async () => {
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

async function performSearch(pageNumberToLoad?: number): Promise<void> {
    if (!searchPayload.value) {
        fetchError.value = new Error(
            $gettext("Cannot perform search: no search query defined."),
        );
        return;
    }

    try {
        fetchError.value = null;
        isSearching.value = true;

        const searchResultsResponse = await fetchSearchResults(
            searchPayload.value,
            { page: pageNumberToLoad },
        );

        if (searchResults.value) {
            searchResults.value = {
                ...searchResults.value,
                ...searchResultsResponse,
                resources: [
                    ...searchResults.value.resources,
                    ...searchResultsResponse.resources,
                ],
            };
        } else {
            searchResultsInstanceKey.value += 1;
            searchResults.value = searchResultsResponse;
        }
    } catch (possibleError) {
        fetchError.value = possibleError as Error;
        searchResults.value = null;
    } finally {
        isSearching.value = false;
    }
}

async function searchAtPage(pageNumberToLoad: number): Promise<void> {
    await performSearch(pageNumberToLoad);
}

function onRequestPage(nextPageNumber: number): void {
    void searchAtPage(nextPageNumber);
}

function onUpdateSearchPayload(updatedGroupPayload: GroupPayload): void {
    searchPayload.value = updatedGroupPayload;
    searchResults.value = null;
}

function onSearchButtonClick(): void {
    void performSearch();
}

function onAnalyzePayloadButtonClick(): void {
    if (!searchPayload.value) {
        return;
    }

    shouldShowPayloadAnalyzer.value = true;
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
            <Splitter
                layout="vertical"
                class="search-splitter"
            >
                <SplitterPanel :size="10">
                    <div class="query-panel">
                        <div class="query-panel-body">
                            <GroupBuilder
                                :model-value="searchPayload"
                                :is-root="true"
                                @update:model-value="onUpdateSearchPayload"
                            />
                        </div>

                        <div class="query-panel-footer">
                            <Button
                                icon="pi pi-search"
                                severity="warn"
                                size="large"
                                :label="$gettext('Search')"
                                :loading="isSearching"
                                :disabled="!searchPayload || isSearching"
                                @click="onSearchButtonClick"
                            />

                            <Button
                                icon="pi pi-info-circle"
                                size="large"
                                :label="$gettext('Describe Query')"
                                :disabled="!searchPayload"
                                @click="onAnalyzePayloadButtonClick"
                            />

                            <div
                                v-if="searchResults"
                                style="margin-inline-start: 1rem"
                            >
                                {{ searchResultsMatchCountLabel }}
                            </div>
                        </div>
                    </div>
                </SplitterPanel>

                <SplitterPanel
                    v-if="searchResults"
                    :size="90"
                >
                    <SearchResults
                        :key="searchResultsInstanceKey"
                        :results="searchResults"
                        :is-searching="isSearching"
                        :filter-text="searchFilterText"
                        @request-page="onRequestPage"
                    />
                </SplitterPanel>
            </Splitter>

            <AdvancedSearchFooter
                :filter-text="searchFilterText"
                :search-results="searchResults"
                @update:filter-text="searchFilterText = $event"
            />

            <PayloadAnalyzer
                v-if="searchPayload"
                :datatypes-to-advanced-search-facets="
                    datatypesToAdvancedSearchFacets
                "
                :graphs="graphs"
                :payload="searchPayload"
                :visible="shouldShowPayloadAnalyzer"
                @update:visible="shouldShowPayloadAnalyzer = $event"
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
    overflow: hidden;
    min-height: 0;
}

.content {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
}

.search-splitter {
    display: flex;
    flex-direction: column;
    flex: 1;
    border-radius: 0;
    min-height: 0;
}

.search-splitter :deep(.p-splitterpanel) {
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.query-panel {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

.query-panel-body {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-height: 0;
    overflow: auto;
}

.query-panel-footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: var(--p-content-hover-background);
    border-top: 0.125rem solid var(--p-content-border-color);
}

.search-splitter[data-p-resizing="true"] :deep(.query-panel-body),
.search-splitter[data-p-resizing="true"] :deep(.p-virtualscroller) {
    overflow: hidden !important;
}

:deep(.p-card-body) {
    display: flex;
    flex-direction: column;
    flex: 1;
    gap: 1rem;
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
:deep(.p-treeselect),
:deep(.p-dropdown-item) {
    font-size: 1.2rem;
}
</style>
