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

const MINIMUM_BOTTOM_PANEL_HEIGHT_PIXELS = 0;
const MINIMUM_TOP_PANEL_HEIGHT_PIXELS = 0;

const TOP_PANEL_PERCENT_FALLBACK = 30;
const TOP_PANEL_PERCENT_CHANGE_EPSILON = 0.25;

const AUTO_GROW_COOLDOWN_MILLISECONDS = 0;
const TOP_PANEL_SCROLL_GUARD_PIXELS = 25;

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

const splitterComponentRef = ref<unknown>(null);

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

let resizeObserver: ResizeObserver | null = null;
let rafId: number | null = null;

let cooldownUntilMs = 0;
let trailingTimeoutId: number | null = null;
let trailingTopPercent: number | null = null;

let isApplyingProgrammaticSplitterResize = false;

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

        await nextTick();
        applySplitterSizingIfPossible(topPanelPercent.value);
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

    const contentElement = liveQueryPanelContentElement.value;
    if (!contentElement) {
        return;
    }

    resizeObserver = new ResizeObserver(() => {
        if (isApplyingProgrammaticSplitterResize) {
            return;
        }
        requestAutoGrowTopPanel();
    });

    resizeObserver.observe(contentElement);

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
    isApplyingProgrammaticSplitterResize = false;
}

function raf(): Promise<void> {
    return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

function clamp(minimum: number, maximum: number, value: number): number {
    return Math.max(minimum, Math.min(maximum, value));
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

        const desiredTopPanelPercent = computeDesiredTopPanelPercentIfNeeded();
        if (desiredTopPanelPercent === null) {
            return;
        }

        if (
            desiredTopPanelPercent <=
            topPanelPercent.value + TOP_PANEL_PERCENT_CHANGE_EPSILON
        ) {
            return;
        }

        const nowMs = Date.now();

        if (nowMs >= cooldownUntilMs) {
            applyTopPanelGrow(desiredTopPanelPercent);
            cooldownUntilMs = nowMs + AUTO_GROW_COOLDOWN_MILLISECONDS;
            return;
        }

        trailingTopPercent =
            trailingTopPercent === null
                ? desiredTopPanelPercent
                : Math.max(trailingTopPercent, desiredTopPanelPercent);

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

                const queuedTopPercent = trailingTopPercent;
                trailingTopPercent = null;

                if (queuedTopPercent === null) {
                    return;
                }

                if (
                    queuedTopPercent <=
                    topPanelPercent.value + TOP_PANEL_PERCENT_CHANGE_EPSILON
                ) {
                    return;
                }

                applyTopPanelGrow(queuedTopPercent);
                cooldownUntilMs = Date.now() + AUTO_GROW_COOLDOWN_MILLISECONDS;
            },
            Math.max(0, cooldownUntilMs - nowMs),
        );
    });
}

function computeInitialTopPanelPercent(): number {
    const hostElement = splitterHostElement.value;
    const naturalElement = naturalQueryPanelElement.value;

    if (!hostElement || !naturalElement) {
        return TOP_PANEL_PERCENT_FALLBACK;
    }

    const availablePixels = hostElement.getBoundingClientRect().height;
    if (availablePixels <= 0) {
        return TOP_PANEL_PERCENT_FALLBACK;
    }

    const maxTopPixels = Math.max(
        MINIMUM_TOP_PANEL_HEIGHT_PIXELS,
        availablePixels - MINIMUM_BOTTOM_PANEL_HEIGHT_PIXELS,
    );

    const naturalTopPixels =
        naturalElement.scrollHeight + TOP_PANEL_SCROLL_GUARD_PIXELS;

    const chosenTopPixels = Math.min(
        maxTopPixels,
        Math.max(MINIMUM_TOP_PANEL_HEIGHT_PIXELS, naturalTopPixels),
    );

    return clamp(5, 95, (Math.ceil(chosenTopPixels) / availablePixels) * 100);
}

