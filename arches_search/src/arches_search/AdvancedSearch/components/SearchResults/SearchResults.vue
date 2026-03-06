<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Skeleton from "primevue/skeleton";

import InfiniteVirtualScroller from "@/arches_search/AdvancedSearch/components/SearchResults/components/InfiniteVirtualScroller.vue";
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
    "request-page": [page: number];
}>();

const filteredResults = computed(() => {
    if (!filterText) {
        return results.resources;
    }

    return results.resources.filter((resource: ResourceData) => {
        const displayName =
            resource.descriptors?.[arches.activeLanguage]?.name ?? "";
        return displayName.toLowerCase().includes(filterText);
    });
});

function onRequestNextPage() {
    emit("request-page", results.pagination.page + 1);
}
</script>

<template>
    <div class="search-results">
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

        <InfiniteVirtualScroller
            v-else
            class="search-results-scroller"
            :items="filteredResults"
            :is-searching="isSearching"
            :has-next-page="results.pagination.has_next"
            @request-page="onRequestNextPage"
        >
            <template #item="{ item }">
                <div class="search-result-item">
                    <SearchResultItem :result="item" />
                </div>
            </template>
        </InfiniteVirtualScroller>
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

.search-results-skeleton {
    height: 100%;
}

.search-results-empty {
    margin: 5rem;
}

.search-results-scroller {
    flex: 1;
    overflow: auto;
}

.search-result-item {
    border-bottom: 0.125rem solid var(--p-content-border-color);
}
</style>
