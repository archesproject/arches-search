<script setup lang="ts">
import { ref, watchEffect } from "vue";

import { useGettext } from "vue3-gettext";

import GraphSelection from "@/arches_search/AdvancedSearch/components/GraphSelection/GraphSelection.vue";

import { getSearchResults } from "@/arches_search/AdvancedSearch/api.ts";

const { $gettext } = useGettext();

const selectedGraph = ref<string | null>(null);

watchEffect(() => {
    getSearchResults({
        graph_alias: "new_resource_model",
        query: {
            logic: "AND",
            clauses: [
                {
                    type: "clause",
                    node_alias: "number",
                    search_table: "numeric",
                    datatype: "number",
                    operator: ">",
                    params: [5],
                },
            ],
            groups: [],
        },
    });
});
</script>

<template>
    <div class="advanced-search">
        <GraphSelection @graph-selected="" />
    </div>
</template>

<style scoped>
.advanced-search {
    width: 100%;
    height: 100%;
    background: var(--p-content-background);
    color: var(--p-text-color);
}
</style>
