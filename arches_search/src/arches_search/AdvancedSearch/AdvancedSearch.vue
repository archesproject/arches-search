<script setup lang="ts">
import { provide, ref, watchEffect } from "vue";

import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import Skeleton from "primevue/skeleton";

import AdvancedSearchFooter from "@/arches_search/AdvancedSearch/components/AdvancedSearchFooter.vue";
import PayloadAnalyzer from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/PayloadAnalyzer.vue";
import PayloadBuilder from "@/arches_search/AdvancedSearch/components/PayloadBuilder/PayloadBuilder.vue";
import ResizablePanels from "@/arches_search/AdvancedSearch/components/ResizablePanels.vue";
import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";

import {
    getAdvancedSearchFacets,
    getGraphs,
    getNodesForGraphId as fetchNodesForGraphId,
    getRelatableNodesTreeForGraphId as fetchRelatableNodesTreeForGraphId,
    getSearchResults,
} from "@/arches_search/AdvancedSearch/api.ts";

import { getFromCache } from "@/arches_search/AdvancedSearch/utils/async-cache.ts";

import type {
    AdvancedSearchFacet,
    GroupPayload,
    SearchResults as SearchResultsPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { query } = defineProps<{
    query?: GroupPayload;
}>();

const isLoading = ref(true);
const isSearching = ref(false);
const loadError = ref<Error | null>(null);
const searchError = ref<Error | null>(null);

const searchPayload = ref<GroupPayload | undefined>(query);

const datatypesToAdvancedSearchFacets = ref<
    Record<string, AdvancedSearchFacet[]>
>({});

const graphs = ref([]);
const graphIdToNodeCache = ref({});
const graphIdToRelatableNodesTreeCache = ref({});

const searchResults = ref<SearchResultsPayload | null>(null);
const searchResultsInstanceKey = ref(0);
const searchFilterText = ref("");
const shouldShowPayloadAnalyzer = ref(false);

provide("datatypesToAdvancedSearchFacets", datatypesToAdvancedSearchFacets);
provide("graphs", graphs);
provide("getNodesForGraphId", getNodesForGraphId);
provide("getRelatableNodesTreeForGraphId", getRelatableNodesTreeForGraphId);

watchEffect(async () => {
    try {
        isLoading.value = true;
        await Promise.all([fetchGraphs(), fetchFacets()]);
    } catch (error) {
        loadError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
});

async function getNodesForGraphId(graphId: string) {
    return await getFromCache(graphIdToNodeCache, graphId, async () => {
        const nodesMap = await fetchNodesForGraphId(graphId);
        return Object.values(nodesMap);
    });
}

async function getRelatableNodesTreeForGraphId(graphId: string) {
    return await getFromCache(graphIdToRelatableNodesTreeCache, graphId, () =>
        fetchRelatableNodesTreeForGraphId(graphId),
    );
}

async function fetchFacets() {
    const facets: AdvancedSearchFacet[] = await getAdvancedSearchFacets();
    datatypesToAdvancedSearchFacets.value = facets.reduce<
        Record<string, AdvancedSearchFacet[]>
    >((facetsByDatatype, facet) => {
        facetsByDatatype[facet.datatype_id] = [
            ...(facetsByDatatype[facet.datatype_id] ?? []),
            facet,
        ];
        return facetsByDatatype;
    }, {});
}

async function fetchGraphs() {
    graphs.value = await getGraphs();
}

async function performSearch(pageNumberToLoad?: number) {
    if (!searchPayload.value) {
        searchError.value = new Error(
            $gettext("Cannot perform search: no search query defined."),
        );
        return;
    }

    try {
        searchError.value = null;
        isSearching.value = true;

        const response = await getSearchResults(searchPayload.value, {
            page: pageNumberToLoad,
        });

        if (searchResults.value) {
            searchResults.value = {
                ...searchResults.value,
                ...response,
                resources: [
                    ...searchResults.value.resources,
                    ...response.resources,
                ],
            };
        } else {
            searchResultsInstanceKey.value += 1;
            searchResults.value = response;
        }
    } catch (error) {
        searchError.value = error as Error;
        searchResults.value = null;
    } finally {
        isSearching.value = false;
    }
}

function onUpdateSearchPayload(payload: GroupPayload) {
    searchPayload.value = payload;
    searchResults.value = null;
    searchError.value = null;
}

function onDescribe() {
    shouldShowPayloadAnalyzer.value = true;
}

function onUpdateFilterText(text: string) {
    searchFilterText.value = text;
}

function onUpdatePayloadAnalyzerVisible(visible: boolean) {
    shouldShowPayloadAnalyzer.value = visible;
}

function onRequestPage(nextPageNumber: number) {
    void performSearch(nextPageNumber);
}
</script>

<template>
    <div class="advanced-search">
        <Skeleton
            v-if="isLoading"
            class="loading-skeleton"
        />

        <Message
            v-else-if="loadError"
            severity="error"
        >
            {{ loadError.message }}
        </Message>

        <template v-else>
            <ResizablePanels>
                <template #top>
                    <PayloadBuilder
                        :model-value="searchPayload"
                        :is-searching="isSearching"
                        :total-results="
                            searchResults?.pagination.total_results ?? null
                        "
                        @update:model-value="onUpdateSearchPayload"
                        @search="performSearch"
                        @describe="onDescribe"
                    />
                </template>

                <template #bottom>
                    <Message
                        v-if="searchError"
                        severity="error"
                        class="search-error"
                    >
                        {{ searchError.message }}
                    </Message>

                    <SearchResults
                        v-else-if="searchResults"
                        :key="searchResultsInstanceKey"
                        :results="searchResults"
                        :is-searching="isSearching"
                        :filter-text="searchFilterText"
                        @request-page="onRequestPage"
                    />
                </template>
            </ResizablePanels>

            <AdvancedSearchFooter
                :filter-text="searchFilterText"
                :search-results="searchResults"
                @update:filter-text="onUpdateFilterText"
            />

            <PayloadAnalyzer
                v-if="searchPayload"
                :datatypes-to-advanced-search-facets="
                    datatypesToAdvancedSearchFacets
                "
                :graphs="graphs"
                :payload="searchPayload"
                :visible="shouldShowPayloadAnalyzer"
                @update:visible="onUpdatePayloadAnalyzerVisible"
            />
        </template>
    </div>
</template>

<style scoped>
.advanced-search {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    background: var(--p-content-background);
    color: var(--p-text-color);
    overflow: hidden;
}

.loading-skeleton {
    height: 100%;
}

.search-error {
    margin: 1rem;
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
