<script setup lang="ts">
import {
    provide,
    ref,
    watchEffect,
    computed,
    watch,
    nextTick,
    onBeforeUnmount,
    type Ref,
} from "vue";

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
    getRelatableNodesTreeForGraphId as fetchRelatableNodesTreeForGraphId,
    getSearchResults as fetchSearchResults,
} from "@/arches_search/AdvancedSearch/api.ts";

import type {
    AdvancedSearchFacet,
    GroupPayload,
    SearchResults as SearchResultsPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

const PENDING = "pending";
const READY = "ready";

const MINIMUM_BOTTOM_PANEL_HEIGHT_PIXELS = 260;
const MINIMUM_TOP_PANEL_HEIGHT_PIXELS = 160;

const TOP_PANEL_PERCENT_FALLBACK = 40;
const TOP_PANEL_PERCENT_CHANGE_EPSILON = 0.25;

const AUTO_GROW_COOLDOWN_MILLISECONDS = 250;
const TOP_PANEL_SCROLL_GUARD_PIXELS = 10;

type CacheEntry<T> =
    | { status: typeof PENDING; pending: Promise<T> }
    | { status: typeof READY; value: T };

type TreeSelectNode = {
    key: string;
    label: string;
    children?: TreeSelectNode[];
    leaf?: boolean;
    data?: Record<string, unknown>;
};

type RelatableNodesTreeResponse = {
    target_graph_id: string;
    options: TreeSelectNode[];
};

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

const graphIdToNodeCache = ref<
    Record<string, CacheEntry<Record<string, unknown>[]>>
>({});

const graphIdToRelatableNodesTreeCache = ref<
    Record<string, CacheEntry<RelatableNodesTreeResponse>>
>({});

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
provide("getRelatableNodesTreeForGraphId", getRelatableNodesTreeForGraphId);

const splitterHostElement = ref<HTMLElement | null>(null);
const naturalQueryPanelElement = ref<HTMLElement | null>(null);

const liveQueryPanelBodyElement = ref<HTMLElement | null>(null);
const liveQueryPanelFooterElement = ref<HTMLElement | null>(null);
const liveQueryPanelContentElement = ref<HTMLElement | null>(null);

const shouldRenderSplitter = ref(false);
const hasUserResizedSplitter = ref(false);

const topPanelPercent = ref<number>(TOP_PANEL_PERCENT_FALLBACK);
const bottomPanelPercent = computed<number>(() => 100 - topPanelPercent.value);

const topPanelSplitterProps = computed<Record<string, unknown>>(() =>
    hasUserResizedSplitter.value ? {} : { size: topPanelPercent.value },
);

const bottomPanelSplitterProps = computed<Record<string, unknown>>(() =>
    hasUserResizedSplitter.value ? {} : { size: bottomPanelPercent.value },
);

const splitterInstanceKey = ref(0);

let resizeObserver: ResizeObserver | null = null;
let rafId: number | null = null;

let cooldownUntilMs = 0;
let trailingTimeoutId: number | null = null;
let trailingTopPercent: number | null = null;

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

watch(
    isLoading,
    async (loading) => {
        if (loading) {
            return;
        }

        shouldRenderSplitter.value = false;

        await nextTick();
        await raf();

        topPanelPercent.value = computeInitialTopPanelPercent();

        shouldRenderSplitter.value = true;
    },
    { immediate: true },
);

watchEffect(() => {
    teardownAutoGrow();

    if (!shouldRenderSplitter.value) {
        return;
    }

    if (hasUserResizedSplitter.value) {
        return;
    }

    const el = liveQueryPanelContentElement.value;
    if (!el) {
        return;
    }

    resizeObserver = new ResizeObserver(() => requestAutoGrowTopPanel());
    resizeObserver.observe(el);

    requestAutoGrowTopPanel();
});

onBeforeUnmount(() => teardownAutoGrow());

function teardownAutoGrow(): void {
    resizeObserver?.disconnect();
    resizeObserver = null;

    if (rafId !== null) {
        cancelAnimationFrame(rafId);
        rafId = null;
    }

    if (trailingTimeoutId !== null) {
        window.clearTimeout(trailingTimeoutId);
        trailingTimeoutId = null;
    }

    trailingTopPercent = null;
}

function raf(): Promise<void> {
    return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

function clamp(min: number, max: number, value: number): number {
    return Math.max(min, Math.min(max, value));
}

function requestAutoGrowTopPanel(): void {
    if (!shouldRenderSplitter.value || hasUserResizedSplitter.value) {
        return;
    }

    if (rafId !== null) {
        cancelAnimationFrame(rafId);
    }

    rafId = requestAnimationFrame(() => {
        rafId = null;

        if (hasUserResizedSplitter.value) {
            return;
        }

        const desired = computeDesiredTopPanelPercentIfNeeded();
        if (desired === null) {
            return;
        }

        if (
            desired <=
            topPanelPercent.value + TOP_PANEL_PERCENT_CHANGE_EPSILON
        ) {
            return;
        }

        const now = Date.now();

        if (now >= cooldownUntilMs) {
            applyTopPanelGrow(desired);
            cooldownUntilMs = now + AUTO_GROW_COOLDOWN_MILLISECONDS;
            return;
        }

        trailingTopPercent =
            trailingTopPercent === null
                ? desired
                : Math.max(trailingTopPercent, desired);

        if (trailingTimeoutId !== null) {
            return;
        }

        trailingTimeoutId = window.setTimeout(
            () => {
                trailingTimeoutId = null;

                if (hasUserResizedSplitter.value) {
                    trailingTopPercent = null;
                    return;
                }

                const queued = trailingTopPercent;
                trailingTopPercent = null;

                if (queued === null) {
                    return;
                }

                if (
                    queued <=
                    topPanelPercent.value + TOP_PANEL_PERCENT_CHANGE_EPSILON
                ) {
                    return;
                }

                applyTopPanelGrow(queued);
                cooldownUntilMs = Date.now() + AUTO_GROW_COOLDOWN_MILLISECONDS;
            },
            Math.max(0, cooldownUntilMs - now),
        );
    });
}

function computeInitialTopPanelPercent(): number {
    const host = splitterHostElement.value;
    const natural = naturalQueryPanelElement.value;

    if (!host || !natural) {
        return TOP_PANEL_PERCENT_FALLBACK;
    }

    const available = host.getBoundingClientRect().height;
    if (available <= 0) {
        return TOP_PANEL_PERCENT_FALLBACK;
    }

    const maxTopPx = Math.max(
        MINIMUM_TOP_PANEL_HEIGHT_PIXELS,
        available - MINIMUM_BOTTOM_PANEL_HEIGHT_PIXELS,
    );

    const naturalTopPx = natural.scrollHeight + TOP_PANEL_SCROLL_GUARD_PIXELS;

    const chosenTopPx = Math.min(
        maxTopPx,
        Math.max(MINIMUM_TOP_PANEL_HEIGHT_PIXELS, naturalTopPx),
    );

    return clamp(5, 95, (Math.ceil(chosenTopPx) / available) * 100);
}

function computeDesiredTopPanelPercentIfNeeded(): number | null {
    const host = splitterHostElement.value;
    const body = liveQueryPanelBodyElement.value;
    const footer = liveQueryPanelFooterElement.value;
    const content = liveQueryPanelContentElement.value;

    if (!host || !body || !footer || !content) {
        return null;
    }

    const available = host.getBoundingClientRect().height;
    if (available <= 0) {
        return null;
    }

    const bodyClientPx = body.clientHeight;
    const contentScrollPx = content.scrollHeight;

    if (contentScrollPx <= bodyClientPx + TOP_PANEL_SCROLL_GUARD_PIXELS) {
        return null;
    }

    const footerPx = footer.getBoundingClientRect().height;

    const desiredTopPx =
        footerPx + contentScrollPx + TOP_PANEL_SCROLL_GUARD_PIXELS;

    const maxTopPx = Math.max(
        MINIMUM_TOP_PANEL_HEIGHT_PIXELS,
        available - MINIMUM_BOTTOM_PANEL_HEIGHT_PIXELS,
    );

    const chosenTopPx = Math.min(
        maxTopPx,
        Math.max(MINIMUM_TOP_PANEL_HEIGHT_PIXELS, desiredTopPx),
    );

    return clamp(5, 95, (Math.ceil(chosenTopPx) / available) * 100);
}

function applyTopPanelGrow(desiredTopPercent: number): void {
    topPanelPercent.value = desiredTopPercent;

    teardownAutoGrow();
    splitterInstanceKey.value += 1;
}

function onSplitterResizeEnd(): void {
    hasUserResizedSplitter.value = true;
    teardownAutoGrow();
}

async function getFromCache<T>(
    cache: Ref<Record<string, CacheEntry<T>>>,
    key: string,
    loader: () => Promise<T>,
): Promise<T> {
    const existing = cache.value[key];

    if (existing?.status === PENDING) {
        return await existing.pending;
    }

    if (existing?.status === READY) {
        return existing.value;
    }

    const pending = loader()
        .then((value) => {
            cache.value = {
                ...cache.value,
                [key]: { status: READY, value },
            };
            return value;
        })
        .catch((error) => {
            fetchError.value = error as Error;
            throw error;
        });

    cache.value = {
        ...cache.value,
        [key]: { status: PENDING, pending },
    };

    return await pending;
}

async function getNodesForGraphId(
    graphId: string,
): Promise<Record<string, unknown>[]> {
    return await getFromCache(graphIdToNodeCache, graphId, async () => {
        const nodesMap: Record<
            string,
            Record<string, unknown>
        > = await fetchNodesForGraphId(graphId);
        return Object.values(nodesMap);
    });
}

async function getRelatableNodesTreeForGraphId(
    graphId: string,
): Promise<RelatableNodesTreeResponse> {
    return await getFromCache(
        graphIdToRelatableNodesTreeCache,
        graphId,
        async () => await fetchRelatableNodesTreeForGraphId(graphId),
    );
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

function onRequestPage(nextPageNumber: number): void {
    void performSearch(nextPageNumber);
}

function onUpdateSearchPayload(updatedGroupPayload: GroupPayload): void {
    searchPayload.value = updatedGroupPayload;
    searchResults.value = null;

    requestAutoGrowTopPanel();
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
            <div
                ref="splitterHostElement"
                class="splitter-host"
            >
                <div
                    v-if="!shouldRenderSplitter"
                    class="prelayout"
                >
                    <div
                        ref="naturalQueryPanelElement"
                        class="query-panel"
                    >
                        <div class="query-panel-body prelayout-body">
                            <GroupBuilder
                                :model-value="searchPayload"
                                :is-root="true"
                                @update:model-value="onUpdateSearchPayload"
                            />
                        </div>

                        <div class="query-panel-footer">
                            <Button
                                icon="pi pi-search"
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

                    <div class="results-panel">
                        <SearchResults
                            v-if="searchResults"
                            :key="searchResultsInstanceKey"
                            :results="searchResults"
                            :is-searching="isSearching"
                            :filter-text="searchFilterText"
                            @request-page="onRequestPage"
                        />
                    </div>
                </div>

                <Splitter
                    v-else
                    :key="splitterInstanceKey"
                    layout="vertical"
                    class="search-splitter"
                    @resizeend="onSplitterResizeEnd"
                >
                    <SplitterPanel v-bind="topPanelSplitterProps">
                        <div class="query-panel">
                            <div
                                ref="liveQueryPanelBodyElement"
                                class="query-panel-body"
                            >
                                <div
                                    ref="liveQueryPanelContentElement"
                                    class="query-panel-content"
                                >
                                    <GroupBuilder
                                        :model-value="searchPayload"
                                        :is-root="true"
                                        @update:model-value="
                                            onUpdateSearchPayload
                                        "
                                    />
                                </div>
                            </div>

                            <div
                                ref="liveQueryPanelFooterElement"
                                class="query-panel-footer"
                            >
                                <Button
                                    icon="pi pi-search"
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

                    <SplitterPanel v-bind="bottomPanelSplitterProps">
                        <div class="results-panel">
                            <SearchResults
                                v-if="searchResults"
                                :key="searchResultsInstanceKey"
                                :results="searchResults"
                                :is-searching="isSearching"
                                :filter-text="searchFilterText"
                                @request-page="onRequestPage"
                            />
                        </div>
                    </SplitterPanel>
                </Splitter>
            </div>

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

.splitter-host {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
}

.prelayout {
    display: grid;
    grid-template-rows: auto 1fr;
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
    flex: 1;
    gap: 1rem;
    min-height: 0;
    overflow: auto;
}

.query-panel-content {
    display: block;
}

.prelayout-body {
    overflow: visible;
}

.query-panel-footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: var(--p-content-hover-background);
    border-top: 0.125rem solid var(--p-content-border-color);
}

.results-panel {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    overflow: hidden;
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
