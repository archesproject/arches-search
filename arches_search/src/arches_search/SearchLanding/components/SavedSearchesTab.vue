<script setup lang="ts">
import { useRouter } from "vue-router";

import SavedSearchPanel from "@/arches_search/SimpleSearch/components/SavedSearchPanel.vue";

import { routeNames } from "@/arches_search/routes.ts";
import { usePendingSearchStore } from "@/arches_search/stores/usePendingSearchStore.ts";

const router = useRouter();

function onRunQuery(queryDefinition: Record<string, unknown>): void {
    usePendingSearchStore().set({ searchDefinition: queryDefinition });
    router.push({ name: routeNames.simpleSearch });
}
</script>

<template>
    <div class="saved-searches-tab">
        <SavedSearchPanel
            :should-show-header="false"
            :should-show-save-tab="false"
            @run-query="onRunQuery"
        />
    </div>
</template>

<style scoped>
.saved-searches-tab {
    inline-size: 100%;
    max-inline-size: 70rem;
    margin-inline: auto;
    block-size: 48rem;
    overflow: hidden;
    border: 0.15rem solid var(--arches-search-card-border);
    border-radius: 0.8rem;
}
</style>
