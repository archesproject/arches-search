<script setup lang="ts">
import { ref, watchEffect } from "vue";

import GraphSelection from "@/arches_search/AdvancedSearch/components/GraphSelection/GraphSelection.vue";

import { getSearchResults } from "@/arches_search/AdvancedSearch/api.ts";

const selectedGraph = ref<string | null>(null);
console.log(selectedGraph);

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
                node_alias: "",
                search_table: "term",
                datatype: "string",
                operator: "EQUALS",
                params: ["Active"],
            },
        ],
        groups: [],
        aggregations: [
            {
                name: "funding_by_project_type",
                // "where": { "numeric_funding_awarded__value__lt": 100000 },
                group_by: [
                    {
                        alias: "Projects_by_Type",
                        search_table: "term",
                        field: "term_project_type__value",
                        node_alias: "project_type",
                    },
                ],
                metrics: [
                    {
                        alias: "Total_Funding",
                        fn: "Sum",
                        search_table: "numeric",
                        field: "numeric_funding_awarded__value",
                        node_alias: "funding_awarded",
                    },
                ],
                // order_by: ["-numeric_funding_awarded__value", "term_project_type__value"],
                //limit: 3,
            },
            {
                name: "count_by_project_type",
                where: { term_project_type__value: "Consortia" },
                group_by: [
                    {
                        alias: "Projects_by_Type",
                        search_table: "term",
                        field: "term_project_type__value",
                        node_alias: "project_type",
                    },
                ],
                metrics: [
                    {
                        alias: "Project_Count",
                        fn: "Count",
                        search_table: "term",
                        field: "term_project_type__value",
                        node_alias: "project_type",
                    },
                ],
            },
            // {
            //     "name": "average_funding_per_project",
            //     // "where": { "numeric_funding_awarded__value__lt": 100000 },
            //     "group_by": [],
            //     "metrics": [ {
            //         "alias": "Average_Funding",
            //         "fn": "Avg",
            //         "search_table": "numeric",
            //         "field": "numeric_funding_awarded__value",
            //         "node_alias": "funding_awarded"
            //     }]
            // },
            {
                name: "project_totals",
                where: {},
                aggregate: [
                    {
                        alias: "total_rows",
                        fn: "Count",
                        field: "resourceinstanceid",
                        distinct: true,
                    },
                ],
            },
            {
                name: "total_funding_awarded",
                where: {},
                aggregate: [
                    {
                        alias: "total_funding_awarded",
                        fn: "Sum",
                        search_table: "numeric",
                        field: "numeric_funding_awarded__value",
                        node_alias: "funding_awarded",
                        distinct: true,
                    },
                ],
            },
        ],
    };

    getSearchResults({
        graph_slug: "casf-project",
        query: query,
    });
});
</script>

<template>
    <div class="advanced-search">
        <GraphSelection @graph-selected="console.log($event)" />
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
