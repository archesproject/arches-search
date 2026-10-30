<script setup lang="ts">
import { provide, ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "openvue/message";
import Skeleton from "openvue/skeleton";
import Splitter from "openvue/splitter";
import SplitterPanel from "openvue/splitterpanel";

import AdvancedSearchHelp from "@/arches_search/AdvancedSearch/components/AdvancedSearchHelp.vue";
import PayloadAnalyzer from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/PayloadAnalyzer.vue";
import QueryBuilder from "@/arches_search/AdvancedSearch/components/QueryBuilder/QueryBuilder.vue";
import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";
import RelatedResourcesPanel from "@/arches_search/SimpleSearch/components/RelatedResourcesPanel.vue";
import ResultsToolbar from "@/arches_search/SimpleSearch/components/ResultsToolbar.vue";

import {
    getAdvancedSearchFacets,
    getGraphs,
    getNodesForGraphId as fetchNodesForGraphId,
    getRelatableNodesTreeForGraphId as fetchRelatableNodesTreeForGraphId,
    getRelatableNodesTreeForGraphPair as fetchRelatableNodesTreeForGraphPair,
} from "@/arches_search/AdvancedSearch/api.ts";
import { provideQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import { getFromCache } from "@/arches_search/AdvancedSearch/utils/async-cache.ts";
import { fetchSearchResults } from "@/arches_search/SimpleSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import { useSidePanel } from "@/arches_search/SimpleSearch/composables/useSidePanel.ts";
import { sortSpecForValue } from "@/arches_search/SimpleSearch/utils/results-sort.ts";
import { RESULTS_SORT_RELEVANCE } from "@/arches_search/SimpleSearch/types.ts";

import type {
    AdvancedSearchFacet,
    GraphModel,
    Node,
    RelatableNodesTreeForGraphPairResponse,
    RelatableNodesTreeResponse,
    SearchResults as SearchResultsPayload,
} from "@/arches_search/AdvancedSearch/types.ts";
import type { ResultsSortValue } from "@/arches_search/SimpleSearch/types.ts";

const FIRST_RESULTS_PAGE = 1;
const RESULTS_PANEL_MIN_SIZE = 20;

const { $gettext } = useGettext();
const { advancedQuery, applyAdvancedQuery } = useSearchFilters();
const {
    isRelatedResourcesOpen,
    relatedResource,
    resultsPanelSize,
    visibleSidePanelSize,
    sidePanelMinSize,
    sidePanelContentClass,
    sidePanelStyle,
    closeSidePanel,
    onSplitterResizeStart,
    onSplitterResize,
    onSplitterResizeEnd,
} = useSidePanel();

const isLoading = ref(true);
const loadError = ref<Error | null>(null);
const graphs = ref<GraphModel[]>([]);
const datatypesToAdvancedSearchFacets = ref<
    Record<string, AdvancedSearchFacet[]>
>({});
const graphIdToNodeCache = ref({});
const graphIdToRelatableNodesTreeCache = ref({});
const graphIdPairToRelatableNodesTreeCache = ref({});
const searchResults = ref<SearchResultsPayload | null>(null);
const searchResultsInstanceKey = ref(0);
const isSearching = ref(false);
const searchError = ref<Error | null>(null);
const searchedGraphSlug = ref<string | null>(null);
const sortValue = ref<ResultsSortValue | null>(RESULTS_SORT_RELEVANCE);
const isDescribeVisible = ref(false);

provide("datatypesToAdvancedSearchFacets", datatypesToAdvancedSearchFacets);
provide("graphs", graphs);
provide("getNodesForGraphId", getNodesForGraphId);
provide("getRelatableNodesTreeForGraphId", getRelatableNodesTreeForGraphId);
provide("getRelatableNodesTreeForGraphPair", getRelatableNodesTreeForGraphPair);

const { root, prunedPayload, clearQuery } = provideQueryBuilder({
    graphs,
    datatypesToAdvancedSearchFacets,
    getNodesForGraphId,
});

watchEffect(async () => {
    try {
        isLoading.value = true;
        await Promise.all([fetchGraphs(), fetchFacets()]);
    } catch (error) {
        loadError.value = toError(error);
    } finally {
        isLoading.value = false;
    }
});

// The query applied when the page opens is searched once everything it needs
// has loaded, so arriving from Simple Search shows its results straight away.
watch(isLoading, (loading) => {
    if (!loading && advancedQuery.value) {
        searchedGraphSlug.value = advancedQuery.value.graph_slug;
        void performSearch(FIRST_RESULTS_PAGE);
    }
});

async function getNodesForGraphId(graphId: string): Promise<Node[]> {
    return await getFromCache(graphIdToNodeCache, graphId, async () => {
        const nodesMap = await fetchNodesForGraphId(graphId);
        return Object.values(nodesMap);
    });
}

async function getRelatableNodesTreeForGraphId(
    graphId: string,
): Promise<RelatableNodesTreeResponse> {
    return await getFromCache(graphIdToRelatableNodesTreeCache, graphId, () =>
        fetchRelatableNodesTreeForGraphId(graphId),
    );
}

async function getRelatableNodesTreeForGraphPair(
    graphId: string,
    otherGraphId: string,
): Promise<RelatableNodesTreeForGraphPairResponse> {
    return await getFromCache(
        graphIdPairToRelatableNodesTreeCache,
        `${graphId}::${otherGraphId}`,
        () => fetchRelatableNodesTreeForGraphPair(graphId, otherGraphId),
    );
}

async function fetchFacets(): Promise<void> {
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

async function fetchGraphs(): Promise<void> {
    graphs.value = await getGraphs();
}

function toError(error: unknown): Error {
    if (error instanceof Error) {
        return error;
    }
    return new Error(String(error));
}

async function performSearch(page: number): Promise<void> {
    if (!searchedGraphSlug.value) {
        return;
    }

    isSearching.value = true;
    searchError.value = null;
    try {
        const results = await fetchSearchResults({
            queries: advancedQuery.value ? [advancedQuery.value] : [],
            graphSlugs: [searchedGraphSlug.value],
            page,
            sort: sortSpecForValue(sortValue.value),
        });

        if (page > FIRST_RESULTS_PAGE && searchResults.value) {
            searchResults.value = {
                ...results,
                resources: [
                    ...searchResults.value.resources,
                    ...results.resources,
                ],
            };
        } else {
            searchResultsInstanceKey.value += 1;
            searchResults.value = results;
        }
    } catch (error) {
        searchError.value = toError(error);
    } finally {
        isSearching.value = false;
    }
}

function onSearch(): void {
    if (!root.value) {
        return;
    }
    applyAdvancedQuery(prunedPayload.value);
    searchedGraphSlug.value = root.value.graphSlug;
    void performSearch(FIRST_RESULTS_PAGE);
}

function onClearAll(): void {
    clearQuery();
    applyAdvancedQuery(null);
    searchedGraphSlug.value = null;
    searchResults.value = null;
    searchError.value = null;
}

function onSortValueUpdate(nextSortValue: ResultsSortValue | null): void {
    sortValue.value = nextSortValue;
    void performSearch(FIRST_RESULTS_PAGE);
}

function onRequestPage(page: number): void {
    void performSearch(page);
}
</script>

<template>
    <div class="advanced-search">
        <Skeleton
            v-if="isLoading"
            class="advanced-search-loading"
        />

        <Message
            v-else-if="loadError"
            severity="error"
        >
            {{ loadError.message }}
        </Message>

        <Splitter
            v-else
            class="advanced-search-splitter"
            @resizestart="onSplitterResizeStart"
            @resize="onSplitterResize"
            @resizeend="onSplitterResizeEnd"
        >
            <SplitterPanel
                class="advanced-search-main"
                :size="resultsPanelSize"
                :min-size="RESULTS_PANEL_MIN_SIZE"
            >
                <QueryBuilder
                    :is-searching="isSearching"
                    @search="onSearch"
                    @describe="isDescribeVisible = true"
                    @clear-all="onClearAll"
                />
                <ResultsToolbar
                    :total-results="
                        searchResults?.pagination.total_results ?? 0
                    "
                    :sort-value="sortValue"
                    :show-filters="false"
                    :show-map="false"
                    :has-map-filter="false"
                    :show-time="false"
                    :has-time-filter="false"
                    :show-saved-searches="false"
                    :show-export-results="false"
                    :hide-filters-button="true"
                    :hide-time-button="true"
                    :hide-map-button="true"
                    :hide-saved-searches-button="true"
                    :hide-export-results-button="true"
                    @update:sort-value="onSortValueUpdate"
                />
                <Message
                    v-if="searchError"
                    severity="error"
                    class="advanced-search-error"
                >
                    {{ searchError.message }}
                </Message>
                <SearchResults
                    v-else-if="searchResults"
                    :key="searchResultsInstanceKey"
                    :results="searchResults"
                    :is-searching="isSearching"
                    :filter-text="''"
                    :graph-models="graphs"
                    @request-page="onRequestPage"
                />
                <span
                    v-else
                    class="advanced-search-empty"
                >
                    {{
                        $gettext(
                            "Choose a resource model, add conditions and click Search.",
                        )
                    }}
                </span>
            </SplitterPanel>

            <SplitterPanel
                class="advanced-search-side-panel"
                :size="visibleSidePanelSize"
                :min-size="sidePanelMinSize"
                :style="sidePanelStyle"
            >
                <div
                    class="advanced-search-side-panel-content"
                    :class="sidePanelContentClass"
                >
                    <RelatedResourcesPanel
                        v-if="isRelatedResourcesOpen && relatedResource"
                        :resource-title="relatedResource.title"
                        @close="closeSidePanel()"
                    />
                    <AdvancedSearchHelp v-else />
                </div>
            </SplitterPanel>
        </Splitter>

        <PayloadAnalyzer
            v-if="prunedPayload"
            :datatypes-to-advanced-search-facets="
                datatypesToAdvancedSearchFacets
            "
            :graphs="graphs"
            :payload="prunedPayload"
            :visible="isDescribeVisible"
            @update:visible="isDescribeVisible = $event"
        />
    </div>
</template>

<style scoped>
.advanced-search {
    display: flex;
    flex-direction: column;
    block-size: 100%;
    overflow: hidden;
    background: var(--p-content-background);
    color: var(--p-text-color);
    font-size: var(--p-arches-search-font-size);
}

.advanced-search .advanced-search-loading {
    block-size: 100%;
}

.advanced-search .advanced-search-splitter {
    flex: 1;
    min-block-size: 0;
    overflow: hidden;
    border-radius: 0;
}

.advanced-search .advanced-search-main {
    display: flex;
    flex-direction: column;
    min-inline-size: 0;
    overflow: hidden;
}

.advanced-search .advanced-search-error {
    margin: 1.6rem;
}

.advanced-search .advanced-search-empty {
    padding: 2.4rem;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
}

.advanced-search .advanced-search-side-panel {
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.advanced-search .advanced-search-side-panel-content {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 20rem;
    overflow-y: auto;
    background-color: var(--arches-search-card-bg);
    opacity: 0;
    translate: 1.25rem 0;
    transition:
        opacity 180ms ease,
        translate 240ms ease;
}

.advanced-search .advanced-search-side-panel-content.side-panel-content-open {
    opacity: 1;
    translate: 0 0;
    border-inline-start: 0.1rem solid var(--p-content-border-color);
}

.advanced-search .advanced-search-splitter :deep(.p-splitter-gutter) {
    background: var(--p-content-border-color);
}
</style>
