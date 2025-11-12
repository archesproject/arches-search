<script setup lang="ts">
import SearchResultItem from "@/arches_search/AdvancedSearch/components/SearchResults/components/SearchResultItem.vue";

import type { SearchResults } from "@/arches_search/AdvancedSearch/types";

const { results } = defineProps<{
    results: SearchResults;
}>();
</script>
<template>
    <div class="search-results">
        <div
            v-if="results.resources.length === 0"
            class="no-results"
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
<style lang="css" scoped>
.search-results {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    overflow: hidden;
    flex: 1;
    border-top: 1px solid var(--p-content-border-color);
    margin-top: 2rem;
}
.no-results {
    margin: 5rem;
    font-size: 2rem;
}
.search-result-item {
    border-bottom: 1px solid var(--p-content-border-color);
}
.search-results-content {
    overflow: auto;
}
</style>