function computeDesiredTopPanelPercentIfNeeded(): number | null {
    const hostElement = splitterHostElement.value;
    const bodyElement = liveQueryPanelBodyElement.value;
    const footerElement = liveQueryPanelFooterElement.value;
    const contentElement = liveQueryPanelContentElement.value;

    if (!hostElement || !bodyElement || !footerElement || !contentElement) {
        return null;
    }

    const availablePixels = hostElement.getBoundingClientRect().height;
    if (availablePixels <= 0) {
        return null;
    }

    const bodyClientPixels = bodyElement.clientHeight;
    const contentScrollPixels = contentElement.scrollHeight;

    if (
        contentScrollPixels <=
        bodyClientPixels + TOP_PANEL_SCROLL_GUARD_PIXELS
    ) {
        return null;
    }

    const footerPixels = footerElement.getBoundingClientRect().height;

    const desiredTopPixels =
        footerPixels + contentScrollPixels + TOP_PANEL_SCROLL_GUARD_PIXELS;

    const maxTopPixels = Math.max(
        MINIMUM_TOP_PANEL_HEIGHT_PIXELS,
        availablePixels - MINIMUM_BOTTOM_PANEL_HEIGHT_PIXELS,
    );

    const chosenTopPixels = Math.min(
        maxTopPixels,
        Math.max(MINIMUM_TOP_PANEL_HEIGHT_PIXELS, desiredTopPixels),
    );

    return clamp(5, 95, (Math.ceil(chosenTopPixels) / availablePixels) * 100);
}

function applyTopPanelGrow(desiredTopPercent: number): void {
    topPanelPercent.value = desiredTopPercent;

    isApplyingProgrammaticSplitterResize = true;

    void nextTick().then(() => {
        applySplitterSizingIfPossible(desiredTopPercent);

        requestAnimationFrame(() => {
            isApplyingProgrammaticSplitterResize = false;
        });
    });
}

function applySplitterSizingIfPossible(desiredTopPercent: number): void {
    const splitterInstance = splitterComponentRef.value as {
        resetState?: () => void;
        $el?: HTMLElement;
        panelSizes?: number[];
        saveState?: () => void;
    } | null;

    if (!splitterInstance) {
        return;
    }

    if (typeof splitterInstance.resetState === "function") {
        splitterInstance.resetState();
        return;
    }

    applySplitterFlexBasisFallback(splitterInstance, desiredTopPercent);
}

function applySplitterFlexBasisFallback(
    splitterInstance: {
        $el?: HTMLElement;
        panelSizes?: number[];
        saveState?: () => void;
    },
    desiredTopPercent: number,
): void {
    const splitterRootElement: HTMLElement | null =
        splitterInstance.$el ?? null;
    if (!splitterRootElement) {
        return;
    }

    const panelElements = splitterRootElement.querySelectorAll<HTMLElement>(
        ":scope > .p-splitterpanel",
    );
    if (panelElements.length < 2) {
        return;
    }

    const gutterElement =
        splitterRootElement.querySelector<HTMLElement>(
            ":scope > .p-splitter-gutter",
        ) ?? null;

    const gutterSizePixels = gutterElement?.getBoundingClientRect().height ?? 4;

    const topFlexBasis = `calc(${desiredTopPercent}% - ${gutterSizePixels}px)`;
    const bottomFlexBasis = `calc(${100 - desiredTopPercent}% - ${gutterSizePixels}px)`;

    panelElements[0].style.flexBasis = topFlexBasis;
    panelElements[1].style.flexBasis = bottomFlexBasis;

    if (Array.isArray(splitterInstance.panelSizes)) {
        splitterInstance.panelSizes = [
            desiredTopPercent,
            100 - desiredTopPercent,
        ];

        if (typeof splitterInstance.saveState === "function") {
            splitterInstance.saveState();
        }
    }
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
                    ref="splitterComponentRef"
                    layout="vertical"
                    class="search-splitter"
                    @resizeend="onSplitterResizeEnd"
                >
                    <SplitterPanel
                        v-bind="topPanelSplitterProps"
                        :min-size="10"
                    >
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

                    <SplitterPanel
                        v-bind="bottomPanelSplitterProps"
                        :min-size="10"
                    >
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
    margin-top: 1rem;
    flex: 1;
    gap: 1rem;
    min-height: 0;
    overflow: auto;
}

.query-panel-content {
    display: block;
}

.query-panel-content > :first-child {
    padding-inline: 3rem;
    border: 0;
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
