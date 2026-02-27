<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Skeleton from "primevue/skeleton";

import arches from "arches";

import SearchResultCard from "@/arches_search/SearchResults/SearchResultCard.vue";

import {
    fetchResourceDescriptors,
    fetchSearchReportConfig,
} from "@/arches_search/SearchResults/api.ts";

import type {
    SearchResults,
    ResourceData,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    ResourceDescriptorData,
    SearchReportConfig,
} from "@/arches_search/SearchResults/types.ts";

const { $gettext } = useGettext();

const SCROLL_THRESHOLD_PIXELS = 72;

const { results, isSearching, filterText } = defineProps<{
    results: SearchResults;
    isSearching: boolean;
    filterText: string;
}>();

const emit = defineEmits<{
    (event: "request-page", page: number): void;
}>();

const descriptorsByResourceId = ref<Record<string, ResourceDescriptorData>>({});
const configsByGraphId = ref<Map<string, SearchReportConfig | null>>(new Map());
const isPageRequestInFlight = ref(false);

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

        const ids = resources.map((r) => r.resourceinstanceid);

        // Batch-fetch all descriptors (and graph_ids) for this page
        try {
            const descriptors = await fetchResourceDescriptors(ids);
            descriptorsByResourceId.value = {
                ...descriptorsByResourceId.value,
                ...descriptors,
            };
        } catch (error) {
            console.error("Failed to fetch resource descriptors:", error);
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
            />
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
    margin: 5rem;
}

.search-results-body {
    display: flex;
    flex-direction: column;
    flex: 1;
    overflow-y: auto;
}
</style>
