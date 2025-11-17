<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Skeleton from "primevue/skeleton";

import SearchResultItem from "@/arches_search/AdvancedSearch/components/SearchResults/components/SearchResultItem.vue";

import type { SearchResults } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { results, isSearching } = defineProps<{
    results: SearchResults;
    isSearching: boolean;
}>();
</script>

<template>
    <div class="search-results">
        <div
            v-if="isSearching"
            class="search-results-skeleton"
        >
            <Skeleton class="search-results-skeleton-inner" />
        </div>

        <div
            v-else-if="results.resources.length === 0"
            class="search-results-empty"
        >
            {{ $gettext("No results") }}
        </div>

        <div
            v-else
            class="search-results-content"
        >
            <div
                v-for="result in results.resources"
                :key="result.resourceinstanceid"
                class="search-result-item"
            >
                <SearchResultItem :result="result" />
            </div>
        </div>
    </div>
</template>

<style scoped>
.search-results {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    flex: 1;
    margin-top: 2rem;
    border-top: 0.125rem solid var(--p-content-border-color);
    overflow: hidden;
}

.search-results-skeleton {
    display: flex;
    flex: 1;
    padding: 2rem;
}

.search-results-skeleton-inner {
    flex: 1;
}

.search-results-empty {
    margin: 5rem;
    font-size: 2rem;
}

.search-results-content {
    flex: 1;
    overflow: auto;
}

.search-result-item {
    border-bottom: 0.125rem solid var(--p-content-border-color);
}
</style>
