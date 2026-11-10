<script setup lang="ts">
import { computed, ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Skeleton from "openvue/skeleton";

import SearchResultCard from "@/arches_search/SearchResults/SearchResultCard.vue";

import {
    fetchResourceDescriptors,
    fetchResourceInstanceLifecycleStates,
    fetchSearchReportConfig,
} from "@/arches_search/SearchResults/api.ts";
import { useResultsMapSelection } from "@/arches_search/SimpleSearch/composables/useResultsMapSelection.ts";

import type {
    SearchResults,
    ResourceData,
    GraphModel,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    ResourceDescriptorData,
    ResourceInstanceLifecycleState,
    SearchReportConfig,
} from "@/arches_search/SearchResults/types.ts";

const REQUEST_PAGE_EVENT = "request-page" as const;

const SCROLL_THRESHOLD_PIXELS = 72;

const { results, isSearching, graphModels } = defineProps<{
    results: SearchResults;
    isSearching: boolean;
    graphModels: GraphModel[];
}>();

const emit = defineEmits<{
    (event: typeof REQUEST_PAGE_EVENT, page: number): void;
}>();

const resultsMapSelection = useResultsMapSelection();
const { $gettext } = useGettext();

const descriptorsByResourceId = ref<Record<string, ResourceDescriptorData>>({});
const configsByGraphId = ref<Map<string, SearchReportConfig | null>>(new Map());
const lifecycleStatesById = ref<Map<string, ResourceInstanceLifecycleState>>(
    new Map(),
);
const isPageRequestInFlight = ref(false);

const requestedDescriptorIds = new Set<string>();

const graphModelsByGraphId = computed<Map<string, GraphModel>>(
    () =>
        new Map(
            graphModels.map((graphModel) => [graphModel.graphid, graphModel]),
        ),
);

const endOfResultsText = computed<string>(() =>
    $gettext("%{count} results", {
        count: String(results.pagination.total_results),
    }),
);

const pinnedResourceId = computed<string | null>(
    () => resultsMapSelection?.pinnedResourceId.value ?? null,
);

const listedResources = computed<ResourceData[]>(() =>
    results.resources.filter(
        (resource) => resource.resourceinstanceid !== pinnedResourceId.value,
    ),
);

const resultRowsByResourceId = computed<Map<string, ResourceData>>(
    () =>
        new Map(
            results.resources.map((resource) => [
                resource.resourceinstanceid,
                resource,
            ]),
        ),
);

watchEffect(async () => {
    try {
        const lifecycleStates = await fetchResourceInstanceLifecycleStates();
        lifecycleStatesById.value = new Map(
            lifecycleStates.map((lifecycleState) => [
                lifecycleState.id,
                lifecycleState,
            ]),
        );
    } catch (error) {
        console.error(
            "Failed to fetch resource instance lifecycle states:",
            error,
        );
    }
});

watch(
    () => results.resources,
    (resources: ResourceData[]) => {
        void loadCardData(
            resources.map((resource) => resource.resourceinstanceid),
        );
    },
    { immediate: true },
);

watch(pinnedResourceId, (resourceId) => {
    if (resourceId !== null) {
        void loadCardData([resourceId]);
    }
});

watch(
    () => isSearching,
    (isNowSearching: boolean) => {
        if (!isNowSearching) {
            isPageRequestInFlight.value = false;
        }
    },
);

async function loadCardData(resourceIds: string[]): Promise<void> {
    if (resourceIds.length === 0) {
        return;
    }

    const idsToFetch = resourceIds.filter(
        (resourceId) => !requestedDescriptorIds.has(resourceId),
    );

    if (idsToFetch.length > 0) {
        idsToFetch.forEach((resourceId) =>
            requestedDescriptorIds.add(resourceId),
        );
        try {
            const descriptors = await fetchResourceDescriptors(idsToFetch);
            descriptorsByResourceId.value = {
                ...descriptorsByResourceId.value,
                ...descriptors,
            };
        } catch (error) {
            console.error("Failed to fetch resource descriptors:", error);
            idsToFetch.forEach((resourceId) =>
                requestedDescriptorIds.delete(resourceId),
            );
        }
    }

    // Deduplicate by graph_id, fetch one search config per unique graph
    const graphIdToRepresentativeResourceId = new Map<string, string>();
    for (const resourceId of resourceIds) {
        const graphId = getGraphIdForResourceId(resourceId);
        if (graphId && !graphIdToRepresentativeResourceId.has(graphId)) {
            graphIdToRepresentativeResourceId.set(graphId, resourceId);
        }
    }

    await Promise.all(
        [...graphIdToRepresentativeResourceId.entries()]
            .filter(([graphId]) => !configsByGraphId.value.has(graphId))
            .map(async ([graphId, resourceId]) => {
                try {
                    const config = await fetchSearchReportConfig(resourceId);
                    configsByGraphId.value.set(graphId, config);
                } catch (error) {
                    console.error(
                        `Failed to fetch search config for graph ${graphId}:`,
                        error,
                    );
                    configsByGraphId.value.set(graphId, null);
                }
            }),
    );
}

function getGraphIdForResourceId(resourceId: string): string {
    return (
        descriptorsByResourceId.value[resourceId]?.graph_id ??
        resultRowsByResourceId.value.get(resourceId)?.graph_id ??
        ""
    );
}

function getReportConfigForResourceId(
    resourceId: string,
): SearchReportConfig | null {
    return (
        configsByGraphId.value.get(getGraphIdForResourceId(resourceId)) ?? null
    );
}

function isReportConfigLoadedForResourceId(resourceId: string): boolean {
    return configsByGraphId.value.has(getGraphIdForResourceId(resourceId));
}

function getGraphModelForResourceId(resourceId: string): GraphModel | null {
    return (
        graphModelsByGraphId.value.get(getGraphIdForResourceId(resourceId)) ??
        null
    );
}

function getLifecycleStateForResourceId(
    resourceId: string,
): ResourceInstanceLifecycleState | null {
    const lifecycleStateId =
        resultRowsByResourceId.value.get(resourceId)
            ?.resource_instance_lifecycle_state_id ??
        descriptorsByResourceId.value[resourceId]?.lifecycle_state_id ??
        "";
    return lifecycleStatesById.value.get(lifecycleStateId) ?? null;
}

function unpinResource(): void {
    resultsMapSelection?.unpin();
}

function requestNextPage(): void {
    if (isSearching || isPageRequestInFlight.value) {
        return;
    }
    if (!results.pagination.has_next) {
        return;
    }

    isPageRequestInFlight.value = true;
    emit(REQUEST_PAGE_EVENT, results.pagination.page + 1);
}

function handleScroll(event: Event): void {
    const scrollContainer = event.target as HTMLElement | null;
    if (!scrollContainer) {
        return;
    }

    const distanceFromBottom =
        scrollContainer.scrollHeight -
        (scrollContainer.scrollTop + scrollContainer.clientHeight);
    if (distanceFromBottom > SCROLL_THRESHOLD_PIXELS) {
        return;
    }

    requestNextPage();
}
</script>

<template>
    <div class="search-results">
        <div
            v-if="pinnedResourceId"
            class="search-results-pinned"
        >
            <div class="search-results-pinned-header">
                <span class="search-results-pinned-label">
                    <i class="pi pi-map-marker" />
                    <span>{{ $gettext("Selected on map") }}</span>
                </span>
                <Button
                    class="search-results-unpin"
                    icon="pi pi-times"
                    variant="text"
                    :label="$gettext('Unpin')"
                    @click="unpinResource"
                />
            </div>
            <SearchResultCard
                :key="pinnedResourceId"
                :resource-instance-id="pinnedResourceId"
                :descriptor-data="
                    descriptorsByResourceId[pinnedResourceId] ?? null
                "
                :report-config="getReportConfigForResourceId(pinnedResourceId)"
                :report-config-loaded="
                    isReportConfigLoadedForResourceId(pinnedResourceId)
                "
                :graph-model="getGraphModelForResourceId(pinnedResourceId)"
                :lifecycle-state="
                    getLifecycleStateForResourceId(pinnedResourceId)
                "
            />
        </div>

        <Skeleton
            v-if="isSearching && results.resources.length === 0"
            class="search-results-skeleton"
        />

        <div
            v-else-if="!isSearching && results.resources.length === 0"
            class="search-results-empty"
        >
            {{ $gettext("No results") }}
        </div>

        <div
            v-else
            class="search-results-body"
            @scroll.passive="handleScroll"
        >
            <SearchResultCard
                v-for="resource in listedResources"
                :key="resource.resourceinstanceid"
                :resource-instance-id="resource.resourceinstanceid"
                :descriptor-data="
                    descriptorsByResourceId[resource.resourceinstanceid] ?? null
                "
                :report-config="
                    getReportConfigForResourceId(resource.resourceinstanceid)
                "
                :report-config-loaded="
                    isReportConfigLoadedForResourceId(
                        resource.resourceinstanceid,
                    )
                "
                :graph-model="
                    getGraphModelForResourceId(resource.resourceinstanceid)
                "
                :lifecycle-state="
                    getLifecycleStateForResourceId(resource.resourceinstanceid)
                "
            />
        </div>

        <div
            v-if="results.resources.length > 0"
            class="search-results-footer"
        >
            — {{ endOfResultsText }} —
        </div>
    </div>
</template>

<style scoped>
.search-results {
    display: flex;
    flex-direction: column;
    block-size: 100%;
    inline-size: 100%;
    flex: 1;
    overflow: hidden;
}

.search-results-skeleton {
    block-size: 100%;
}

.search-results-pinned {
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    gap: 0.6rem;
    max-block-size: 50%;
    overflow-y: auto;
    padding-block: 1.2rem 1.6rem;
    padding-inline: 2.4rem;
    background-color: var(--arches-search-filter-map-bg);
    border-block-end: 0.1rem solid var(--arches-search-filter-map-border);
}

.search-results-pinned-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.search-results-pinned-label {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--arches-search-filter-map-text);
}

.search-results-unpin {
    font-size: 1.2rem;
    padding-block: 0.3rem;
    padding-inline: 0.8rem;
    color: var(--arches-search-filter-map-text);
}

.search-results-empty {
    padding: 4rem 2.4rem;
    text-align: center;
    font-size: 1.4rem;
    color: var(--p-text-muted-color);
}

.search-results-body {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    flex: 1;
    padding: 1.6rem 2.4rem;
    overflow-y: auto;
    min-block-size: 0;
}

.search-results-footer {
    flex-shrink: 0;
    text-align: center;
    padding: 1.6rem 2.4rem;
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
}
</style>
