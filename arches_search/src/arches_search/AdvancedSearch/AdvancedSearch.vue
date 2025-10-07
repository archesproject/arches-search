<script setup lang="ts">
import { ref, watchEffect } from "vue";

import { useGettext } from "vue3-gettext";

import GraphSelection from "@/arches_search/AdvancedSearch/components/GraphSelection/GraphSelection.vue";

import { getSearchResults } from "@/arches_search/AdvancedSearch/api.ts";

const { $gettext } = useGettext();

const selectedGraph = ref<string | null>(null);

watchEffect(() => {
    // const query = {
    //         logic: "AND",
    //         clauses: [
    //             {
    //                 node_alias: "number",
    //                 search_table: "numeric",
    //                 datatype: "number",
    //                 operator: "LESS_THAN",
    //                 params: [5],
    //             },
    //         ],
    //         groups: [],
    // };

    // const query = {
    //         logic: "AND",
    //         clauses: [
    //             {
    //                 node_alias: "string",
    //                 search_table: "term",
    //                 datatype: "string",
    //                 operator: "EQUALS",
    //                 params: ["STRING"],
    //             },
    //         ],
    //         groups: [],
    // };

    // const query = {
    //     logic: "AND",
    //     clauses: [
    //         {
    //             node_alias: "number",
    //             search_table: "numeric",
    //             datatype: "number",
    //             operator: "LESS_THAN",
    //             params: [5],
    //         },
    //         {
    //             node_alias: "string",
    //             search_table: "term",
    //             datatype: "string",
    //             operator: "EQUALS",
    //             params: ["STRING"],
    //         },
    //     ],
    //     groups: [],
    // };

    // const query = {
    //     logic: "OR",
    //     clauses: [
    //         {
    //             node_alias: "number",
    //             search_table: "numeric",
    //             datatype: "number",
    //             operator: "LESS_THAN",
    //             params: [5],
    //         },
    //         {
    //             node_alias: "string",
    //             search_table: "term",
    //             datatype: "string",
    //             operator: "EQUALS",
    //             params: ["STRING"],
    //         },
    //     ],
    //     groups: [],
    // }

    // const query =  {
    //     logic: "OR",
    //     clauses: [
    //         {
    //             node_alias: "string_2",
    //             search_table: "term",
    //             datatype: "string",
    //             operator: "EQUALS",
    //             params: ["STRING TWO"],
    //         }
    //     ],
    //     groups: [
    //         {
    //             logic: "AND",
    //             clauses: [
    //                 {
    //                     node_alias: "number",
    //                     search_table: "numeric",
    //                     datatype: "number",
    //                     operator: "LESS_THAN",
    //                     params: [5],
    //                 },
    //                 {
    //                     node_alias: "string",
    //                     search_table: "term",
    //                     datatype: "string",
    //                     operator: "EQUALS",
    //                     params: ["STRING"],
    //                 },
    //             ],
    //             groups: [],
    //         }
    //     ],
    // }

    const query = {
        logic: "AND",
        clauses: [
            {
                node_alias: "string",
                search_table: "term",
                datatype: "string",
                operator: "EQUALS",
                params: ["STRING"],
            },
        ],
        groups: [
            {
                logic: "AND",
                clauses: [
                    {
                        type: "reflective",
                        search_table: "numeric",
                        left_node_alias: "fingernail_length",
                        operator: "<",
                        right_node_alias: "toenail_length",
                    },
                ],
                groups: [],
            },
        ],
        aggregations: [
            {
                name: "count_by_graph_slug",
                where: { name__isnull: false },
                group_by: ["graph__slug"],
                metrics: [
                    {
                        alias: "row_count",
                        fn: "Count",
                        field: "resourceinstanceid",
                        distinct: true,
                    },
                ],
                order_by: ["-row_count", "graph__slug"],
                limit: 6,
            },
            {
                name: "totals_with_graph_names",
                where: { name__isnull: false },
                aggregate: [
                    {
                        alias: "total_rows",
                        fn: "Count",
                        field: "resourceinstanceid",
                        distinct: true,
                    },
                ],
            },
        ],
    };

    getSearchResults({
        graph_slug: "new_resource_model",
        query: query,
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
