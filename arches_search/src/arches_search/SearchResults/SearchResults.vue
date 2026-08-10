<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Skeleton from "primevue/skeleton";

import arches from "arches";

import SearchResultCard from "@/arches_search/SearchResults/SearchResultCard.vue";

import {
    fetchResourceDescriptors,
    fetchResourceInstanceLifecycleStates,
    fetchSearchReportConfig,
} from "@/arches_search/SearchResults/api.ts";

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

const { $gettext } = useGettext();

const SCROLL_THRESHOLD_PIXELS = 72;

const { results, isSearching, filterText, graphModels } = defineProps<{
    results: SearchResults;
    isSearching: boolean;
    filterText: string;
    graphModels: GraphModel[];
}>();

const graphModelsByGraphId = computed<Map<string, GraphModel>>(
    () =>
        new Map(
            graphModels.map((graphModel) => [graphModel.graphid, graphModel]),
        ),
);

const emit = defineEmits<{
    (event: "request-page", page: number): void;
}>();

const descriptorsByResourceId = ref<Record<string, ResourceDescriptorData>>({});
const configsByGraphId = ref<Map<string, SearchReportConfig | null>>(new Map());
const lifecycleStatesById = ref<Map<string, ResourceInstanceLifecycleState>>(
    new Map(),
);
const isPageRequestInFlight = ref(false);

const requestedDescriptorIds = new Set<string>();

// Bounded by graph count, not resource count, so fetched once here
// rather than resolved per result.
onMounted(async () => {
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

const visibleResources = computed<ResourceData[]>(() => {
    if (!filterText) return results.resources;
    const needle = filterText.toLowerCase();
    return results.resources.filter((resource: ResourceData) => {
        const name =
            descriptorsByResourceId.value[resource.resourceinstanceid]
                ?.descriptors?.[arches.activeLanguage]?.name ?? "";
        return name.toLowerCase().includes(needle);
    });
});

watch(
    () => results.resources,
    async (resources: ResourceData[]) => {
        if (!resources.length) return;

        const idsToFetch = resources
            .map((r) => r.resourceinstanceid)
            .filter((id) => !requestedDescriptorIds.has(id));

        if (idsToFetch.length) {
            idsToFetch.forEach((id) => requestedDescriptorIds.add(id));
            try {
                const descriptors = await fetchResourceDescriptors(idsToFetch);
                descriptorsByResourceId.value = {
                    ...descriptorsByResourceId.value,
                    ...descriptors,
                };
            } catch (error) {
                console.error("Failed to fetch resource descriptors:", error);
                idsToFetch.forEach((id) => requestedDescriptorIds.delete(id));
            }
        }

        // Deduplicate by graph_id, fetch one search config per unique graph
        const graphIdToRepresentativeResourceId = new Map<string, string>();
        for (const resource of resources) {
            const graphId =
                descriptorsByResourceId.value[resource.resourceinstanceid]
                    ?.graph_id ?? resource.graph_id;
            if (graphId && !graphIdToRepresentativeResourceId.has(graphId)) {
                graphIdToRepresentativeResourceId.set(
                    graphId,
                    resource.resourceinstanceid,
                );
            }
        }

        await Promise.all(
            [...graphIdToRepresentativeResourceId.entries()]
                .filter(([graphId]) => !configsByGraphId.value.has(graphId))
                .map(async ([graphId, resourceId]) => {
                    try {
                        const config =
                            await fetchSearchReportConfig(resourceId);
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
    },
    { immediate: true },
);

watch(
    () => isSearching,
    (isNowSearching: boolean) => {
        if (!isNowSearching) {
            isPageRequestInFlight.value = false;
        }
    },
);

function getGraphIdForResource(resource: ResourceData): string {
    return (
        descriptorsByResourceId.value[resource.resourceinstanceid]?.graph_id ??
        resource.graph_id ??
        ""
    );
}

function requestNextPage(): void {
    if (isSearching || isPageRequestInFlight.value) return;
    if (!results.pagination.has_next) return;

    isPageRequestInFlight.value = true;
    emit("request-page", results.pagination.page + 1);
}

function handleScroll(event: Event): void {
    const el = event.target as HTMLElement | null;
    if (!el) return;

    const distanceFromBottom =
        el.scrollHeight - (el.scrollTop + el.clientHeight);
    if (distanceFromBottom > SCROLL_THRESHOLD_PIXELS) return;

    requestNextPage();
}

const endOfResultsText = computed(() =>
    $gettext("%{count} results", {
        count: String(results.pagination.total_results),
    }),
);
</script>

<template>
    <div class="search-results">
        <Skeleton
            v-if="isSearching && results.resources.length === 0"
            style="height: 100%"
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
                v-for="resource in visibleResources"
                :key="resource.resourceinstanceid"
                :result="resource"
                :descriptor-data="
                    descriptorsByResourceId[resource.resourceinstanceid] ?? null
                "
                :report-config="
                    configsByGraphId.get(getGraphIdForResource(resource)) ??
                    null
                "
                :report-config-loaded="
                    configsByGraphId.has(getGraphIdForResource(resource))
                "
                :graph-model="
                    graphModelsByGraphId.get(getGraphIdForResource(resource)) ??
                    null
                "
                :lifecycle-state="
                    lifecycleStatesById.get(
                        resource.resource_instance_lifecycle_state_id ?? '',
                    ) ?? null
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
    height: 100%;
    width: 100%;
    flex: 1;
    overflow: hidden;
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
    min-height: 0;
}

.search-results-footer {
    flex-shrink: 0;
    text-align: center;
    padding: 1.6rem 2.4rem;
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
}
</style>
