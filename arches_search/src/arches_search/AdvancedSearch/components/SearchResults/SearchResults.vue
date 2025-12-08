<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Skeleton from "primevue/skeleton";
import VirtualScroller from "primevue/virtualscroller";

import SearchResultItem from "@/arches_search/AdvancedSearch/components/SearchResults/components/SearchResultItem.vue";

import arches from "arches";

import type {
    SearchResults,
    ResourceData,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { results, isSearching, filterText } = defineProps<{
    results: SearchResults;
    isSearching: boolean;
    filterText: string;
}>();

const emit = defineEmits<{
    (event: "request-page", page: number): void;
}>();

const SCROLL_THRESHOLD_MULTIPLIER = 2;
const VIRTUAL_SCROLLER_ITEM_SIZE_PIXELS = 36;

const isPageRequestInFlight = ref(false);

const searchResultListItems = computed<ResourceData[]>(() => {
    if (!filterText) {
        return results.resources;
    }

    return results.resources.filter((resource) => {
        const displayName = getResourceDisplayName(resource);

        if (!displayName) {
            return false;
        }

        return displayName.toLowerCase().includes(filterText);
    });
});

watch(
    () => isSearching,
    (isNowSearching: boolean): void => {
        if (!isNowSearching) {
            isPageRequestInFlight.value = false;
        }
    },
);

function getResourceDisplayName(resource: ResourceData): string {
    return resource.descriptors?.[arches.activeLanguage]?.name ?? "";
}

function requestNextPage(): boolean {
    if (isSearching || isPageRequestInFlight.value) {
        return false;
    }

    if (!results.pagination.has_next) {
        return false;
    }

    isPageRequestInFlight.value = true;

    const nextPageNumber = results.pagination.page + 1;
    emit("request-page", nextPageNumber);

    return true;
}

function handleScroll(event: Event): void {
    const scrollContainerElement = event.target as HTMLElement | null;

    if (!scrollContainerElement) {
        return;
    }

    const scrollTop = scrollContainerElement.scrollTop;
    const clientHeight = scrollContainerElement.clientHeight;
    const scrollHeight = scrollContainerElement.scrollHeight;

    const distanceFromBottom = scrollHeight - (scrollTop + clientHeight);
    const thresholdPixels =
        VIRTUAL_SCROLLER_ITEM_SIZE_PIXELS * SCROLL_THRESHOLD_MULTIPLIER;

    if (distanceFromBottom > thresholdPixels) {
        return;
    }

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
        >
            <VirtualScroller
                class="search-results-content"
                :items="searchResultListItems"
                :item-size="VIRTUAL_SCROLLER_ITEM_SIZE_PIXELS"
                :append-only="true"
                :show-loader="false"
                :loading="isSearching"
                @scroll.passive="handleScroll"
            >
                <template #item="{ item }">
                    <div class="search-result-item">
                        <SearchResultItem :result="item" />
                    </div>
                </template>
            </VirtualScroller>
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
}

.search-results-content {
    flex: 1;
    overflow: auto;
}

.search-result-item {
    border-bottom: 0.125rem solid var(--p-content-border-color);
}
</style>
