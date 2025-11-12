<script setup lang="ts">
import { defineProps, provide, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";

import QueryGroup from "@/arches_search/AdvancedSearch/components/QueryGroup.vue";
import SearchResultsView from "@/arches_search/AdvancedSearch/components/SearchResults/SearchResultsView.vue";

import {
    getAdvancedSearchFacets,
    getGraphs,
    getNodesForGraphId as fetchNodesForGraphId,
    getSearchResults,
} from "@/arches_search/AdvancedSearch/api.ts";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/utils/query-tree";
import type {
    AdvancedSearchFacet,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types";

const { $gettext } = useGettext();

const { query } = defineProps<{ query?: GroupPayload }>();

const isLoading = ref(true);
const fetchError = ref<Error | null>(null);

const rootGroupPayload = ref<GroupPayload>();

const datatypesToAdvancedSearchFacets = ref<{ [datatype: string]: unknown[] }>(
    {},
);
const graphs = ref([]);

const graphIdsToNodes = ref<{ [graphId: string]: unknown[] }>({});
const inflightLoads: Map<string, Promise<unknown[]>> = new Map();
const searchResults = ref<SearchResults>({
    aggregations: {},
    resources: [
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $28936 | Estimated Completion Date:2024-04-30",
                    map_popup:
                        "  |  | Funding Awarded: $28936 | Estimated Completion Date:2024-04-30",
                    name: "Opportunity Connect",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Opportunity Connect",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1aa66c8b-cf02-4504-9db4-509ab994cd46",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25080 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $25080 | Estimated Completion Date:",
                    name: "Lincoln Family",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lincoln Family",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fec4fccb-4c43-4f8d-a383-8393e45e1823",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-21",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-21",
                    name: "Digital Empowerment Program (DEP)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Empowerment Program (DEP)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fcf08b53-069f-4a57-93e7-632c621d67a1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $6415 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $6415 | Estimated Completion Date:2023-12-03",
                    name: "Senior Connection Initiative - Oak Ridge Sr. Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Senior Connection Initiative - Oak Ridge Sr. Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9263c530-3f26-40ed-b0e2-8fed4fa63caf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $4311200 | Estimated Completion Date:2026-06-15",
                    map_popup:
                        "  |  | Funding Awarded: $4311200 | Estimated Completion Date:2026-06-15",
                    name: "Get Connected! Call Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Get Connected! Call Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "080d7cc1-dede-4b25-8f6a-d1682706cbf1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $1230000 | Estimated Completion Date:2025-11-08",
                    map_popup:
                        "  |  | Funding Awarded: $1230000 | Estimated Completion Date:2025-11-08",
                    name: "Fresno State Connect",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Connect",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "de67eaa3-9927-4105-8d13-6348cc05d1ab",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    name: "Fresno State Parent University - Glenn County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - Glenn County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9c236cb0-d874-4fba-9f3c-699bf271ddc6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - KINGS COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - KINGS COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fc837fea-b793-4ca7-9f10-8a627d5aecdc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - MARIPOSA COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - MARIPOSA COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "68afbf1a-45fd-4b3c-8906-1bd0d64f9860",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2023-06-30",
                    name: "Fresno State Parent University - SAN JOAQUIN COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - SAN JOAQUIN COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a65e5a99-e2a4-4845-b7be-2fdfb5b25092",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - STANISLAUS COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - STANISLAUS COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3eb3efe4-13fd-4a8e-84a7-3540bbdeec6c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - TUOLUMNE COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - TUOLUMNE COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2d4b713a-6ca8-4a04-b4f2-09d5ed00bd65",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $136018 | Estimated Completion Date:2025-11-01",
                    map_popup:
                        "  |  | Funding Awarded: $136018 | Estimated Completion Date:2025-11-01",
                    name: "FMCI&Oth DL",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "FMCI&Oth DL",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "478c880f-6b97-41b2-9dbd-2c23d713d0f6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $31731 | Estimated Completion Date:2024-07-12",
                    map_popup:
                        "  |  | Funding Awarded: $31731 | Estimated Completion Date:2024-07-12",
                    name: "Digital Equity for Seniors-Concord",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Equity for Seniors-Concord",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a11ca969-f0f8-4ba0-8f83-588a062a83f6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $246700 | Estimated Completion Date:2026-06-10",
                    map_popup:
                        "  |  | Funding Awarded: $246700 | Estimated Completion Date:2026-06-10",
                    name: "Digital Literacy for Workforce Development: Justice Involved Individuals",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Literacy for Workforce Development: Justice Involved Individuals",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1c42b2ae-50aa-4a4c-9ec0-1e9ff07d5d37",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $28383 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $28383 | Estimated Completion Date:2023-12-31",
                    name: "JL Richard & Irene Cooper Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "JL Richard & Irene Cooper Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6ebf0119-6fa8-4b48-b6e9-9a0ceff82b20",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $29603 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $29603 | Estimated Completion Date:2023-12-31",
                    name: "Saint Mary's Garden",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Saint Mary's Garden",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7f42e9a3-daf1-47e0-9be2-45fd5e23d9a0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $151424 | Estimated Completion Date:2026-07-11",
                    map_popup:
                        "  |  | Funding Awarded: $151424 | Estimated Completion Date:2026-07-11",
                    name: "City of Lynwood DL",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "City of Lynwood DL",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fabcb8e1-19c6-45a6-83ad-db98546036d8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24629 | Estimated Completion Date:2026-06-05",
                    map_popup:
                        "  |  | Funding Awarded: $24629 | Estimated Completion Date:2026-06-05",
                    name: "City of Ontario DL",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "City of Ontario DL",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4e10df8a-175d-4932-adfd-60c8579e501e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $27165 | Estimated Completion Date:2023-04-04",
                    map_popup:
                        "  |  | Funding Awarded: $27165 | Estimated Completion Date:2023-04-04",
                    name: "San Leandro Main Library Digital Inclusion Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Leandro Main Library Digital Inclusion Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "57efc887-b685-45dc-b975-a2d3a854e2ed",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $7059 | Estimated Completion Date:2023-05-30",
                    map_popup:
                        "  |  | Funding Awarded: $7059 | Estimated Completion Date:2023-05-30",
                    name: "Computer Literacy & Technology Training - Pueblo Nuevo",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Computer Literacy & Technology Training - Pueblo Nuevo",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ef6c282e-b87a-4bf6-9600-7e0256ddc3eb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $27909 | Estimated Completion Date:2022-10-24",
                    map_popup:
                        "  |  | Funding Awarded: $27909 | Estimated Completion Date:2022-10-24",
                    name: "Compass Family Digital Inclusion",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Compass Family Digital Inclusion",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "017c7722-29fe-4a1e-910d-c2cf6ca86113",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $29935 | Estimated Completion Date:2021-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $29935 | Estimated Completion Date:2021-09-30",
                    name: "Connected At Home",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connected At Home",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2d949b64-ff80-4ceb-b90c-fbad68de8aac",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2025-10-04",
                    map_popup:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2025-10-04",
                    name: "Community Technology Associate (CTA) Digital Literacy Program - Mission District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Community Technology Associate (CTA) Digital Literacy Program - Mission District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e468906b-88ce-4fdd-81a6-f1a96b35e0cb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $38487 | Estimated Completion Date:2024-08-31",
                    map_popup:
                        "  |  | Funding Awarded: $38487 | Estimated Completion Date:2024-08-31",
                    name: "1275 South Winery Avenue (Summer Park)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "1275 South Winery Avenue (Summer Park)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "149a9167-3b33-4f73-8b77-de1a206a1d32",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-12-03",
                    name: "1777 Newbury Drive-San Jose",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "1777 Newbury Drive-San Jose",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "06179263-c4b0-4e0a-b7c7-815e6b7e11d0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $15480 | Estimated Completion Date:2025-04-07",
                    map_popup:
                        "  |  | Funding Awarded: $15480 | Estimated Completion Date:2025-04-07",
                    name: "4838 East Laurel Ave. (Arbor Court)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "4838 East Laurel Ave. (Arbor Court)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4e8a8306-2c80-4f7f-a9e0-f99ec3f340a2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $9048 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $9048 | Estimated Completion Date:2023-12-03",
                    name: "600 A Street P.O. Box 1055-Pt. Reyes Station",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "600 A Street P.O. Box 1055-Pt. Reyes Station",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4dd5bba3-f057-4a89-a072-115011b4f05c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-12-03",
                    name: "990 College Ave.-St. Helena",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "990 College Ave.-St. Helena",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "94fafeaa-b685-42ef-9cf9-6114b3af3ffa",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $18850 | Estimated Completion Date:2024-01-10",
                    map_popup:
                        "  |  | Funding Awarded: $18850 | Estimated Completion Date:2024-01-10",
                    name: "Mackey Terrrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mackey Terrrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c6f5858e-1b2a-45a6-833d-1722fa0150f1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $27619 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $27619 | Estimated Completion Date:2023-03-31",
                    name: "Alta Mira Family",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Alta Mira Family",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "05d72370-5b34-4918-9217-c724af720dcf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54676 | Estimated Completion Date:2025-04-04",
                    map_popup:
                        "  |  | Funding Awarded: $54676 | Estimated Completion Date:2025-04-04",
                    name: "Central",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Central",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3ea45c7a-1be4-4ce8-b05f-53792317468a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $48217 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $48217 | Estimated Completion Date:2023-03-31",
                    name: "Eden Palms",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Eden Palms",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "47996c49-6489-4fa8-ac19-ec0784bbbb92",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $65392 | Estimated Completion Date:2025-04-04",
                    map_popup:
                        "  |  | Funding Awarded: $65392 | Estimated Completion Date:2025-04-04",
                    name: "Hayward",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hayward",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b0a78685-7f8c-4b15-b37a-0726be94b6da",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $75152 | Estimated Completion Date:2025-04-04",
                    map_popup:
                        "  |  | Funding Awarded: $75152 | Estimated Completion Date:2025-04-04",
                    name: "San Jose",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Jose",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "16630b4a-95c7-48bc-b458-e006f0587cfc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $12372 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $12372 | Estimated Completion Date:2023-12-05",
                    name: "EngAGE in Digital Literacy - Olivera Senior Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "EngAGE in Digital Literacy - Olivera Senior Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "50da9109-c53e-4053-a92c-d35abeb82df4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $15953 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $15953 | Estimated Completion Date:2023-07-31",
                    name: "The Alder: Digital Literacy in Supportive Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Alder: Digital Literacy in Supportive Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5dab99fc-2f92-4532-ba86-e82b15181e46",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $87750 | Estimated Completion Date:2025-10-04",
                    map_popup:
                        "  |  | Funding Awarded: $87750 | Estimated Completion Date:2025-10-04",
                    name: "Digital Connections Bay Area",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Connections Bay Area",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3e8a6e9b-4122-4030-9554-f75ef47ca87b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $83825 | Estimated Completion Date:2025-10-04",
                    map_popup:
                        "  |  | Funding Awarded: $83825 | Estimated Completion Date:2025-10-04",
                    name: "Digital Connections Los Angeles",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Connections Los Angeles",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "502092be-1def-42ed-8945-d56b28e8eeae",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $71764 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $71764 | Estimated Completion Date:2023-12-03",
                    name: "Expanding Digital Literacy for the Aging",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Expanding Digital Literacy for the Aging",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e9388730-242b-49e1-a2e7-cc38f3d72269",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $17696 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $17696 | Estimated Completion Date:2023-06-30",
                    name: "Access for All - Redwood City",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Access for All - Redwood City",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bc5109f8-6bdf-4b82-bc9b-e53a056c830b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $142409 | Estimated Completion Date:2024-11-12",
                    map_popup:
                        "  |  | Funding Awarded: $142409 | Estimated Completion Date:2024-11-12",
                    name: "San Jose ON",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Jose ON",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c2a97f6f-df73-4a6c-b259-e7ecf189e094",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $75300 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $75300 | Estimated Completion Date:2025-04-03",
                    name: "Adelanto Elementary District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Adelanto Elementary District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b8617565-b174-4a1e-a015-0f2bd8296b0e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $11472 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $11472 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Apple Valley_92307-08",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Apple Valley_92307-08",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2078a54e-aff8-4df4-9b4b-b009bad7daeb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $70500 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $70500 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Chino Hills_91709",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Chino Hills_91709",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9da7af95-0e60-4041-9ce9-efcea86d85f7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $66950 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $66950 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Fontana_92336",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Fontana_92336",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "eb5f501c-9c0f-4c35-8678-458f33462393",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49176 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $49176 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Montclair_91763",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Montclair_91763",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "092067e2-e966-43c4-a087-51602511b846",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $18430 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $18430 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_RanchoCuc_91701",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_RanchoCuc_91701",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "aa9d1e86-898e-45ed-849a-f6272998e217",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $72198 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $72198 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Redlands_92373",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Redlands_92373",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "32132cdd-865c-4c5c-ae28-381a86bdbdb1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $55866 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $55866 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Snbrndo_92407",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Snbrndo_92407",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2320cbe7-b366-4e16-8228-8f67e837cd75",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $29647 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $29647 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Upland_91786",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Upland_91786",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ca587867-c414-4ff9-8c8d-fbd0f67dc428",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $52315 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $52315 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_YuccaValley_92284",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_YuccaValley_92284",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d769caeb-81ab-40cc-a781-32de7a156218",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74700 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74700 | Estimated Completion Date:2025-04-03",
                    name: "Chino Valley Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Chino Valley Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "99bcf3fb-fba1-49d9-be30-90c531f4b87b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $73800 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $73800 | Estimated Completion Date:2025-04-03",
                    name: "Fontana Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fontana Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8076c842-e9cb-4c88-bc6e-48b527bfc314",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $77200 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $77200 | Estimated Completion Date:2025-04-03",
                    name: "Morongo Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Morongo Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "52fcc956-e965-4e5c-b9fa-6daac5ddc67b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $73100 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $73100 | Estimated Completion Date:2025-04-03",
                    name: "Rialto Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Rialto Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "67df4c4e-aac2-44ee-82e6-12e74cbf7d8b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $76100 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $76100 | Estimated Completion Date:2025-04-03",
                    name: "Silver Valley Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Silver Valley Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3ed3c79f-ce25-477a-9bd1-b86fe9a38a42",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74450 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74450 | Estimated Completion Date:2025-04-03",
                    name: "Yucaipa-Calimesa Joint District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Yucaipa-Calimesa Joint District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7bf6a013-734f-4020-b1d9-c244fc54c285",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $60402 | Estimated Completion Date:2022-07-30",
                    map_popup:
                        "  |  | Funding Awarded: $60402 | Estimated Completion Date:2022-07-30",
                    name: "Digital Literacy in Castroville",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Literacy in Castroville",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "43908f12-4a34-4e3f-847d-5dded463daf3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $57598 | Estimated Completion Date:2025-10-10",
                    map_popup:
                        "  |  | Funding Awarded: $57598 | Estimated Completion Date:2025-10-10",
                    name: "Southwest Fresno - Legacy Commons",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Southwest Fresno - Legacy Commons",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "178fc545-5bf9-4543-bb2c-c8a083e9ebe4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $708560 | Estimated Completion Date:2023-06-03",
                    map_popup:
                        "  |  | Funding Awarded: $708560 | Estimated Completion Date:2023-06-03",
                    name: "human-I-T Connect",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "human-I-T Connect",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5ae7a1cb-8210-4583-9356-1b2a89482aa5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $539247 | Estimated Completion Date:2023-08-27",
                    map_popup:
                        "  |  | Funding Awarded: $539247 | Estimated Completion Date:2023-08-27",
                    name: "Digital Literacy for Foster Youth",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Literacy for Foster Youth",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9fbafbda-ca2e-4f00-b082-b5ca8f1d56ad",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $97750 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $97750 | Estimated Completion Date:2022-12-31",
                    name: "Cybernauts at LAPL",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cybernauts at LAPL",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "68706c6d-f394-484b-94d8-2fc35070b1ba",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $84297 | Estimated Completion Date:2019-12-15",
                    map_popup:
                        "  |  | Funding Awarded: $84297 | Estimated Completion Date:2019-12-15",
                    name: "Conectate y Avanza (Connect and Advance)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Conectate y Avanza (Connect and Advance)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "980eddf8-df68-4830-8060-6219dd2cb69f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $23152 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $23152 | Estimated Completion Date:2022-06-30",
                    name: "Public Access Upgrade, Grass Valley Library",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Public Access Upgrade, Grass Valley Library",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1a48cae0-7f4e-4953-b1d4-4615f6aee027",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $41799 | Estimated Completion Date:2026-06-07",
                    map_popup:
                        "  |  | Funding Awarded: $41799 | Estimated Completion Date:2026-06-07",
                    name: "Oakland Adult and Career Learning (OACE) - Digital Literacy Instruction",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Oakland Adult and Career Learning (OACE) - Digital Literacy Instruction",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fce2d971-561b-4a12-912e-631762c95f83",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $93250 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $93250 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Call Center Broadband Signups - Solano County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Call Center Broadband Signups - Solano County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "30d30db2-bd98-4108-9942-1fa20939e06e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Digital Literacy - Solano County Housing Sites",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Digital Literacy - Solano County Housing Sites",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a699cd25-ee32-4ad7-a5e7-c45a078708dc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $3171 | Estimated Completion Date:2020-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $3171 | Estimated Completion Date:2020-12-31",
                    name: "Get Connected Oakland- OUSD District 3 High Schools",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Get Connected Oakland- OUSD District 3 High Schools",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2cd68dba-50a8-46cf-9d39-6ce7b7f51a59",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $39243 | Estimated Completion Date:2022-04-18",
                    map_popup:
                        "  |  | Funding Awarded: $39243 | Estimated Completion Date:2022-04-18",
                    name: "Technology Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Technology Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d3719bb8-9094-45fb-a598-e20bbd748080",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $52028 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $52028 | Estimated Completion Date:2022-12-31",
                    name: "Montebello, CA Community Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Montebello, CA Community Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "493b13cc-309e-4f28-97ee-5c9b652539ce",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $40472 | Estimated Completion Date:2022-08-31",
                    map_popup:
                        "  |  | Funding Awarded: $40472 | Estimated Completion Date:2022-08-31",
                    name: "RaB Broadband Access 1.0 (N Location)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "RaB Broadband Access 1.0 (N Location)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5522dbd5-ee06-4ef9-909e-a93370c6c2cc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-16",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-16",
                    name: "Central Riverside County ACP Outreach Call Center Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Central Riverside County ACP Outreach Call Center Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1615dbc5-4b68-4253-996d-b7be9edfc485",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $147000 | Estimated Completion Date:2025-10-03",
                    map_popup:
                        "  |  | Funding Awarded: $147000 | Estimated Completion Date:2025-10-03",
                    name: "Digital Inclusion- Literacy workshops",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Inclusion- Literacy workshops",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8199e7e5-6dc2-4da6-bf0e-7b4da7ef498a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50000 | Estimated Completion Date:2025-03-26",
                    map_popup:
                        "  |  | Funding Awarded: $50000 | Estimated Completion Date:2025-03-26",
                    name: "Satellite St. Andrew's Manor, LLC, and and 3268 San Pablo, LP",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Satellite St. Andrew's Manor, LLC, and and 3268 San Pablo, LP",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9ba9e489-35f4-4a3a-b872-9ed1be13c202",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $30833 | Estimated Completion Date:2022-12-22",
                    map_popup:
                        "  |  | Funding Awarded: $30833 | Estimated Completion Date:2022-12-22",
                    name: "Sand Creek",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sand Creek",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d3849b8c-cea2-41b5-b934-360bf1c4dc46",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $12685 | Estimated Completion Date:2021-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $12685 | Estimated Completion Date:2021-06-30",
                    name: "Bell Tech Center-Broadband",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bell Tech Center-Broadband",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2be258ac-e9ed-47db-9cbf-31e6efad8cf2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $83466 | Estimated Completion Date:2021-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $83466 | Estimated Completion Date:2021-06-30",
                    name: "Whittier Tech Center-Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Whittier Tech Center-Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0140c7e4-2444-4c2a-a3ff-11d17b4a3dce",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $18850 | Estimated Completion Date:2023-01-12",
                    map_popup:
                        "  |  | Funding Awarded: $18850 | Estimated Completion Date:2023-01-12",
                    name: "Westside Courts Digital Bridge",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Westside Courts Digital Bridge",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "26c7cbbf-6808-4bf3-9663-3a58d513d634",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $77700 | Estimated Completion Date:2023-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $77700 | Estimated Completion Date:2023-09-30",
                    name: "Tech Exchange: Oakland Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Oakland Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a9baf213-a077-4df8-85d7-55ecc6ec2202",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $97750 | Estimated Completion Date:2021-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $97750 | Estimated Completion Date:2021-09-30",
                    name: "Tech Hub",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Hub",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d28538a5-9e70-4933-8176-a46b670957d5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $68803 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $68803 | Estimated Completion Date:2023-06-30",
                    name: "Access San Jose",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Access San Jose",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "07d307db-e3d9-4065-880c-b6fc8481e357",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $64793 | Estimated Completion Date:2023-01-31",
                    map_popup:
                        "  |  | Funding Awarded: $64793 | Estimated Completion Date:2023-01-31",
                    name: "VIVO Computer Training for Broadband Access",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "VIVO Computer Training for Broadband Access",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f09466bb-ec8b-4f17-83c6-675bf71734f3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $99452 | Estimated Completion Date:2024-04-30",
                    map_popup:
                        "  |  | Funding Awarded: $99452 | Estimated Completion Date:2024-04-30",
                    name: "WISE Connections",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "WISE Connections",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "244b8cf7-228a-4eca-bc92-e33fff063ea2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $1000000 | Estimated Completion Date:2028-02-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $1000000 | Estimated Completion Date:2028-02-01",
                    name: "Connected Central Coast Phase IV",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connected Central Coast Phase IV",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "51bb3655-eb18-4a48-b895-7313062e1154",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2025-11-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2025-11-01",
                    name: "Inland Empire Broadband Implementation",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Inland Empire Broadband Implementation",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2f0d1b53-3225-47c2-9f5c-66cb06e2a098",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $572000 | Estimated Completion Date:2025-11-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $572000 | Estimated Completion Date:2025-11-01",
                    name: "Redwood Coast Connect Deployment Support",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Redwood Coast Connect Deployment Support",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "159b1a40-9a88-4e51-8b48-1c7b6e9a2bff",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $999970 | Estimated Completion Date:2028-05-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $999970 | Estimated Completion Date:2028-05-01",
                    name: "Connecting Upstate California",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connecting Upstate California",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "df0c8b07-4667-4fa1-8af9-3b3e88acbee9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $61952 | Estimated Completion Date:2011-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $61952 | Estimated Completion Date:2011-05-01",
                    name: "Hopland",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hopland",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7a9cfd6a-27f3-43a9-bdcf-67893df2b0e5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $18392 | Estimated Completion Date:2011-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $18392 | Estimated Completion Date:2011-05-01",
                    name: "Comptche",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Comptche",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c07d73fd-73a2-4a25-9d99-b85357df387c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $56628 | Estimated Completion Date:2011-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $56628 | Estimated Completion Date:2011-05-01",
                    name: "Alta/Blue Canyon",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Alta/Blue Canyon",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0000b2a9-00bb-49d6-b558-9834538ec600",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $640698 | Estimated Completion Date:2016-07-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $640698 | Estimated Completion Date:2016-07-01",
                    name: "Poker Flat Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Poker Flat Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9fb77a85-8f90-4348-8c3e-af7b7601484b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $848063 | Estimated Completion Date:2023-08-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $848063 | Estimated Completion Date:2023-08-01",
                    name: "Brookside Country Club",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Brookside Country Club",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9ff481e7-ffb8-4356-aacc-e042bf169095",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $705410 | Estimated Completion Date:2024-03-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $705410 | Estimated Completion Date:2024-03-01",
                    name: "Darlene Road",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Darlene Road",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dcb79adc-9ae6-4c2d-b737-92bef7387afc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $100444 | Estimated Completion Date:2010-03-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $100444 | Estimated Completion Date:2010-03-01",
                    name: "Birds Landing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Birds Landing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1a10637b-6433-48aa-b413-4ec3ff102499",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $415438 | Estimated Completion Date:2022-12-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $415438 | Estimated Completion Date:2022-12-01",
                    name: "Sutter Placer",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sutter Placer",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "18fdc0e6-0dc2-4581-bd53-eecd1232fdaa",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $692889 | Estimated Completion Date:2022-06-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $692889 | Estimated Completion Date:2022-06-01",
                    name: "Weimar Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Weimar Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "eae8bd72-e2df-4698-adf4-19194cdf4b33",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $168171 | Estimated Completion Date:2012-11-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $168171 | Estimated Completion Date:2012-11-01",
                    name: "Havasu Palms and Black Meadow",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Havasu Palms and Black Meadow",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "13c59c1d-5a78-46e1-8a85-f70d5cb9a4e2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1491078 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1491078 | Estimated Completion Date:2025-12-31",
                    name: "Nicasio",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Nicasio",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "19571309-2ff6-44ad-a0a9-889e4a955460",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $1076062 | Estimated Completion Date:2022-02-01",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $1076062 | Estimated Completion Date:2022-02-01",
                    name: "Light Saber",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Light Saber",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d84ace7e-6972-4fbc-892b-0a0df13597ad",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Middle-Mile | Funding Awarded: $1721280 | Estimated Completion Date:2014-03-01",
                    map_popup:
                        " Infrastructure | Middle-Mile | Funding Awarded: $1721280 | Estimated Completion Date:2014-03-01",
                    name: "Plumas-Sierra Telecom middle-mile",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Plumas-Sierra Telecom middle-mile",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "46d7b9cd-7e5f-48c5-bf3d-ab2559e44a6d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $1270872 | Estimated Completion Date:2022-07-01",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $1270872 | Estimated Completion Date:2022-07-01",
                    name: "Plumas Eureka-Johnsville",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Plumas Eureka-Johnsville",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "710d3dc4-522d-4831-9263-bbd84d23259d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $11108189 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $11108189 | Estimated Completion Date:2025-12-31",
                    name: "Southern Lassen",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Southern Lassen",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f9ee99d3-6474-4949-aeae-cb572cee887a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $239991 | Estimated Completion Date:2017-02-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $239991 | Estimated Completion Date:2017-02-01",
                    name: "Gigafy Backus",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gigafy Backus",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8292d67d-19cf-4e59-8d11-725b8a068285",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $3124490 | Estimated Completion Date:2018-09-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $3124490 | Estimated Completion Date:2018-09-01",
                    name: "Gigafy North 395",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gigafy North 395",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "31eadbc2-81ce-41a0-ab3b-1dc5ae1e5ca5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $10083005 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $10083005 | Estimated Completion Date:2025-12-31",
                    name: "Three County Fiber",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Three County Fiber",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b08d68a5-e0bf-4169-8a75-866725b21fbe",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $3645085 | Estimated Completion Date:2021-04-01",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $3645085 | Estimated Completion Date:2021-04-01",
                    name: "Happy Camp to Somes Bar Fiber Connectivity",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Happy Camp to Somes Bar Fiber Connectivity",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6fdbb8de-40e7-4cf1-beca-394e539c8328",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24250 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $24250 | Estimated Completion Date:2019-06-30",
                    name: "Chestnut Creek Senior Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Chestnut Creek Senior Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bbc3cd21-31ad-4d1e-a749-9dda80e0ef03",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $34510 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $34510 | Estimated Completion Date:2019-06-30",
                    name: "Mandela Gateway Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mandela Gateway Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "546fa8b9-02c9-4f63-8c61-bc117d15355e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23881 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $23881 | Estimated Completion Date:2019-06-30",
                    name: "Terraza Palmera at St. Josephs",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Terraza Palmera at St. Josephs",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "76aa86f0-4f0d-4d2f-b17f-d886c2414242",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $49490 | Estimated Completion Date:2019-09-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $49490 | Estimated Completion Date:2019-09-30",
                    name: "Westlake Christian Terrace West",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Westlake Christian Terrace West",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d5457b92-eed5-41d5-9828-162869784291",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $49219 | Estimated Completion Date:2020-09-16",
                    map_popup:
                        " Housing |  | Funding Awarded: $49219 | Estimated Completion Date:2020-09-16",
                    name: "Cochrane Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cochrane Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6c5ce251-be21-4a47-abb5-b50e41e41c9d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $37239 | Estimated Completion Date:2020-05-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $37239 | Estimated Completion Date:2020-05-20",
                    name: "Palm Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Palm Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "004ec245-7469-4977-ad7e-bfa66db65c0a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23327 | Estimated Completion Date:2020-03-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $23327 | Estimated Completion Date:2020-03-31",
                    name: "Rodeo Gateway",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Rodeo Gateway",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0af7b605-47bf-4c57-8be7-0de6898a6ff4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17704 | Estimated Completion Date:2020-05-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $17704 | Estimated Completion Date:2020-05-20",
                    name: "Turina House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Turina House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ddac75ab-c549-4252-84ec-29396a217806",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33032 | Estimated Completion Date:2022-04-27",
                    map_popup:
                        " Housing |  | Funding Awarded: $33032 | Estimated Completion Date:2022-04-27",
                    name: "Hismen Hin-Nu Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hismen Hin-Nu Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0689f2c1-3330-4f85-9b53-b275e56e0a46",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21040 | Estimated Completion Date:2019-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $21040 | Estimated Completion Date:2019-01-31",
                    name: "Camphora",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Camphora",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "86d13759-ebbb-4ad1-bf76-9654548e0c7f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $11951 | Estimated Completion Date:2017-12-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $11951 | Estimated Completion Date:2017-12-15",
                    name: "Weinreb Place",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Weinreb Place",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d266ce32-cd80-4c40-9a16-22e77e7ad687",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29287 | Estimated Completion Date:2020-03-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $29287 | Estimated Completion Date:2020-03-30",
                    name: "Betty Ann Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Betty Ann Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7f4eae35-013b-4bfb-9a31-215d5ce75b9b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $20350 | Estimated Completion Date:2017-03-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $20350 | Estimated Completion Date:2017-03-10",
                    name: "El Paseo Digital Connections",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "El Paseo Digital Connections",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f347f90b-3446-48d3-a7e5-612704b2f27f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $19223 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $19223 | Estimated Completion Date:2018-01-31",
                    name: "Harbor Hills Housing Development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Harbor Hills Housing Development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "96919c43-89ab-4565-b837-f9627c4cfc4b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24564 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $24564 | Estimated Completion Date:2019-06-30",
                    name: "Glen Ellen Mutual Housing Community",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Glen Ellen Mutual Housing Community",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9e006c08-3b24-4eb8-a12e-132697e7164c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29246 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $29246 | Estimated Completion Date:2019-06-30",
                    name: "Mutual Housing at River Garden",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mutual Housing at River Garden",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b8fb5973-3a44-4652-9ed9-e1d5c9226891",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27524 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $27524 | Estimated Completion Date:2019-06-30",
                    name: "Mutual Housing on the Greenway",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mutual Housing on the Greenway",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8b18bb42-8e35-4fae-ad88-fcaac042462b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21217 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $21217 | Estimated Completion Date:2019-06-30",
                    name: "Victory Townhomes Mutual Housing Community",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Victory Townhomes Mutual Housing Community",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "31f5c7ac-628d-49c1-8385-78202d27cf1a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $6271 | Estimated Completion Date:2016-11-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $6271 | Estimated Completion Date:2016-11-10",
                    name: "579 Vallejo Street Senior Apartments Adoption",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "579 Vallejo Street Senior Apartments Adoption",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1017c8f3-6945-4864-a47d-21064f42ebb3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $47875 | Estimated Completion Date:2018-10-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $47875 | Estimated Completion Date:2018-10-30",
                    name: "Amistad House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Amistad House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c78b31e4-f4d5-4299-a9ec-aa44fa90c595",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $46360 | Estimated Completion Date:2019-05-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $46360 | Estimated Completion Date:2019-05-31",
                    name: "Lakeside Senior Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lakeside Senior Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "eb5cc0d4-0c99-4b1d-b238-284d8aeda722",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $48054 | Estimated Completion Date:2018-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $48054 | Estimated Completion Date:2018-08-30",
                    name: "Petaluma Avenue Homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Petaluma Avenue Homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cc308fb7-b9f2-43b6-9d2d-8d9f47626db2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16161 | Estimated Completion Date:2017-12-05",
                    map_popup:
                        " Housing |  | Funding Awarded: $16161 | Estimated Completion Date:2017-12-05",
                    name: "Parc Grove Northwest",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parc Grove Northwest",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0ce9efbc-d07c-4c8f-a4b6-5dd36f6988a3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $42928 | Estimated Completion Date:2019-07-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $42928 | Estimated Completion Date:2019-07-15",
                    name: "West Capitol Courtyards",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "West Capitol Courtyards",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c34066cb-c0b6-4bfb-9182-80a2d7ee48a4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $32400 | Estimated Completion Date:2018-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $32400 | Estimated Completion Date:2018-07-31",
                    name: "Guest House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Guest House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ef9a1c97-0e66-44c2-bd00-7c26e4e73c26",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17175 | Estimated Completion Date:2021-02-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $17175 | Estimated Completion Date:2021-02-28",
                    name: "Brierwood",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Brierwood",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "489e86cd-7918-493e-a20c-73a9090ace50",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $38710 | Estimated Completion Date:2016-09-16",
                    map_popup:
                        " Housing |  | Funding Awarded: $38710 | Estimated Completion Date:2016-09-16",
                    name: "Parklane Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parklane Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c8e2308c-4c35-491b-9a0c-b81d5171d237",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $39285 | Estimated Completion Date:2017-11-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $39285 | Estimated Completion Date:2017-11-20",
                    name: "990 Pacific",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "990 Pacific",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ee3404ba-bf93-483b-8d24-e68158e3484c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $40250 | Estimated Completion Date:2017-06-27",
                    map_popup:
                        " Housing |  | Funding Awarded: $40250 | Estimated Completion Date:2017-06-27",
                    name: "Mayberry Townhomes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mayberry Townhomes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3b2fb34f-0dc5-4265-82d4-6c54ebc70c60",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $74952 | Estimated Completion Date:2018-11-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $74952 | Estimated Completion Date:2018-11-02",
                    name: "Parks at Fig Garden",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parks at Fig Garden",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "72455f59-1927-46ab-a353-9e5d539e4520",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $13847 | Estimated Completion Date:2015-10-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $13847 | Estimated Completion Date:2015-10-01",
                    name: "Gwen Bolden Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gwen Bolden Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "28ec3bef-4f81-4f16-87d8-4d13da3a0a88",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $18650 | Estimated Completion Date:2016-02-03",
                    map_popup:
                        " Housing |  | Funding Awarded: $18650 | Estimated Completion Date:2016-02-03",
                    name: "Broadway Village II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Broadway Village II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "28f9ebf6-6ef6-4389-ab79-6c75136f9bc6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26638 | Estimated Completion Date:2017-12-07",
                    map_popup:
                        " Housing |  | Funding Awarded: $26638 | Estimated Completion Date:2017-12-07",
                    name: "Centertown",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Centertown",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ab8e7c97-5f29-4744-a835-2a6b0f8d99b3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $66860 | Estimated Completion Date:2017-05-11",
                    map_popup:
                        " Housing |  | Funding Awarded: $66860 | Estimated Completion Date:2017-05-11",
                    name: "Elena Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Elena Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3f73b6b4-0eff-4a08-9e6b-3684368c65f5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $42000 | Estimated Completion Date:2019-06-24",
                    map_popup:
                        " Housing |  | Funding Awarded: $42000 | Estimated Completion Date:2019-06-24",
                    name: "Los Robles",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Los Robles",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "eebd0c78-d2aa-4daa-8d7c-b5df21c6ddec",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12333 | Estimated Completion Date:2016-03-08",
                    map_popup:
                        " Housing |  | Funding Awarded: $12333 | Estimated Completion Date:2016-03-08",
                    name: "Riviera",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Riviera",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "920b6514-4c65-4839-a0bc-0353eb6d019c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $11833 | Estimated Completion Date:2016-03-09",
                    map_popup:
                        " Housing |  | Funding Awarded: $11833 | Estimated Completion Date:2016-03-09",
                    name: "Turina House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Turina House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d0cb5e8d-4b43-4df8-bbfc-1bdf449e5816",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30735 | Estimated Completion Date:2017-06-23",
                    map_popup:
                        " Housing |  | Funding Awarded: $30735 | Estimated Completion Date:2017-06-23",
                    name: "Giant Road",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Giant Road",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "97b5ae8e-e96b-44db-a847-1c49f90c8a53",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $42605 | Estimated Completion Date:2017-08-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $42605 | Estimated Completion Date:2017-08-02",
                    name: "Madison Park",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Madison Park",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "24bf1f09-8057-458f-9d56-ad5e04c7eac6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $42980 | Estimated Completion Date:2017-03-23",
                    map_popup:
                        " Housing |  | Funding Awarded: $42980 | Estimated Completion Date:2017-03-23",
                    name: "San Pablo Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Pablo Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3cbcdf15-7185-47f0-a196-e486da7ff406",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28029 | Estimated Completion Date:2019-01-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $28029 | Estimated Completion Date:2019-01-10",
                    name: "Jasmine Square",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Jasmine Square",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1ba2e098-8dc2-4c65-97dd-ba0184dacd37",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $34625 | Estimated Completion Date:2017-09-14",
                    map_popup:
                        " Housing |  | Funding Awarded: $34625 | Estimated Completion Date:2017-09-14",
                    name: "Tienda Drive Senior",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tienda Drive Senior",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a7304c35-f632-40cd-90c5-483c803d574a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26198 | Estimated Completion Date:2016-06-17",
                    map_popup:
                        " Housing |  | Funding Awarded: $26198 | Estimated Completion Date:2016-06-17",
                    name: "Camphora Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Camphora Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a473b896-b87b-45f9-9188-dbeb6cbd3a5d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25425 | Estimated Completion Date:2015-12-03",
                    map_popup:
                        " Housing |  | Funding Awarded: $25425 | Estimated Completion Date:2015-12-03",
                    name: "Craig Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Craig Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e127a69e-72a2-4710-9008-7377036d92d0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $63340 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $63340 | Estimated Completion Date:",
                    name: "Los Esteros",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Los Esteros",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "66ad6b38-73c6-48d4-94e4-667961edac59",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $40350 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $40350 | Estimated Completion Date:",
                    name: "Second Street Studios",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Second Street Studios",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ef1ef24b-21b8-4270-a7b6-08a5e23697d2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25960 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $25960 | Estimated Completion Date:",
                    name: "Clinton Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Clinton Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "46a97021-0732-44c9-ae0d-70b47fd4435e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24200 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $24200 | Estimated Completion Date:",
                    name: "Mirage Vista",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mirage Vista",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8c3577ae-3d52-45b0-b326-720734b274d1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21893 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $21893 | Estimated Completion Date:",
                    name: "Edgewater Isle",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Edgewater Isle",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0f4679e8-65d6-4d2b-8006-e224424b5b1e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22457 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $22457 | Estimated Completion Date:",
                    name: "Dayton Square",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Dayton Square",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c3607e97-9e37-46cf-8f3d-02e5df878700",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $59970 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $59970 | Estimated Completion Date:",
                    name: "Union Towers",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Union Towers",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b2e2cded-ef9c-4592-ab70-9fea265269ff",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30000 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $30000 | Estimated Completion Date:",
                    name: "Arvin Sun Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Arvin Sun Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "65310b85-ec33-4199-ba93-b4196d4189ee",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15808 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $15808 | Estimated Completion Date:",
                    name: "Monterey St",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Monterey St",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7e50a5bb-95c1-45e2-b2dd-9e1d9a6615d0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $35100 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $35100 | Estimated Completion Date:",
                    name: "Plaza Towers",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Plaza Towers",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f0a72bc5-02b7-4827-9721-e54b9e6ed07d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $51000 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $51000 | Estimated Completion Date:",
                    name: "Village Congressional",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Village Congressional",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f309a8d6-62f2-47b8-b10c-2e7b1f6b513e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22128 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $22128 | Estimated Completion Date:",
                    name: "Miller Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Miller Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0d96dd45-8ed6-4a70-a097-60159bf707a3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $40121 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $40121 | Estimated Completion Date:",
                    name: "Mary Elizabeth Inn",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mary Elizabeth Inn",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "37fa47cb-64ad-4889-8e2a-485a063d7a76",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33550 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $33550 | Estimated Completion Date:",
                    name: "Land Park Woods",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Land Park Woods",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f2fc3ef4-4605-4f3d-965f-b831b06fa19a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23509 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $23509 | Estimated Completion Date:",
                    name: "St. Stephens Senior Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "St. Stephens Senior Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f334c524-17aa-40f6-ab93-5b6b2da2aad9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24193 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $24193 | Estimated Completion Date:",
                    name: "University Avenue Senior",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "University Avenue Senior",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ea654a7c-48b1-4078-abee-8760fe3d9ae3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $34293 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $34293 | Estimated Completion Date:",
                    name: "Los Robles",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Los Robles",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5e0d9ba3-ab2a-4063-961d-7515fc709b4f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $41565 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $41565 | Estimated Completion Date:",
                    name: "Mayacamas Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mayacamas Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1b1fde37-ccb2-4b54-b9f1-9eea1848b23d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $66810 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $66810 | Estimated Completion Date:",
                    name: "Silverado Creek Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Silverado Creek Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "960bf0ac-5bab-4768-9e43-27e5a6b6b97d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25545 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $25545 | Estimated Completion Date:",
                    name: "Broad Street Place",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Broad Street Place",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9a7d51d5-4026-4551-9dfd-c1e1c4be9f12",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $7200 | Estimated Completion Date:2019-11-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $7200 | Estimated Completion Date:2019-11-26",
                    name: "Casas Las Granadas",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Casas Las Granadas",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3f8f3be2-2771-4e97-890a-4195dd75c16d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17400 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $17400 | Estimated Completion Date:2017-08-30",
                    name: "Creekside Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Creekside Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "265d996e-efac-4667-8fb0-a243fddfbd7e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25200 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $25200 | Estimated Completion Date:2017-08-30",
                    name: "El Patio Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "El Patio Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1fd8de77-3391-4972-b5ca-42f6e20796c1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $8400 | Estimated Completion Date:2019-04-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $8400 | Estimated Completion Date:2019-04-30",
                    name: "Juniper Street Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Juniper Street Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "34c14dc6-ed82-41c5-8a04-8cf7695ea968",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23400 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $23400 | Estimated Completion Date:2017-08-30",
                    name: "Los Adobes de Maria II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Los Adobes de Maria II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "69dbadb8-1b81-4933-89d3-0e089efc71a5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24000 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $24000 | Estimated Completion Date:2017-08-30",
                    name: "Ocean View Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ocean View Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "15ea1e8a-6c15-4b59-93f0-974cd88561b4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $45160 | Estimated Completion Date:2024-01-19",
                    map_popup:
                        " Housing |  | Funding Awarded: $45160 | Estimated Completion Date:2024-01-19",
                    name: "Pismo Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pismo Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9313d1ae-cdbc-475c-89cd-4191da75a9f8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $14400 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $14400 | Estimated Completion Date:2017-08-30",
                    name: "Schoolhouse Lane Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Schoolhouse Lane Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9866d4c3-0687-42be-88ff-6cecbcdac64b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33750 | Estimated Completion Date:2019-07-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $33750 | Estimated Completion Date:2019-07-26",
                    name: "South Bay Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "South Bay Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ca358a2a-e8a4-40d3-8fea-93b863b8d62a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16800 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $16800 | Estimated Completion Date:2017-08-30",
                    name: "Victoria Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Victoria Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fe7bd20d-19dd-4d1a-a026-3e48d38390d0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26348 | Estimated Completion Date:2024-04-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $26348 | Estimated Completion Date:2024-04-15",
                    name: "Acacia Ln Senior Apartments Residential Broadband",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Acacia Ln Senior Apartments Residential Broadband",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4aea4772-2b10-47ac-8280-a430ba7d6d80",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $9617 | Estimated Completion Date:2016-02-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $9617 | Estimated Completion Date:2016-02-02",
                    name: "Mountain View",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mountain View",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5e0df4c2-d534-4d76-8fda-2667300366d4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $20803 | Estimated Completion Date:2017-09-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $20803 | Estimated Completion Date:2017-09-15",
                    name: "Sun House Senior",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sun House Senior",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e5aba6ba-29b2-4869-a068-2774fbf216c5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $7161 | Estimated Completion Date:2015-06-25",
                    map_popup:
                        " Housing |  | Funding Awarded: $7161 | Estimated Completion Date:2015-06-25",
                    name: "1275 Lindberg",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "1275 Lindberg",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f36558c1-7304-4900-b03d-afe44770d7ff",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $65077 | Estimated Completion Date:2024-02-16",
                    map_popup:
                        " Housing |  | Funding Awarded: $65077 | Estimated Completion Date:2024-02-16",
                    name: "Coliseum Place",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Coliseum Place",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "35e6711f-c01b-4551-a219-7cf6170f8f11",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17166 | Estimated Completion Date:2017-11-16",
                    map_popup:
                        " Housing |  | Funding Awarded: $17166 | Estimated Completion Date:2017-11-16",
                    name: "Bayview Commons",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bayview Commons",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c8cc0d2c-b2ff-44d2-90a0-3f542dd7a636",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21225 | Estimated Completion Date:2017-03-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $21225 | Estimated Completion Date:2017-03-30",
                    name: "Columbia Park Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Columbia Park Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5d1ad4fa-8ecc-4241-9bf1-fd3a9e5d1fa0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15847 | Estimated Completion Date:2017-04-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $15847 | Estimated Completion Date:2017-04-26",
                    name: "Otterbein Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Otterbein Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "073353a7-2f16-46a2-82e9-ba92423ae90c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17994 | Estimated Completion Date:2016-12-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $17994 | Estimated Completion Date:2016-12-02",
                    name: "Petaluma Avenue Homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Petaluma Avenue Homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fe070fc7-eedf-4842-ad48-5cf1d4cb467a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21600 | Estimated Completion Date:2016-04-19",
                    map_popup:
                        " Housing |  | Funding Awarded: $21600 | Estimated Completion Date:2016-04-19",
                    name: "ALMOND COURT PARTNERS",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ALMOND COURT PARTNERS",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1b46e838-ea1e-4dcc-8531-c14f6480a17d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $57240 | Estimated Completion Date:2024-08-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $57240 | Estimated Completion Date:2024-08-26",
                    name: "Dinuba Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Dinuba Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "066c8038-38fc-436d-8aa6-aadcba9f2b96",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24000 | Estimated Completion Date:2016-04-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $24000 | Estimated Completion Date:2016-04-26",
                    name: "Lincoln Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lincoln Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "190f11ca-b9e5-4241-a71a-27db05dae5e4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $35100 | Estimated Completion Date:2017-04-13",
                    map_popup:
                        " Housing |  | Funding Awarded: $35100 | Estimated Completion Date:2017-04-13",
                    name: "SOLINAS VILLAGE aka SELF HELP COMMUNITIES 1, LLC",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "SOLINAS VILLAGE aka SELF HELP COMMUNITIES 1, LLC",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c9705c41-e8b5-4c17-af42-fafc351f817e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:2018-05-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:2018-05-02",
                    name: "Villa de Guadalupe",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Villa de Guadalupe",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "31344bbf-a8a8-48f2-8f60-cb1a22f47164",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26400 | Estimated Completion Date:2016-04-21",
                    map_popup:
                        " Housing |  | Funding Awarded: $26400 | Estimated Completion Date:2016-04-21",
                    name: "WASHINGTON PLAZA PARTNERS",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "WASHINGTON PLAZA PARTNERS",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "93549e77-363d-4ba0-8c65-399dafaa6595",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $59900 | Estimated Completion Date:2016-04-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $59900 | Estimated Completion Date:2016-04-01",
                    name: "Parc Grove Commons",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parc Grove Commons",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0f92f551-cfb2-47c2-bf5e-80829715be8e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10044 | Estimated Completion Date:2020-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $10044 | Estimated Completion Date:2020-07-31",
                    name: "Star Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Star Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1d1c1017-605a-4c5f-8c05-4954e607234d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $37800 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $37800 | Estimated Completion Date:2018-01-31",
                    name: "Palm Grove",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Palm Grove",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c232bb8c-3dfd-4fc0-b7a6-c9cf474caabd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $39000 | Estimated Completion Date:2019-11-19",
                    map_popup:
                        " Housing |  | Funding Awarded: $39000 | Estimated Completion Date:2019-11-19",
                    name: "Positano Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Positano Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b0b2f63a-630e-40ea-9403-3477076a67da",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30600 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $30600 | Estimated Completion Date:2018-01-31",
                    name: "Sandpiper Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sandpiper Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0ca364a2-7541-40d8-9475-97dc58c8e103",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $14400 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $14400 | Estimated Completion Date:2018-01-31",
                    name: "Ted Zenich Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ted Zenich Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d3d0a774-6bb4-4310-aa5c-6df727740092",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $8909 | Estimated Completion Date:2015-10-29",
                    map_popup:
                        " Housing |  | Funding Awarded: $8909 | Estimated Completion Date:2015-10-29",
                    name: "The Fairfax Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Fairfax Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "daa34ef4-be12-4e17-abd0-969f8aac0b50",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21462 | Estimated Completion Date:2017-12-08",
                    map_popup:
                        " Housing |  | Funding Awarded: $21462 | Estimated Completion Date:2017-12-08",
                    name: "939 Eddy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "939 Eddy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "917df364-331a-476e-8cc3-bf6760767f59",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24865 | Estimated Completion Date:2017-06-06",
                    map_popup:
                        " Housing |  | Funding Awarded: $24865 | Estimated Completion Date:2017-06-06",
                    name: "Curran House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Curran House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7adf312e-6bd5-4a3d-86ef-269103495ad4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $43976 | Estimated Completion Date:2017-09-27",
                    map_popup:
                        " Housing |  | Funding Awarded: $43976 | Estimated Completion Date:2017-09-27",
                    name: "Folsom + Dore Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Folsom + Dore Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7ec0d51c-d6cf-4801-bd56-c39293911a87",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $41170 | Estimated Completion Date:2017-09-22",
                    map_popup:
                        " Housing |  | Funding Awarded: $41170 | Estimated Completion Date:2017-09-22",
                    name: "Mosaica (Family)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mosaica (Family)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ef363425-2e5f-4435-ad4e-81eeedd99585",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $31683 | Estimated Completion Date:2017-12-08",
                    map_popup:
                        " Housing |  | Funding Awarded: $31683 | Estimated Completion Date:2017-12-08",
                    name: "West Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "West Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "60d0ae3f-fb3e-4d90-925d-b9cd254c41e5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27600 | Estimated Completion Date:2018-11-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $27600 | Estimated Completion Date:2018-11-28",
                    name: "Almond Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Almond Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a215cfef-a57e-44a1-b0ed-b1476bf87dd0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21825 | Estimated Completion Date:2018-11-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $21825 | Estimated Completion Date:2018-11-28",
                    name: "Mountain View Townhomes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mountain View Townhomes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "99afddf8-b6c0-48a4-a191-b17234cb2e25",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15750 | Estimated Completion Date:2016-01-12",
                    map_popup:
                        " Housing |  | Funding Awarded: $15750 | Estimated Completion Date:2016-01-12",
                    name: "Patio Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Patio Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ce967ad4-98a0-4b14-949c-d88a6734230a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $90000 | Estimated Completion Date:2022-11-23",
                    map_popup:
                        "  |  | Funding Awarded: $90000 | Estimated Completion Date:2022-11-23",
                    name: "21/22 Klamath River Rural Broadband Initiative (KRRBI) Broadband Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "21/22 Klamath River Rural Broadband Initiative (KRRBI) Broadband Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c3ae31c5-99d9-48ad-80fa-e1cfdb902106",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50000 | Estimated Completion Date:2021-11-30",
                    map_popup:
                        "  |  | Funding Awarded: $50000 | Estimated Completion Date:2021-11-30",
                    name: "Feasibility to buy out Frontier Assets in Del Norte",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Feasibility to buy out Frontier Assets in Del Norte",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5d85a991-59cf-4ad3-a0a3-1004800b01f2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $64852 | Estimated Completion Date:2026-05-20",
                    map_popup:
                        "  |  | Funding Awarded: $64852 | Estimated Completion Date:2026-05-20",
                    name: "CEP Digital Literacy, San Luis Obispo County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "CEP Digital Literacy, San Luis Obispo County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "580df7a9-fcf2-47fa-b841-09445fd93e41",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $137308 | Estimated Completion Date:2026-05-20",
                    map_popup:
                        "  |  | Funding Awarded: $137308 | Estimated Completion Date:2026-05-20",
                    name: "CEP Digital Literacy, Ventura County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "CEP Digital Literacy, Ventura County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6a53e0f7-6a96-4699-8f50-5c56a6b33c49",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $40000 | Estimated Completion Date:2023-01-12",
                    map_popup:
                        "  |  | Funding Awarded: $40000 | Estimated Completion Date:2023-01-12",
                    name: "Project 3: Resighini Rancheria Broadband Regulatory and Carrier Outreach Support",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 3: Resighini Rancheria Broadband Regulatory and Carrier Outreach Support",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "924c6628-4268-40a7-a8d3-28510d8f5bcb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $97000 | Estimated Completion Date:2021-10-26",
                    map_popup:
                        "  |  | Funding Awarded: $97000 | Estimated Completion Date:2021-10-26",
                    name: "Working With Communities For Sustainable Broadband",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Working With Communities For Sustainable Broadband",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "971c3c06-7409-43a3-8948-b82537dcd87f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2021-12-04",
                    map_popup:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2021-12-04",
                    name: "Project 1: Technical Feasibility Study for Broadband Deployment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 1: Technical Feasibility Study for Broadband Deployment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b47fc48d-90c2-4f0b-89f2-219602bedae5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2023-03-10",
                    map_popup:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2023-03-10",
                    name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8bd55d8d-999d-4b5f-9d36-3918899ef265",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $149500 | Estimated Completion Date:2022-07-01",
                    map_popup:
                        "  |  | Funding Awarded: $149500 | Estimated Completion Date:2022-07-01",
                    name: "Affordable Housing and Broadband Infrastructure",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Affordable Housing and Broadband Infrastructure",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c7e93e1a-5672-468b-a130-5c409ff34c73",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $98700 | Estimated Completion Date:2022-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $98700 | Estimated Completion Date:2022-07-31",
                    name: "Sustainable Broadband Services",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sustainable Broadband Services",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5afe52d8-1113-4a43-8b3d-7918371cf499",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $109000 | Estimated Completion Date:2022-09-01",
                    map_popup:
                        "  |  | Funding Awarded: $109000 | Estimated Completion Date:2022-09-01",
                    name: "Round Valley CASF  Technical Assistance I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Round Valley CASF  Technical Assistance I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "01cf4518-1d19-4112-abab-cb02395ead36",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2023-02-28",
                    map_popup:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2023-02-28",
                    name: "Technical Feasibility Study for Broadband Deployment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Technical Feasibility Study for Broadband Deployment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "40d9a07e-85c3-4178-ad7b-d37fce046f79",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $110000 | Estimated Completion Date:2023-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $110000 | Estimated Completion Date:2023-09-30",
                    name: "Round Valley CASF Technical Assistance III",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Round Valley CASF Technical Assistance III",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "24c31e23-4f2d-4c3a-8437-e42ce715be7b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2024-01-01",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2024-01-01",
                    name: "Tribal Technical Assistance (TTA) - Tower Feasibility Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tribal Technical Assistance (TTA) - Tower Feasibility Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "089f19ee-22b5-4a8e-8fe7-d13dba8b6316",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $119900 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $119900 | Estimated Completion Date:",
                    name: "Quechan Indian Tribe Feasibility Study for Broadband Deployment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Quechan Indian Tribe Feasibility Study for Broadband Deployment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a670cd7c-fe1b-427a-8522-dbf50636e875",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    name: "Pauma Band of Luise\u00f1o Indians Tribal Technical Assistance",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pauma Band of Luise\u00f1o Indians Tribal Technical Assistance",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "71b0e2ff-919e-4357-9c52-e9abb85fded5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    name: "RVIT Data Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "RVIT Data Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3dd8d3d2-22d1-4915-8ccb-e79411403a68",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    name: "Broadband Feasibility Study and Partnership Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Broadband Feasibility Study and Partnership Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ad348399-4bf7-4bd4-bfc4-781a4e334291",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $139400 | Estimated Completion Date:2026-05-20",
                    map_popup:
                        "  |  | Funding Awarded: $139400 | Estimated Completion Date:2026-05-20",
                    name: "Connect, Communicate, Color Your World! - CEP Schools, Santa Barbara County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connect, Communicate, Color Your World! - CEP Schools, Santa Barbara County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e73ed0b4-3b6c-46c9-b8c8-b7782fcbb7af",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $26735 | Estimated Completion Date:2025-10-25",
                    map_popup:
                        "  |  | Funding Awarded: $26735 | Estimated Completion Date:2025-10-25",
                    name: "Anza Electric Cooperative, Inc. Public Broadband Education Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Anza Electric Cooperative, Inc. Public Broadband Education Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b5c85ca8-89e6-4a13-929b-337295e0bd37",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $59690 | Estimated Completion Date:2023-07-01",
                    map_popup:
                        "  |  | Funding Awarded: $59690 | Estimated Completion Date:2023-07-01",
                    name: "Digital Health Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Health Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "15a30717-b89c-4eb9-9d41-3d80ab3388bb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $77900 | Estimated Completion Date:2026-06-03",
                    map_popup:
                        "  |  | Funding Awarded: $77900 | Estimated Completion Date:2026-06-03",
                    name: "Digital Health Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Health Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e1e53414-1214-4407-852d-68faba1557c1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $38718 | Estimated Completion Date:2023-11-30",
                    map_popup:
                        "  |  | Funding Awarded: $38718 | Estimated Completion Date:2023-11-30",
                    name: "Computer Lab Reinvestment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Computer Lab Reinvestment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0417d304-c7e9-4f7a-8770-9be7e723ba8c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-20",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-20",
                    name: "Call Center San Luis Obispo County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Call Center San Luis Obispo County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "10baa16b-f451-4e99-95ad-3198646fb486",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-20",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-20",
                    name: "Call Center Santa Barbara County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Call Center Santa Barbara County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "412f6c6e-4c9c-4dbf-894d-7160f270e897",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-20",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-20",
                    name: "Call Center Ventura County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Call Center Ventura County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "53821b7c-7979-4a2b-9571-fd14c78bb7aa",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $43742 | Estimated Completion Date:2026-04-05",
                    map_popup:
                        "  |  | Funding Awarded: $43742 | Estimated Completion Date:2026-04-05",
                    name: "Bridging The Digital Divide For Los Angeles Affordable Housing Residents - Gonzaque Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bridging The Digital Divide For Los Angeles Affordable Housing Residents - Gonzaque Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "467f443d-312a-4236-8a58-c4408589e37d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $88922 | Estimated Completion Date:2026-04-05",
                    map_popup:
                        "  |  | Funding Awarded: $88922 | Estimated Completion Date:2026-04-05",
                    name: "Bridging The Digital Divide For Los Angeles Affordable Housing Residents - Imperial Courts",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bridging The Digital Divide For Los Angeles Affordable Housing Residents - Imperial Courts",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bd07e3d8-e08a-4b9b-aec6-6faa2b7e6137",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $93672 | Estimated Completion Date:2026-04-05",
                    map_popup:
                        "  |  | Funding Awarded: $93672 | Estimated Completion Date:2026-04-05",
                    name: "Bridging The Digital Divide For Los Angeles Affordable Housing Residents - Jordon Downs",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bridging The Digital Divide For Los Angeles Affordable Housing Residents - Jordon Downs",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "731d5fc9-7426-4036-9a33-ad7e2bdc2a71",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $103192 | Estimated Completion Date:2026-04-05",
                    map_popup:
                        "  |  | Funding Awarded: $103192 | Estimated Completion Date:2026-04-05",
                    name: "Bridging The Digital Divide For Los Angeles Affordable Housing Residents Nickerson",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bridging The Digital Divide For Los Angeles Affordable Housing Residents Nickerson",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1bda514a-83d3-436c-a42f-b11948f610be",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $14867 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $14867 | Estimated Completion Date:2023-12-03",
                    name: "Senior Connection Initiative - Bell Manor Sr. Apartments.",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Senior Connection Initiative - Bell Manor Sr. Apartments.",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8548774e-29db-41c7-8644-d0b3ef6e6ce6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $3664 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $3664 | Estimated Completion Date:2023-12-03",
                    name: "Senior Connection Initiative - Cabernet Sr. Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Senior Connection Initiative - Cabernet Sr. Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "95da0652-fa6b-4a96-b6c6-36db4c73b1d6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $9155 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $9155 | Estimated Completion Date:2023-12-03",
                    name: "Senior Connection Initiative - Charles Street Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Senior Connection Initiative - Charles Street Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a5901d5f-af80-4fb0-bfac-28d5b8bccb57",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $12266 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $12266 | Estimated Completion Date:2023-12-03",
                    name: "Senior Connection Initiative - Fitch Mt. Sr. Apartments.",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Senior Connection Initiative - Fitch Mt. Sr. Apartments.",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ca892c44-3059-480a-b7dd-8806c0b0e4d3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $5041 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $5041 | Estimated Completion Date:2023-12-03",
                    name: "Senior Connection Initiative - Park Land Sr. Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Senior Connection Initiative - Park Land Sr. Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e70e7a16-8ede-4058-b99b-bca90a542fd1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $6415 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $6415 | Estimated Completion Date:2023-12-03",
                    name: "Senior Connection Initiative - Sonoma Creek Sr. Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Senior Connection Initiative - Sonoma Creek Sr. Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6347d67b-c520-499c-ac74-3fafe08e0f60",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $6904 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $6904 | Estimated Completion Date:2023-12-03",
                    name: "Senior Connection Initiative - Village Green Sr. Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Senior Connection Initiative - Village Green Sr. Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bfbea1b7-b5c0-4084-8aaf-a6d9471490f2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $10965 | Estimated Completion Date:2023-12-01",
                    map_popup:
                        "  |  | Funding Awarded: $10965 | Estimated Completion Date:2023-12-01",
                    name: "Senior Connection Initiative - Vinecrest Sr. Apartments.",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Senior Connection Initiative - Vinecrest Sr. Apartments.",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2f808d53-a4ab-403d-8219-5fc405eb31cd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $135264 | Estimated Completion Date:2026-06-15",
                    map_popup:
                        "  |  | Funding Awarded: $135264 | Estimated Completion Date:2026-06-15",
                    name: "Get Connected! DigitalLearn - Pacific Coast",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Get Connected! DigitalLearn - Pacific Coast",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "234098e7-18a5-4c59-8cdb-54e6aac5cbe0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $487500 | Estimated Completion Date:2026-06-15",
                    map_popup:
                        "  |  | Funding Awarded: $487500 | Estimated Completion Date:2026-06-15",
                    name: "Get Connected! DigitalLearn - Riverside County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Get Connected! DigitalLearn - Riverside County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d592e13f-658c-4313-8d41-2b4450ecec03",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $1230000 | Estimated Completion Date:2026-06-15",
                    map_popup:
                        "  |  | Funding Awarded: $1230000 | Estimated Completion Date:2026-06-15",
                    name: "Get Connected! DigitalLearn - South Bay and Gateway Cities of Los Angeles County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Get Connected! DigitalLearn - South Bay and Gateway Cities of Los Angeles County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bbb53433-5e14-4281-8d1b-eb6b78e7fe09",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $487500 | Estimated Completion Date:2022-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $487500 | Estimated Completion Date:2022-03-31",
                    name: "Fresno State Call Center: Central California Region",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Call Center: Central California Region",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "67c5e116-9789-4af5-86b5-dceb2e7b2cd8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    name: "Fresno State Parent University - Del Norte County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - Del Norte County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f58d0d8f-9159-4d90-aba9-1f9401255c71",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2022-06-30",
                    name: "Fresno State Parent University - FRESNO COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - FRESNO COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ecd292ce-c398-4a85-81af-0949e90d8022",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - FRESNO COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - FRESNO COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c4a4bd63-ef0d-46e3-b574-bbc55235fed0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    name: "Fresno State Parent University - Humboldt County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - Humboldt County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2c64672d-5f76-46f0-954f-17464bef0c78",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    name: "Fresno State Parent University - Imperial County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - Imperial County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "58f20ff0-0344-42d5-838a-e4fe8a3ec49b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2022-06-30",
                    name: "Fresno State Parent University - KERN COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - KERN COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c7aee7b8-1a66-4836-9f48-1e9c74253d64",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - KERN COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - KERN COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7dc72cbd-c26e-4403-bb65-9db0afdcfd53",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2022-06-30",
                    name: "Fresno State Parent University - KINGS COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - KINGS COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "305bcde5-c62f-453d-a6e4-1c1a60dd7242",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    name: "Fresno State Parent University - Lake County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - Lake County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3711462a-c30a-41d9-be82-05c0affadfc0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2023-06-30",
                    name: "Fresno State Parent University - MADERA COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - MADERA COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c3541219-9dc8-4953-a6c4-2e6151ef08eb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - MADERA COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - MADERA COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dcf2b328-9a7e-450d-823d-4dcccb393352",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2023-06-30",
                    name: "Fresno State Parent University - MERCED COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - MERCED COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "041f47f6-8f44-4ec9-bbc1-2df139d23d40",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - MERCED COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - MERCED COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "521fab3a-0d0d-46d4-8819-49979367e912",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - MONTEREY COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - MONTEREY COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "de68a66c-c263-46a7-978c-7a75682d4a07",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - SAN BENITO COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - SAN BENITO COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1ab47eb7-fe8c-4f92-b451-4ddbac90448d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - SAN JOAQUIN COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - SAN JOAQUIN COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d0e70652-d37d-4d91-bd13-d58bdac22ffb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54580 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54580 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - SAN LUIS OBISPO COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - SAN LUIS OBISPO COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4c1b6d57-ff9a-4a75-8352-9c289e5495ca",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    name: "Fresno State Parent University - Siskiyou County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - Siskiyou County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bd32cb32-00e6-4c9d-bbcc-b32a4075fae2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2023-06-30",
                    name: "Fresno State Parent University - STANISLAUS COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - STANISLAUS COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ed170c36-6961-4013-9ab7-d8c0f5ed6aa0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    name: "Fresno State Parent University - Tehama County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - Tehama County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8ac3952f-625b-4ae4-9b00-a38fedeed6fe",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $143100 | Estimated Completion Date:2025-12-31",
                    name: "Fresno State Parent University - Trinity County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - Trinity County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4e6abeb4-69f0-4f69-b82e-5b67645eeda8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $71516 | Estimated Completion Date:2022-06-30",
                    name: "Fresno State Parent University - TULARE COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - TULARE COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "72d9ea2c-1cb1-4565-933a-7eb064df61da",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $54480 | Estimated Completion Date:2023-12-05",
                    name: "Fresno State Parent University - TULARE COUNTY",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno State Parent University - TULARE COUNTY",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ff5dd7fc-dfb4-41c2-ab5f-e005f52e10aa",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $147169 | Estimated Completion Date:2025-03-27",
                    map_popup:
                        "  |  | Funding Awarded: $147169 | Estimated Completion Date:2025-03-27",
                    name: "Canal Alliance Adult Education English as a Second Language Digital Literacy Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Canal Alliance Adult Education English as a Second Language Digital Literacy Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d3ae9cd0-01b9-4997-a3f7-c566bb20b552",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $83248 | Estimated Completion Date:2022-04-29",
                    map_popup:
                        "  |  | Funding Awarded: $83248 | Estimated Completion Date:2022-04-29",
                    name: "Digital Education Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Education Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "35f50ae0-d0ce-482e-9d21-7921ccbe3d7c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $125997 | Estimated Completion Date:2025-11-01",
                    map_popup:
                        "  |  | Funding Awarded: $125997 | Estimated Completion Date:2025-11-01",
                    name: "FMCI&Oth BA",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "FMCI&Oth BA",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cf4673b1-8507-4e38-baed-8503ccf61a4f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $138584 | Estimated Completion Date:2025-11-01",
                    map_popup:
                        "  |  | Funding Awarded: $138584 | Estimated Completion Date:2025-11-01",
                    name: "WUYC Annx ESC BA",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "WUYC Annx ESC BA",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2a423476-a421-4984-ba10-12c1bc344d22",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2025-11-01",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2025-11-01",
                    name: "WUYC Annx ESC DL",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "WUYC Annx ESC DL",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2968b2aa-5e9a-40be-b4fc-dc1b53350db5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $35817 | Estimated Completion Date:2024-07-12",
                    map_popup:
                        "  |  | Funding Awarded: $35817 | Estimated Completion Date:2024-07-12",
                    name: "Digital Equity for Seniors-Berkeley",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Equity for Seniors-Berkeley",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "827a5e6c-767f-4035-ad1f-efe2f0143fc3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $26964 | Estimated Completion Date:2024-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $26964 | Estimated Completion Date:2024-12-31",
                    name: "Digital Equity for Seniors-Guardian",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Equity for Seniors-Guardian",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "598a0f0f-fef2-4dc2-97cb-b9721e53a80e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $28326 | Estimated Completion Date:2024-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $28326 | Estimated Completion Date:2024-12-31",
                    name: "Digital Equity for Seniors-Josie Barrow",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Equity for Seniors-Josie Barrow",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d8e52a42-6501-4676-a31f-4ba8c2114d8f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $31731 | Estimated Completion Date:2024-07-12",
                    map_popup:
                        "  |  | Funding Awarded: $31731 | Estimated Completion Date:2024-07-12",
                    name: "Digital Equity for Seniors-San Leandro",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Equity for Seniors-San Leandro",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5b17167e-2582-4c33-9b61-c2f24cbd71a6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $35137 | Estimated Completion Date:2024-07-12",
                    map_popup:
                        "  |  | Funding Awarded: $35137 | Estimated Completion Date:2024-07-12",
                    name: "Digital Equity for Seniors-San Pablo",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Equity for Seniors-San Pablo",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2bad1dc1-aa88-49f9-81dc-c5f1688960db",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $247264 | Estimated Completion Date:2026-06-10",
                    map_popup:
                        "  |  | Funding Awarded: $247264 | Estimated Completion Date:2026-06-10",
                    name: "Digital Literacy for Workforce Development: English Langugage Learners",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Literacy for Workforce Development: English Langugage Learners",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4b279008-cfd8-4eb8-98dc-f669b2864342",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $490393 | Estimated Completion Date:2026-06-10",
                    map_popup:
                        "  |  | Funding Awarded: $490393 | Estimated Completion Date:2026-06-10",
                    name: "Northeastern and Upstate Call Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Northeastern and Upstate Call Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5363c90b-dc97-4a5a-aad8-4f76300cd8d9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $16034 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $16034 | Estimated Completion Date:2023-12-31",
                    name: "Beth Eden Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Beth Eden Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1c7355d9-2fde-451c-a246-e128d97b346e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $26086 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $26086 | Estimated Completion Date:2023-12-31",
                    name: "Garfield Park Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Garfield Park Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b280e303-4c89-4df1-8627-412ff8103db3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $25971 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $25971 | Estimated Completion Date:2023-12-31",
                    name: "Percy Abrams & Sister Thea Bowman Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Percy Abrams & Sister Thea Bowman Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "87fd0d10-2998-43d3-9b0f-300e44801d8e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $32100 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $32100 | Estimated Completion Date:2023-12-31",
                    name: "Plaza De Las Flores",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Plaza De Las Flores",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0f883fdb-1873-431a-a003-8714c1225dbc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $17297 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $17297 | Estimated Completion Date:2023-12-31",
                    name: "Providence Senior Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Providence Senior Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e20de912-f7f9-4e52-b008-0d774e7dc4f5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $4650 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $4650 | Estimated Completion Date:2023-12-31",
                    name: "Roy C Nichols Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Roy C Nichols Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1fe79653-832c-4a7f-a747-7b15361d6f9d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $34824 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $34824 | Estimated Completion Date:2023-12-31",
                    name: "Southlake",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Southlake",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b6bc7464-05df-481a-a4f2-4a2416a05d2e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $9563 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $9563 | Estimated Completion Date:2022-06-30",
                    name: "Cerritos Library Broadband Access Improvement",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cerritos Library Broadband Access Improvement",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "35b59ff0-014f-4345-9412-1c096c1e8fb1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $152065 | Estimated Completion Date:2026-07-08",
                    map_popup:
                        "  |  | Funding Awarded: $152065 | Estimated Completion Date:2026-07-08",
                    name: "La Puente Digital Empowerment Project: Building a Connected Community",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "La Puente Digital Empowerment Project: Building a Connected Community",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3ec01b9c-f458-4a06-b191-0282df47bc6e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $149000 | Estimated Completion Date:2025-10-10",
                    map_popup:
                        "  |  | Funding Awarded: $149000 | Estimated Completion Date:2025-10-10",
                    name: "Computer Confident MoVal (CC: MoVal)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Computer Confident MoVal (CC: MoVal)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d03d76eb-df66-485a-9369-52c18a5e361c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $20373 | Estimated Completion Date:2023-11-10",
                    map_popup:
                        "  |  | Funding Awarded: $20373 | Estimated Completion Date:2023-11-10",
                    name: "East Oakland Seniors Digital Inclusion",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "East Oakland Seniors Digital Inclusion",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "eac2236b-b3d0-4bd5-8241-f0ebb97d4795",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $20373 | Estimated Completion Date:2023-12-15",
                    map_popup:
                        "  |  | Funding Awarded: $20373 | Estimated Completion Date:2023-12-15",
                    name: "West Oakland Seniors Digital Inclusion",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "West Oakland Seniors Digital Inclusion",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7e3df478-2b72-49b7-a851-212c94e6f909",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $51099 | Estimated Completion Date:2026-05-30",
                    map_popup:
                        "  |  | Funding Awarded: $51099 | Estimated Completion Date:2026-05-30",
                    name: "City of Palm Springs Demuth Community Center Broadband Access Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "City of Palm Springs Demuth Community Center Broadband Access Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cf3c8c4f-f0a3-4aed-952f-4aa85d29062c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $80546 | Estimated Completion Date:2025-10-10",
                    map_popup:
                        "  |  | Funding Awarded: $80546 | Estimated Completion Date:2025-10-10",
                    name: "Palm Springs Public Library BA",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Palm Springs Public Library BA",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "82ef0578-894a-4938-ae92-8cf0d9bd5fc7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $17800 | Estimated Completion Date:2023-01-12",
                    map_popup:
                        "  |  | Funding Awarded: $17800 | Estimated Completion Date:2023-01-12",
                    name: "In Library Laptop Check Out",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "In Library Laptop Check Out",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "70b86d54-9cc7-41cc-860d-30cbfd90690d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50783 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $50783 | Estimated Completion Date:2022-12-31",
                    name: "El Gabilan Library Connects!",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "El Gabilan Library Connects!",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6ac1a417-7932-472b-94ba-ab8abc47b2fe",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $22551 | Estimated Completion Date:2023-05-24",
                    map_popup:
                        "  |  | Funding Awarded: $22551 | Estimated Completion Date:2023-05-24",
                    name: "San Leandro Manor Branch Library Digital Inclusion Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Leandro Manor Branch Library Digital Inclusion Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "986a2eb4-89c6-4179-b4c4-caef13aa53a2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $41895 | Estimated Completion Date:2023-10-31",
                    map_popup:
                        "  |  | Funding Awarded: $41895 | Estimated Completion Date:2023-10-31",
                    name: "South San Francisco Digital Literacy Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "South San Francisco Digital Literacy Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d5da21d8-b1bc-479f-8bd4-7605ba8dad64",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $58033 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $58033 | Estimated Completion Date:2022-06-30",
                    name: "Latino Digital Literacy-Bishop Elementary School",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Latino Digital Literacy-Bishop Elementary School",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "81c7ef3d-57b9-4b34-b767-ed21ddd59a18",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $58033 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $58033 | Estimated Completion Date:2022-06-30",
                    name: "Latino Digital Literacy-Columbia Middle School",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Latino Digital Literacy-Columbia Middle School",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ac7437fd-092c-485c-9ef6-a061191a0b59",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $40657 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $40657 | Estimated Completion Date:2022-06-30",
                    name: "Latino Digital Literacy-Ellis Elementary School",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Latino Digital Literacy-Ellis Elementary School",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ae2107a0-cce1-4995-ab78-a5d5b1223719",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $40657 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $40657 | Estimated Completion Date:2022-06-30",
                    name: "Latino Digital Literacy-Lakewood Elementary School",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Latino Digital Literacy-Lakewood Elementary School",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "382ad777-c874-4f47-ac10-a5b6a603690a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $58033 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $58033 | Estimated Completion Date:2022-06-30",
                    name: "Latino Digital Literacy-San Miguel Elementary School",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Latino Digital Literacy-San Miguel Elementary School",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9c22c112-8a86-4e2f-a11c-fb0a63574f2c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $58033 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $58033 | Estimated Completion Date:2022-06-30",
                    name: "Latino Digital Literacy-Vargas Elementary School",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Latino Digital Literacy-Vargas Elementary School",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8e2e3505-70eb-4b4a-9ad3-7bf79d7ca34a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $10629 | Estimated Completion Date:2023-05-30",
                    map_popup:
                        "  |  | Funding Awarded: $10629 | Estimated Completion Date:2023-05-30",
                    name: "Computer Literacy & Technology Training - Vila Hermosa",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Computer Literacy & Technology Training - Vila Hermosa",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "73bbb56b-20b0-4182-85bf-8bcce4693b71",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $32174 | Estimated Completion Date:2020-12-04",
                    map_popup:
                        "  |  | Funding Awarded: $32174 | Estimated Completion Date:2020-12-04",
                    name: "Bridging the Digital Divide",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bridging the Digital Divide",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4449c6cf-b012-4fe4-bf62-e5ce2fbd86e1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $72371 | Estimated Completion Date:2025-10-25",
                    map_popup:
                        "  |  | Funding Awarded: $72371 | Estimated Completion Date:2025-10-25",
                    name: "Community Bridges Digital Literacy Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Community Bridges Digital Literacy Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9d45cf2a-3f17-4524-82de-0aa9537f5ed8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $27588 | Estimated Completion Date:2021-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $27588 | Estimated Completion Date:2021-09-30",
                    name: "El Sobrante Library Reconstruction",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "El Sobrante Library Reconstruction",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2710d8ba-2598-4a36-a9b8-8393f041734a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $3375700 | Estimated Completion Date:2025-10-27",
                    map_popup:
                        "  |  | Funding Awarded: $3375700 | Estimated Completion Date:2025-10-27",
                    name: "County of Los Angeles - Digital Navigator Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "County of Los Angeles - Digital Navigator Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "359057b1-5d11-44d1-bb7b-04d31a146dfe",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $25027 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $25027 | Estimated Completion Date:2023-12-03",
                    name: "Bridging the Digital Gap Among Older Adults - Guerneville",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bridging the Digital Gap Among Older Adults - Guerneville",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8c11f571-2fba-4d17-b69b-5c4f1847ecfd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Broadband Access |  | Funding Awarded: $85000 | Estimated Completion Date:2025-04-13",
                    map_popup:
                        " Broadband Access |  | Funding Awarded: $85000 | Estimated Completion Date:2025-04-13",
                    name: "Yolo County Affordable Connectivity Program Enrollment Outreach",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Yolo County Affordable Connectivity Program Enrollment Outreach",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e6e2f313-baf4-4a7c-ae24-3045ee03d573",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $17228 | Estimated Completion Date:2024-02-23",
                    map_popup:
                        "  |  | Funding Awarded: $17228 | Estimated Completion Date:2024-02-23",
                    name: "DISH Supportive Housing Digital Literacy Program-Camelot",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "DISH Supportive Housing Digital Literacy Program-Camelot",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ed74cb0f-1398-4301-8516-62db88b9d7a8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $17228 | Estimated Completion Date:2023-12-12",
                    map_popup:
                        "  |  | Funding Awarded: $17228 | Estimated Completion Date:2023-12-12",
                    name: "DISH Supportive Housing Digital Literacy Program-Star",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "DISH Supportive Housing Digital Literacy Program-Star",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1a4b926b-d6c4-4c39-b168-093ea3793d05",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $34965 | Estimated Completion Date:2025-10-04",
                    map_popup:
                        "  |  | Funding Awarded: $34965 | Estimated Completion Date:2025-10-04",
                    name: "Community Technology Associate (CTA) Digital Literacy Program - Bayview/Hunters Point",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Community Technology Associate (CTA) Digital Literacy Program - Bayview/Hunters Point",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "11841bdc-19e8-4c2e-9939-c49ab71e390d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $69930 | Estimated Completion Date:2025-10-04",
                    map_popup:
                        "  |  | Funding Awarded: $69930 | Estimated Completion Date:2025-10-04",
                    name: "Community Technology Associate (CTA) Digital Literacy Program - Hayes Valley/Fillmore",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Community Technology Associate (CTA) Digital Literacy Program - Hayes Valley/Fillmore",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8510c3b2-085e-4bd0-80c3-4b5b25b7883a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-12-03",
                    name: "100 Kings Circle-Cloverdale",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "100 Kings Circle-Cloverdale",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "652b5196-ae7a-4886-aa4b-f1d8d957572f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $18850 | Estimated Completion Date:2024-04-21",
                    map_popup:
                        "  |  | Funding Awarded: $18850 | Estimated Completion Date:2024-04-21",
                    name: "100 Ned's Way-Tiburon",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "100 Ned's Way-Tiburon",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "79e4f192-18d2-491b-bf27-a6e1a0017beb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $27095 | Estimated Completion Date:2024-07-17",
                    map_popup:
                        "  |  | Funding Awarded: $27095 | Estimated Completion Date:2024-07-17",
                    name: "1000 El Camino Real (Gateway Santa Clara)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "1000 El Camino Real (Gateway Santa Clara)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8ed5ed70-9634-40a4-8c6d-ca8fb5b0b103",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $23197 | Estimated Completion Date:2025-04-07",
                    map_popup:
                        "  |  | Funding Awarded: $23197 | Estimated Completion Date:2025-04-07",
                    name: "1101 Carver Road (Archway Commons I)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "1101 Carver Road (Archway Commons I)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "eeb9e87f-05bc-443e-b6c2-aa904dc9b3b5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-12-03",
                    name: "1535 W. San Carlos Street-San Jose",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "1535 W. San Carlos Street-San Jose",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2956612f-a54e-4769-a65a-de2b8ca1eebe",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $14626 | Estimated Completion Date:2023-12-01",
                    map_popup:
                        "  |  | Funding Awarded: $14626 | Estimated Completion Date:2023-12-01",
                    name: "16170 Monterey Road-Morgan Hill",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "16170 Monterey Road-Morgan Hill",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bf3a8d00-4d2d-448f-aa4b-97098b500fa3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $22620 | Estimated Completion Date:2024-03-11",
                    map_popup:
                        "  |  | Funding Awarded: $22620 | Estimated Completion Date:2024-03-11",
                    name: "164 N San Pedro Road-San Rafael",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "164 N San Pedro Road-San Rafael",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "558f11b8-1a13-44dd-b7a1-921a8e6c4b19",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $14703 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $14703 | Estimated Completion Date:2023-12-03",
                    name: "235 E. Dunne Avenue-Morgan Hill",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "235 E. Dunne Avenue-Morgan Hill",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "57497554-b00e-4e8c-aabc-21c375903436",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $30740 | Estimated Completion Date:2024-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $30740 | Estimated Completion Date:2024-07-31",
                    name: "2738 Kollmar Avenue (Taylor Oaks)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "2738 Kollmar Avenue (Taylor Oaks)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "069cae55-89f9-426c-ae47-fb4963d92ef7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-12-03",
                    map_popup:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-12-03",
                    name: "355 Race Street-San Jose",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "355 Race Street-San Jose",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "52c0d23a-cf1a-4906-aa7d-2394c66b3e23",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $18850 | Estimated Completion Date:2024-04-15",
                    map_popup:
                        "  |  | Funding Awarded: $18850 | Estimated Completion Date:2024-04-15",
                    name: "37 Miwok Way-Mill Valley",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "37 Miwok Way-Mill Valley",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "05112c32-e785-4132-9170-153a15c7fd2b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $23180 | Estimated Completion Date:2025-04-07",
                    map_popup:
                        "  |  | Funding Awarded: $23180 | Estimated Completion Date:2025-04-07",
                    name: "500 W. Linwood Ave Phase I (Avena Bella I)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "500 W. Linwood Ave Phase I (Avena Bella I)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "84491035-8f29-4f2a-a1ae-c1e7d0e8b876",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $23180 | Estimated Completion Date:2025-04-07",
                    map_popup:
                        "  |  | Funding Awarded: $23180 | Estimated Completion Date:2025-04-07",
                    name: "500 W. Linwood Ave Phase II (Avena Bella II)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "500 W. Linwood Ave Phase II (Avena Bella II)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e1dbe64c-b7fb-4636-9915-7d7f04c90b24",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $38560 | Estimated Completion Date:2025-04-07",
                    map_popup:
                        "  |  | Funding Awarded: $38560 | Estimated Completion Date:2025-04-07",
                    name: "5004 Hartnett Ave. (Crescent Park)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "5004 Hartnett Ave. (Crescent Park)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3691fce9-9eff-4ae9-9398-939f9c6895e2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $38587 | Estimated Completion Date:2025-04-07",
                    map_popup:
                        "  |  | Funding Awarded: $38587 | Estimated Completion Date:2025-04-07",
                    name: "5450 DeMarcus Blvd. (Camellia Place)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "5450 DeMarcus Blvd. (Camellia Place)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "43645fce-62c9-4b90-81a1-9ec59d9f504e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $22243 | Estimated Completion Date:2024-04-21",
                    map_popup:
                        "  |  | Funding Awarded: $22243 | Estimated Completion Date:2024-04-21",
                    name: "605 Willow Road-Menlo Park",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "605 Willow Road-Menlo Park",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "55883440-6004-4122-9ee8-9c97c6d80bd1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $18773 | Estimated Completion Date:2024-01-24",
                    map_popup:
                        "  |  | Funding Awarded: $18773 | Estimated Completion Date:2024-01-24",
                    name: "638 21st Street -Oakland",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "638 21st Street -Oakland",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f3ae2bef-1ab4-41f5-bcac-726318badb44",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $30740 | Estimated Completion Date:2024-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $30740 | Estimated Completion Date:2024-07-31",
                    name: "875 N. 10th Street (Cornerstone at Japantown)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "875 N. 10th Street (Cornerstone at Japantown)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cbbf0c24-52d4-4df2-9953-2b47a40317e0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $19856 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $19856 | Estimated Completion Date:2023-12-31",
                    name: "Eastern Park Apartments Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Eastern Park Apartments Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fb7ced13-d973-4122-8618-be4eb5e3b702",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2024-03-11",
                    map_popup:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2024-03-11",
                    name: "Estrella Vista",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Estrella Vista",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4e21da93-9261-4165-9637-a6ee04d13413",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-03-01",
                    map_popup:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2023-03-01",
                    name: "Fellowship Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fellowship Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1a748530-41ec-4b50-ba88-2458bf6e6bfb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2024-03-11",
                    map_popup:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2024-03-11",
                    name: "Markham Plaza I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Markham Plaza I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bfa519a3-1a49-474a-98e1-d1cb0b1f4653",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2024-03-11",
                    map_popup:
                        "  |  | Funding Awarded: $24505 | Estimated Completion Date:2024-03-11",
                    name: "Markham Plaza II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Markham Plaza II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ce9876cd-88c2-44cd-aba6-ed2a25f4652b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $19856 | Estimated Completion Date:2022-09-29",
                    map_popup:
                        "  |  | Funding Awarded: $19856 | Estimated Completion Date:2022-09-29",
                    name: "Town Park Towers Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Town Park Towers Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "51331e4b-10ed-41a4-baf0-a5267ff655b6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $19856 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $19856 | Estimated Completion Date:2023-12-31",
                    name: "Western Park Apartments Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Western Park Apartments Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a47296d9-3b9c-4a16-8c82-1f4c2dca8fee",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $31419 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $31419 | Estimated Completion Date:2023-03-31",
                    name: "Ashland Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ashland Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "98b115da-731a-4c41-a0fb-deb0cba08990",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $34143 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $34143 | Estimated Completion Date:2023-03-31",
                    name: "Cambrian Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cambrian Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fce21ab4-40cb-4a5f-b1bd-bfb9516baef1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $30965 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $30965 | Estimated Completion Date:2023-03-31",
                    name: "East Bluff",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "East Bluff",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e57270d7-da62-47c6-a5a8-87f293f49e5b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $25023 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $25023 | Estimated Completion Date:2023-03-31",
                    name: "Eden Issei Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Eden Issei Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "643eabff-e420-4a35-a436-c9034433b164",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $32554 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $32554 | Estimated Completion Date:2023-03-31",
                    name: "Eden Lodge",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Eden Lodge",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d2fcfc2c-b79f-4bb4-a8a1-d894bd49291c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $17933 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $17933 | Estimated Completion Date:2023-03-31",
                    name: "Estabrook Place",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Estabrook Place",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "701b5326-c727-4d98-9622-8a3f1d4ca5b9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $29376 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $29376 | Estimated Completion Date:2023-03-31",
                    name: "Ford Road Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ford Road Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f7647ddf-0998-42d1-b1d0-041e1b0c8f83",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $43158 | Estimated Completion Date:2025-04-04",
                    map_popup:
                        "  |  | Funding Awarded: $43158 | Estimated Completion Date:2025-04-04",
                    name: "Fremont",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fremont",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f380d68f-7a4b-4264-b1db-6b2679c0ab9b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $60403 | Estimated Completion Date:2025-04-04",
                    map_popup:
                        "  |  | Funding Awarded: $60403 | Estimated Completion Date:2025-04-04",
                    name: "North Bay",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "North Bay",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bb00811f-0bb3-49e4-be76-a13c2d3d579d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $25732 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $25732 | Estimated Completion Date:2023-03-31",
                    name: "Rivertown Place",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Rivertown Place",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f069d872-1b19-4eaf-ab4f-cc43706e18e4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $78760 | Estimated Completion Date:2025-04-04",
                    map_popup:
                        "  |  | Funding Awarded: $78760 | Estimated Completion Date:2025-04-04",
                    name: "San Diego",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Diego",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2a0a450c-3cbf-45ec-bfc3-8eb82e1728b2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $64707 | Estimated Completion Date:2025-04-04",
                    map_popup:
                        "  |  | Funding Awarded: $64707 | Estimated Completion Date:2025-04-04",
                    name: "Tri-Valley",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tri-Valley",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "50ac9c7d-cd91-45df-9192-5655d9a815d2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $30057 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $30057 | Estimated Completion Date:2023-03-31",
                    name: "Virginia Lane",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Virginia Lane",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "89fdf481-7a89-432b-a285-42461d76894d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $78397 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $78397 | Estimated Completion Date:2022-06-30",
                    name: "Bilingual Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bilingual Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6ec0e082-5464-4d76-b396-a6b9a344a315",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $11608 | Estimated Completion Date:2023-08-22",
                    map_popup:
                        "  |  | Funding Awarded: $11608 | Estimated Completion Date:2023-08-22",
                    name: "EngAGE in Digital Literacy - Cotton's Point Senior Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "EngAGE in Digital Literacy - Cotton's Point Senior Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5100f67a-e5b8-4132-af5c-c8bfece1034b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $15272 | Estimated Completion Date:2024-03-11",
                    map_popup:
                        "  |  | Funding Awarded: $15272 | Estimated Completion Date:2024-03-11",
                    name: "EngAGE in Technology",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "EngAGE in Technology",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a0fe88fd-0944-4a49-bf88-252e740e979d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $14889 | Estimated Completion Date:2024-03-11",
                    map_popup:
                        "  |  | Funding Awarded: $14889 | Estimated Completion Date:2024-03-11",
                    name: "EngAGE in Technology (Long Beach Senior Arts Colony)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "EngAGE in Technology (Long Beach Senior Arts Colony)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1ce8dd2f-1700-4c7e-8ddc-33489160b504",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $14180 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $14180 | Estimated Completion Date:2023-07-31",
                    name: "1180 4th Street: Digital Literacy in Supportive Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "1180 4th Street: Digital Literacy in Supportive Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "889b0021-201a-43e3-ba87-a123421ffb38",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $10635 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $10635 | Estimated Completion Date:2023-07-31",
                    name: "Auburn and Minna-Lee: Digital Literacy in Supportive Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Auburn and Minna-Lee: Digital Literacy in Supportive Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "66a2ac14-f611-4866-a3b2-3215b1191d90",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $17725 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $17725 | Estimated Completion Date:2023-07-31",
                    name: "The Crosby: Digital Literacy in Supportive Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Crosby: Digital Literacy in Supportive Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6a6b0d1a-5261-481e-b0b9-339390a22a5c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $10635 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $10635 | Estimated Completion Date:2023-07-31",
                    name: "The Elm: Digital Literacy in Supportive Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Elm: Digital Literacy in Supportive Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7ea3b4b9-50f3-40e7-88c8-6a152601ed00",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $14180 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $14180 | Estimated Completion Date:2023-07-31",
                    name: "The Henry: Digital Literacy in Supportive Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Henry: Digital Literacy in Supportive Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "524f1349-79a6-4f56-95fa-57fa98ade8f9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $14180 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $14180 | Estimated Completion Date:2023-07-31",
                    name: "The Mentone: Digital Literacy in Supportive Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Mentone: Digital Literacy in Supportive Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5d592739-7358-40c4-9714-85e8f4c097db",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $7090 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $7090 | Estimated Completion Date:2023-07-31",
                    name: "The Rose and Hillsdale: Digital Literacy in Supportive Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Rose and Hillsdale: Digital Literacy in Supportive Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fa28109a-3502-4125-a7df-d87e365e6ec8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $117770 | Estimated Completion Date:2026-05-30",
                    map_popup:
                        "  |  | Funding Awarded: $117770 | Estimated Completion Date:2026-05-30",
                    name: "Digital Connections Bay Area",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Connections Bay Area",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0de348e9-2654-4678-9903-d1b46d4eea37",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $87115 | Estimated Completion Date:2025-10-04",
                    map_popup:
                        "  |  | Funding Awarded: $87115 | Estimated Completion Date:2025-10-04",
                    name: "Digital Connections Central Los Angeles",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Connections Central Los Angeles",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2cf48bf3-7b52-465b-af00-dd22e8bb7bb3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $70300 | Estimated Completion Date:2025-10-04",
                    map_popup:
                        "  |  | Funding Awarded: $70300 | Estimated Completion Date:2025-10-04",
                    name: "EveryoneOn Call Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "EveryoneOn Call Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0ebd2350-d30c-4bd3-b339-7b7916c85ae2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $33615 | Estimated Completion Date:2024-03-11",
                    map_popup:
                        "  |  | Funding Awarded: $33615 | Estimated Completion Date:2024-03-11",
                    name: "Opportunity Connect",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Opportunity Connect",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4d229dde-e2e1-4334-83e9-0d19200282cc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $32154 | Estimated Completion Date:2024-03-03",
                    map_popup:
                        "  |  | Funding Awarded: $32154 | Estimated Completion Date:2024-03-03",
                    name: "Opportunity Connect",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Opportunity Connect",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "754264ad-a7a9-4ad5-a70e-4313f3d19a4e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $33615 | Estimated Completion Date:2024-03-11",
                    map_popup:
                        "  |  | Funding Awarded: $33615 | Estimated Completion Date:2024-03-11",
                    name: "Opportunity Connect",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Opportunity Connect",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "df7e0e81-e695-418c-a359-741322a4a11d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $32888 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $32888 | Estimated Completion Date:2023-12-31",
                    name: "Opportunity Connection",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Opportunity Connection",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d0ca5614-4bbc-4b15-ad1f-e2ccc3073ab6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $99653 | Estimated Completion Date:2025-04-05",
                    map_popup:
                        "  |  | Funding Awarded: $99653 | Estimated Completion Date:2025-04-05",
                    name: "Expanding Digital Literacy for the Aging",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Expanding Digital Literacy for the Aging",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5227bfb8-bf2b-4762-9ba5-5fcc09d5e475",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $99715 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $99715 | Estimated Completion Date:2022-12-31",
                    name: "The Tech Squad: Connecting Our Disconnected Seniors",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Tech Squad: Connecting Our Disconnected Seniors",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5f7d515a-08b0-4db7-8e57-2388548e69c9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $25233 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $25233 | Estimated Completion Date:2023-06-30",
                    name: "Access for All - Campbell",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Access for All - Campbell",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d955c17e-b707-4939-a54c-7c0f38c84b6f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $27503 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $27503 | Estimated Completion Date:2023-06-30",
                    name: "Access for All - Morgan Hill",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Access for All - Morgan Hill",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0cedf1e1-0787-47a8-b23f-70218585c989",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $9019 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $9019 | Estimated Completion Date:2023-06-30",
                    name: "Access for All - Mountain View",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Access for All - Mountain View",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "97039a64-b617-47d1-99c9-ed9890d5dc76",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $835 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $835 | Estimated Completion Date:2023-06-30",
                    name: "Access for All - San Jose 1",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Access for All - San Jose 1",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "50136720-4425-4af0-8018-fd651f62745a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $35448 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $35448 | Estimated Completion Date:2023-06-30",
                    name: "Access for All - San Jose 2",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Access for All - San Jose 2",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a8b72557-7083-4856-8efa-22fdeeb56372",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2025-04-24",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2025-04-24",
                    name: "Fresno Coalition for Digital Inclusion: Go Public Schools Fresno Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno Coalition for Digital Inclusion: Go Public Schools Fresno Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "511e56b2-a6e3-44ae-a5a1-61a04bb1822a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $88400 | Estimated Completion Date:2027-06-18",
                    map_popup:
                        "  |  | Funding Awarded: $88400 | Estimated Completion Date:2027-06-18",
                    name: "Digital Inclusion Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Inclusion Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "716b7572-c23e-42c9-9569-7afc96a1ab98",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $135625 | Estimated Completion Date:2026-02-07",
                    map_popup:
                        "  |  | Funding Awarded: $135625 | Estimated Completion Date:2026-02-07",
                    name: "GBBB Healthy Mom's and Babies Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "GBBB Healthy Mom's and Babies Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2a301a37-d27d-4d18-b797-d8c0fa49afcc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74350 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74350 | Estimated Completion Date:2025-04-03",
                    name: "Alta Loma District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Alta Loma District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "64c4186c-bb48-490c-8789-7b0a358ee22e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $75450 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $75450 | Estimated Completion Date:2025-04-03",
                    name: "Apple Valley Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Apple Valley Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a57dcb4f-a0fb-4ccd-9636-dfd326a20e30",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $73062 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $73062 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_29Palms_92277",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_29Palms_92277",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4257cb5e-b41d-488a-91c5-19833d81ab32",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $28567 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $28567 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Adelanto_92301",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Adelanto_92301",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c733d39a-8954-44e4-9d82-024799868ce7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $23815 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $23815 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Barstow_92311",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Barstow_92311",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "250084b9-e1f6-408a-b6de-3acc45f1df44",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $46154 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $46154 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Big Bear City_92314",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Big Bear City_92314",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c326122f-4480-4d2d-9c80-412f5a640d56",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $19927 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $19927 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Big Bear Lk_92315",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Big Bear Lk_92315",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fe94de7e-66b5-4c30-b79a-3432f1156251",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $44953 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $44953 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Chino_91710",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Chino_91710",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b3f04c19-6e02-4a64-9ee3-fe8419ef8c89",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $60769 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $60769 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Colton_92324",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Colton_92324",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "aae705c6-a423-452c-9535-98cd0a28b56f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $66590 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $66590 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Fontana_92335",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Fontana_92335",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "46e6503b-9790-4623-b723-c25e2b06058a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $66950 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $66950 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Fontana_92337",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Fontana_92337",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0aed515a-f27e-4820-9673-851d62a623a0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $69276 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $69276 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Hesperia_92345",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Hesperia_92345",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9b4af255-3ead-4cd7-b982-6e538d83bedf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $59317 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $59317 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Highland_92346",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Highland_92346",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "87edc82a-e942-4049-a7f8-06c5c33568fd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $44690 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $44690 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_LomaLinda_92354",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_LomaLinda_92354",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3eb827cc-3485-4ca5-a8cf-c781adaf60d9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $72198 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $72198 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Ontario_91761",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Ontario_91761",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0a16ad2e-d8bc-4330-8414-5c123d3f0544",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $72198 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $72198 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Ontario_91762",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Ontario_91762",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e68742dd-3181-4226-b2d8-cdb9673faa15",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $63884 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $63884 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Ontario_91764",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Ontario_91764",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ae79ced6-b57f-40f9-97de-3c746c7bd00f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $18430 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $18430 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_RanchoCuc_91730",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_RanchoCuc_91730",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e0d5cb50-c480-4cbb-b2f2-34872b1129cb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $18430 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $18430 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_RanchoCuc_91737",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_RanchoCuc_91737",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3b7f6f9e-3d57-4e5c-b425-8b644c309a3e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $18430 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $18430 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_RanchoCuc_91739",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_RanchoCuc_91739",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "789eafb0-37d4-4b61-a82b-61c2261c0a28",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $55647 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $55647 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Rialto_92376",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Rialto_92376",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b320cf9e-a618-494b-b1ce-47da91803191",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $55647 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $55647 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Rialto_92377",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Rialto_92377",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3ed531df-23ee-472a-976d-8d411fc4cd0e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $43090 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $43090 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Snbrndo_92404",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Snbrndo_92404",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1e8fb42b-942e-4c43-a59c-ab8152675f61",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $55866 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $55866 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Snbrndo_92405",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Snbrndo_92405",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4abbfe61-5d21-4f99-9678-0aac0244c4e5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $55866 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $55866 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Snbrndo_92408",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Snbrndo_92408",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a390dadd-539c-43a6-94c1-0638a8274bf3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $55866 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $55866 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Snbrndo_92411",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Snbrndo_92411",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "30245bcf-5ca4-43f0-a904-47ebd888ebc6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $29647 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $29647 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Upland_91784",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Upland_91784",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a5ce262e-2b1c-4d33-99f6-888aad8dea20",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $40462 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $40462 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Victorville_92392",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Victorville_92392",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8d766dd3-7e01-4ddd-b33a-793a942d1a21",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $39462 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $39462 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Victorville_92394",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Victorville_92394",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "afda6135-704b-4b3f-a092-9c4227422af1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $58305 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $58305 | Estimated Completion Date:2026-05-17",
                    name: "ARPA_Yucaipa_92399",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ARPA_Yucaipa_92399",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "30f2b7a9-82bc-427f-aafd-aadaf34fe6b8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $76440 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $76440 | Estimated Completion Date:2025-04-03",
                    name: "Barstow Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Barstow Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "745247f3-5b6d-4cc8-b47c-99155550ffe0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $75450 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $75450 | Estimated Completion Date:2025-04-03",
                    name: "Bear Valley Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bear Valley Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f8d65775-1e62-460b-8e07-6cb3d76b3141",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $73600 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $73600 | Estimated Completion Date:2025-04-03",
                    name: "Central School District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Central School District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a3967fea-9d7c-4be6-8134-71b11a11904b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74600 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74600 | Estimated Completion Date:2025-04-03",
                    name: "Chaffey Joint Union High School",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Chaffey Joint Union High School",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fcf80f70-0222-49f7-b9f4-9849985cbd24",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $73400 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $73400 | Estimated Completion Date:2025-04-03",
                    name: "Colton Joint UnifiedDistrict",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Colton Joint UnifiedDistrict",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ce9af1fd-4bd6-41db-ae97-9862ad107794",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74400 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74400 | Estimated Completion Date:2025-04-03",
                    name: "Cucamonga District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cucamonga District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a92bbfea-1d4f-46b6-a56a-9a5b4934dbc2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74050 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74050 | Estimated Completion Date:2025-04-03",
                    name: "Etiwanda District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Etiwanda District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6d38e243-cf08-4d01-9dfb-3d4a89bf2668",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $75300 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $75300 | Estimated Completion Date:2025-04-03",
                    name: "Helendale District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Helendale District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5dc8fb70-50bf-4303-b436-7f8379028066",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74900 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74900 | Estimated Completion Date:2025-04-03",
                    name: "Hesperia Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hesperia Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fbe514d7-d289-4a4a-9778-6f54780af708",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $75400 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $75400 | Estimated Completion Date:2025-04-03",
                    name: "Lucerne Valley Un District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lucerne Valley Un District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b3e92be0-592c-49d9-b306-ecf671c8d515",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74400 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74400 | Estimated Completion Date:2025-04-03",
                    name: "Mountan View District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mountan View District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "46a3fbfa-9dfc-41a2-bdaa-a0e584b1d7a1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74350 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74350 | Estimated Completion Date:2025-04-03",
                    name: "Ontario-Montclair District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ontario-Montclair District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d9793e26-8f49-44b4-bc1c-8f2824bd2696",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $75000 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $75000 | Estimated Completion Date:2025-04-03",
                    name: "Oro Grande District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Oro Grande District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6c7417a9-2521-428d-a01c-30b5581112c8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74050 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74050 | Estimated Completion Date:2025-04-03",
                    name: "Redlands Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Redlands Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "20d4ebb0-6696-469b-ae8d-58b7c2e61d85",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74550 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74550 | Estimated Completion Date:2025-04-03",
                    name: "Rim of World Un District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Rim of World Un District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dd24dd99-e417-4e91-8015-122b56f257b9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $73200 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $73200 | Estimated Completion Date:2025-04-03",
                    name: "San Bernardino City Un District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Bernardino City Un District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "15b65d81-24f8-463a-9111-79be1a4038dc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $81700 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $81700 | Estimated Completion Date:2025-04-03",
                    name: "SBVC Valley College CalWORKs",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "SBVC Valley College CalWORKs",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1869b335-1715-4dc0-ac70-2b3a0d628f0b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74000 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74000 | Estimated Completion Date:2025-04-03",
                    name: "Snowline Joint Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Snowline Joint Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b250ddc3-204e-4daa-96f6-a22d6b489f00",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74000 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74000 | Estimated Completion Date:2025-04-03",
                    name: "Upland Unified District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Upland Unified District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dc1f7cb2-da9c-42c3-ac82-aac26ec986dd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $75000 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $75000 | Estimated Completion Date:2025-04-03",
                    name: "Victor Elementary District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Victor Elementary District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "80e19998-2f97-4e7e-8adf-537cef814381",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74900 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $74900 | Estimated Completion Date:2025-04-03",
                    name: "Victor Valley Joint Un District",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Victor Valley Joint Un District",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ca69a4f9-3082-446f-b454-51c8250f3938",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24823 | Estimated Completion Date:2022-11-30",
                    map_popup:
                        "  |  | Funding Awarded: $24823 | Estimated Completion Date:2022-11-30",
                    name: "Family Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Family Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5d66d9a6-138c-4d19-85c2-75deacaed0e8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24310 | Estimated Completion Date:2023-09-20",
                    map_popup:
                        "  |  | Funding Awarded: $24310 | Estimated Completion Date:2023-09-20",
                    name: "Family Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Family Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a632ba73-6202-4194-b7b2-13beb99497ed",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $24310 | Estimated Completion Date:2023-09-20",
                    map_popup:
                        "  |  | Funding Awarded: $24310 | Estimated Completion Date:2023-09-20",
                    name: "Family Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Family Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "21a4b07b-aedb-4873-84d2-4fbd271f180e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $59127 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $59127 | Estimated Completion Date:2023-06-30",
                    name: "Digital Literacy in King City",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Literacy in King City",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fd1e5e3c-bdca-4e2e-9a1a-41c82ec2d93d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $14180 | Estimated Completion Date:2024-06-24",
                    map_popup:
                        "  |  | Funding Awarded: $14180 | Estimated Completion Date:2024-06-24",
                    name: "Hotel Essex: Digital Literacy in Supportive Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hotel Essex: Digital Literacy in Supportive Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "90d28ac8-56e4-4bb2-99af-5c8d1f179e1c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $14180 | Estimated Completion Date:2024-06-24",
                    map_popup:
                        "  |  | Funding Awarded: $14180 | Estimated Completion Date:2024-06-24",
                    name: "The Senator Hotel: Digital Literacy in Supportive Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Senator Hotel: Digital Literacy in Supportive Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a23be53f-a72f-45b2-bbc5-81f7e6c485f2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $30600 | Estimated Completion Date:2025-10-10",
                    map_popup:
                        "  |  | Funding Awarded: $30600 | Estimated Completion Date:2025-10-10",
                    name: "Southeast Cedar Courts",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Southeast Cedar Courts",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cea9c7f3-6748-4667-a80c-cbc51676d456",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $48275 | Estimated Completion Date:2025-10-10",
                    map_popup:
                        "  |  | Funding Awarded: $48275 | Estimated Completion Date:2025-10-10",
                    name: "Tech Camp Senior Edition - County West",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Camp Senior Edition - County West",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "93a4b91f-5e10-418f-bfc1-6d6b43eb28b7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $13643 | Estimated Completion Date:2024-01-09",
                    map_popup:
                        "  |  | Funding Awarded: $13643 | Estimated Completion Date:2024-01-09",
                    name: "Piedmont Gardens Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Piedmont Gardens Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "48b033ed-22ec-4a08-8d55-eb99640bd28a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $750525 | Estimated Completion Date:2020-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $750525 | Estimated Completion Date:2020-12-31",
                    name: "human-I-T Connect",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "human-I-T Connect",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "535ae6ae-a42f-4069-8ef8-ec047980a761",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $68138 | Estimated Completion Date:2024-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $68138 | Estimated Completion Date:2024-03-31",
                    name: "human-I-T Connect (130 Pine Ave)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "human-I-T Connect (130 Pine Ave)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9f79b041-21cb-4ee8-8482-5647cc5d46c8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $68138 | Estimated Completion Date:2024-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $68138 | Estimated Completion Date:2024-03-31",
                    name: "human-I-T Connect (200 Spring St.)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "human-I-T Connect (200 Spring St.)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9dc452b1-2739-4319-bdd6-2490d8a6a002",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $68138 | Estimated Completion Date:2024-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $68138 | Estimated Completion Date:2024-03-31",
                    name: "human-I-T Connect (4525 Sheila St.)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "human-I-T Connect (4525 Sheila St.)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4c446173-f8e0-4bbd-8476-607c3ffae275",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $2050000 | Estimated Completion Date:2025-11-15",
                    map_popup:
                        "  |  | Funding Awarded: $2050000 | Estimated Completion Date:2025-11-15",
                    name: "Human-I-T Connect Los Angeles County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Human-I-T Connect Los Angeles County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4b6e65e9-63ba-4860-a3ff-00ff19a41481",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $19412 | Estimated Completion Date:2021-06-01",
                    map_popup:
                        "  |  | Funding Awarded: $19412 | Estimated Completion Date:2021-06-01",
                    name: "Inglewood Public Library Digital Literacy Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Inglewood Public Library Digital Literacy Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "97b52a2f-3fa8-456a-81e1-dee8144c39bd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $1230000 | Estimated Completion Date:2025-11-17",
                    map_popup:
                        "  |  | Funding Awarded: $1230000 | Estimated Completion Date:2025-11-17",
                    name: "California Health Programs Beneficiaries: ACP Outreach and Enrollment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "California Health Programs Beneficiaries: ACP Outreach and Enrollment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7ffc7b99-f111-4996-a21d-2bfe0f54e811",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $1680 | Estimated Completion Date:2025-03-30",
                    map_popup:
                        "  |  | Funding Awarded: $1680 | Estimated Completion Date:2025-03-30",
                    name: "California Get Connected Collaborative - ICAN",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "California Get Connected Collaborative - ICAN",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e85c6c9e-c254-4a65-89c3-f515c4f15fa6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $87889 | Estimated Completion Date:2025-03-30",
                    map_popup:
                        "  |  | Funding Awarded: $87889 | Estimated Completion Date:2025-03-30",
                    name: "California Get Connected Collaborative - ICAN (1)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "California Get Connected Collaborative - ICAN (1)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fc1f5237-6d9a-4dee-bf7f-0e0278190ff6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $110841 | Estimated Completion Date:2025-10-11",
                    map_popup:
                        "  |  | Funding Awarded: $110841 | Estimated Completion Date:2025-10-11",
                    name: "Digital Literacy for New Americans: Digital Inclusion for School and Careers (DISC)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Literacy for New Americans: Digital Inclusion for School and Careers (DISC)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ec31279b-b1b5-4902-9d32-0c24a052f6f3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $139999 | Estimated Completion Date:2026-06-12",
                    map_popup:
                        "  |  | Funding Awarded: $139999 | Estimated Completion Date:2026-06-12",
                    name: "Loaves, Fishes & Computers: Advanciing the Community with Digital Equity",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Loaves, Fishes & Computers: Advanciing the Community with Digital Equity",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "601b863a-89c2-4d76-a5b0-f902c6c6219f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $23992 | Estimated Completion Date:2024-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $23992 | Estimated Completion Date:2024-09-30",
                    name: "Mosaica Family Apts: Improving Lives Through Digital Literacy and Access",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mosaica Family Apts: Improving Lives Through Digital Literacy and Access",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5b3b4370-5309-4b4e-ae01-52003c674b23",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $11230 | Estimated Completion Date:2024-03-11",
                    map_popup:
                        "  |  | Funding Awarded: $11230 | Estimated Completion Date:2024-03-11",
                    name: "Transition Age Youth Digital Literacy and Job Readiness Training in Sacramento",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Transition Age Youth Digital Literacy and Job Readiness Training in Sacramento",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6cd47c20-d002-4299-b872-fa18eb56493a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $74803 | Estimated Completion Date:2021-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $74803 | Estimated Completion Date:2021-09-30",
                    name: "Conectate y Avanza (Connect and Advance)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Conectate y Avanza (Connect and Advance)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d7f40789-fdbd-4e28-8c9f-63f04d353146",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28432 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $28432 | Estimated Completion Date:",
                    name: "Laguna Commons",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Laguna Commons",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "359743a9-a2e3-41ff-b785-461960466e01",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $23152 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $23152 | Estimated Completion Date:2022-06-30",
                    name: "Public Access Upgrade - Penn Valley Library",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Public Access Upgrade - Penn Valley Library",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "aabc17da-046e-434e-950e-61b8902b7389",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $19403 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $19403 | Estimated Completion Date:2022-06-30",
                    name: "Public Access Upgrade - Truckee Library",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Public Access Upgrade - Truckee Library",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e45cb02c-e476-4241-a4c1-aa38d92aa33d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $20075 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $20075 | Estimated Completion Date:2022-06-30",
                    name: "Public Access Upgrade, Madelyn Helling Library",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Public Access Upgrade, Madelyn Helling Library",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "255c904f-88bf-4021-96fd-eba57604d35d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $99502 | Estimated Completion Date:2025-04-03",
                    map_popup:
                        "  |  | Funding Awarded: $99502 | Estimated Completion Date:2025-04-03",
                    name: "Internet for all in Housing Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Internet for all in Housing Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9a0774c6-dddc-4ba9-b47d-05318d7cda1d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $27030 | Estimated Completion Date:2027-06-03",
                    map_popup:
                        "  |  | Funding Awarded: $27030 | Estimated Completion Date:2027-06-03",
                    name: "Digital Literacy Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Literacy Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9f2c66b8-504c-4e36-ad45-6ba766729e12",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $8883 | Estimated Completion Date:2022-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $8883 | Estimated Completion Date:2022-09-30",
                    name: "Mobile Classroom - Oakland Adult and Career Education (OACE)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mobile Classroom - Oakland Adult and Career Education (OACE)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bfe2fb72-f127-4a4f-9468-021099f21ad0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $134250 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $134250 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Call Center Broadband Signups - Alameda County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Call Center Broadband Signups - Alameda County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ce77380e-246e-41eb-b0ff-1cb8a30cf01b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $93250 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $93250 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Call Center Broadband Signups - Contra Costa County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Call Center Broadband Signups - Contra Costa County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e33d4d2f-d096-47da-8f98-3263f1283b19",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $72750 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $72750 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Call Center Broadband Signups - San Francisco County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Call Center Broadband Signups - San Francisco County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cf6999bc-7c7e-4669-9d40-b270b48878a3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $72750 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $72750 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Call Center Broadband Signups - San Mateo County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Call Center Broadband Signups - San Mateo County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "19fe6141-ffa7-477c-bcea-d8f9ceaf189e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $113750 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $113750 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Call Center Broadband Signups - Santa Clara County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Call Center Broadband Signups - Santa Clara County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cd00052d-0c8e-4ab2-8b33-143806b12b61",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Digital Literacy - Alameda County Housing Sites",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Digital Literacy - Alameda County Housing Sites",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "06ef97bb-bdd0-41ab-86d3-4075d9823637",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Digital Literacy - Alameda County Libraries",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Digital Literacy - Alameda County Libraries",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "beaf8cf4-44c6-48f3-87cc-df3666bb3fbe",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Digital Literacy - San Mateo County Housing Sites",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Digital Literacy - San Mateo County Housing Sites",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "31d186a3-5ea4-443e-955d-5e523b57a093",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Digital Literacy - San Mateo County Libraries",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Digital Literacy - San Mateo County Libraries",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "486cbf73-0497-4a1a-8412-95120d03d097",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $104395 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Digital Literacy - Solano County Libraries",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Digital Literacy - Solano County Libraries",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "93e26a37-51cd-4368-8919-2c38fca23cf5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-06-19",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-06-19",
                    name: "Tech Exchange: Oakland Broadband Access at the TecHub 2023-24",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Oakland Broadband Access at the TecHub 2023-24",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "13bdf1c5-374f-42d3-9889-003484fcb96e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $8737 | Estimated Completion Date:2020-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $8737 | Estimated Completion Date:2020-12-31",
                    name: "Get Connected Oakland- OUSD District 1 High Schools",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Get Connected Oakland- OUSD District 1 High Schools",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a5c78ac7-f534-4ea3-961f-5b424da42915",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $9854 | Estimated Completion Date:2020-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $9854 | Estimated Completion Date:2020-12-31",
                    name: "Get Connected Oakland- OUSD District 2 High Schools",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Get Connected Oakland- OUSD District 2 High Schools",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6e5b0f54-7c71-4c61-9335-4b6dcf4217a3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $47655 | Estimated Completion Date:2020-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $47655 | Estimated Completion Date:2020-12-31",
                    name: "Get Connected Oakland- OUSD District 5 High Schools",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Get Connected Oakland- OUSD District 5 High Schools",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e9d0f18f-ee76-4e77-8fa2-5b8239168596",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $47655 | Estimated Completion Date:2020-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $47655 | Estimated Completion Date:2020-12-31",
                    name: "Get Connected Oakland- OUSD District 6 High Schools",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Get Connected Oakland- OUSD District 6 High Schools",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "38eaa064-9c04-4ef1-8769-fb04965d9f4c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $47655 | Estimated Completion Date:2020-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $47655 | Estimated Completion Date:2020-12-31",
                    name: "Get Connected Oakland- OUSD District 7 High Schools",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Get Connected Oakland- OUSD District 7 High Schools",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9cf69adc-f71f-4558-b5ca-f9a428515ccd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $144000 | Estimated Completion Date:2025-03-26",
                    map_popup:
                        "  |  | Funding Awarded: $144000 | Estimated Completion Date:2025-03-26",
                    name: "Fresno Coalition for Digital Inclusion: PIQE Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno Coalition for Digital Inclusion: PIQE Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "943ea395-5bd8-4f98-ad85-86248c79441c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $82890 | Estimated Completion Date:2023-10-31",
                    map_popup:
                        "  |  | Funding Awarded: $82890 | Estimated Completion Date:2023-10-31",
                    name: "Community Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Community Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ec7292d8-4cff-4d58-8ba1-e8bb21672973",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $52028 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $52028 | Estimated Completion Date:2022-12-31",
                    name: "El Monte, CA Community Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "El Monte, CA Community Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7bef5352-02ff-4c7b-a8d0-963b27d1daba",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $52028 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $52028 | Estimated Completion Date:2022-12-31",
                    name: "Fullerton, CA Community Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fullerton, CA Community Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9521165f-f164-4703-98fa-a72d39c438b6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $52028 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $52028 | Estimated Completion Date:2022-12-31",
                    name: "Wilmington, CA Community Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Wilmington, CA Community Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0abd3f6f-be63-4fa6-8a57-f47d58effa78",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $148965 | Estimated Completion Date:2027-05-01",
                    map_popup:
                        "  |  | Funding Awarded: $148965 | Estimated Completion Date:2027-05-01",
                    name: "Digital Equity Lab",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Equity Lab",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "39aeb120-43fc-4c01-96bd-dc568b1424a3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $40472 | Estimated Completion Date:2022-08-31",
                    map_popup:
                        "  |  | Funding Awarded: $40472 | Estimated Completion Date:2022-08-31",
                    name: "RaB Broadband Access (Mosqueda)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "RaB Broadband Access (Mosqueda)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f63fcc30-00c7-418b-829b-13f86d8f9909",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $73639 | Estimated Completion Date:2022-08-31",
                    map_popup:
                        "  |  | Funding Awarded: $73639 | Estimated Completion Date:2022-08-31",
                    name: "RaB Digital Literacy 1.0 (Mosqueda)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "RaB Digital Literacy 1.0 (Mosqueda)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "08888a57-dabe-49a4-ab36-bd58b087b7a4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $73639 | Estimated Completion Date:2022-08-31",
                    map_popup:
                        "  |  | Funding Awarded: $73639 | Estimated Completion Date:2022-08-31",
                    name: "RaB Digital Literacy 1.0 (N Location)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "RaB Digital Literacy 1.0 (N Location)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3e46395c-2a26-4c4d-970c-0a5af113b813",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $79488 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $79488 | Estimated Completion Date:2022-12-31",
                    name: "DLP/Redwood City Main Library",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "DLP/Redwood City Main Library",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "854095fa-3f83-442b-9489-0278579ff3f2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $22747 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $22747 | Estimated Completion Date:2022-12-31",
                    name: "Redwood City Main Library",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Redwood City Main Library",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "31d2da77-bd4c-4741-a71a-7a35da2ac0d4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-16",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-16",
                    name: "Eastern Riverside County ACP Outreach Call Center Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Eastern Riverside County ACP Outreach Call Center Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f098926d-4dbc-4771-9afa-64d74f4525e1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-16",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-16",
                    name: "Northwestern Riverside County ACP Outreach Call Center Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Northwestern Riverside County ACP Outreach Call Center Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d77bedcd-20f7-492e-9960-bdaf0d636616",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-16",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2026-05-16",
                    name: "Southern Riverside County ACP Outreach Call Center Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Southern Riverside County ACP Outreach Call Center Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0ab71aa4-50b9-444a-b38c-f209b38f6f24",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $149099 | Estimated Completion Date:2026-05-27",
                    map_popup:
                        "  |  | Funding Awarded: $149099 | Estimated Completion Date:2026-05-27",
                    name: "Sacramento Zoroastrian Association DL",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sacramento Zoroastrian Association DL",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "291f3474-28bc-40a9-850c-394e36cd05d6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $227850 | Estimated Completion Date:2026-06-16",
                    map_popup:
                        "  |  | Funding Awarded: $227850 | Estimated Completion Date:2026-06-16",
                    name: "Sacred Heart Community Service BA",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sacred Heart Community Service BA",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0a8a3c26-6c0f-4710-aa4f-c1a132ea4666",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2025-04-04",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2025-04-04",
                    name: "SANDAG Get Connected Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "SANDAG Get Connected Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3a831847-4938-496d-8c21-503e62eafc50",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $98992 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $98992 | Estimated Completion Date:2022-12-31",
                    name: "SDFF Digital Literacy Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "SDFF Digital Literacy Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fb63f66a-19d6-4c90-a40f-570c2436c9ed",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $108000 | Estimated Completion Date:2026-05-30",
                    map_popup:
                        "  |  | Funding Awarded: $108000 | Estimated Completion Date:2026-05-30",
                    name: "Santa Barbara Partners in Education Computers for Families",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Santa Barbara Partners in Education Computers for Families",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ede33f48-8ce3-4602-82da-b030b32fb935",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $94963 | Estimated Completion Date:2020-06-20",
                    map_popup:
                        "  |  | Funding Awarded: $94963 | Estimated Completion Date:2020-06-20",
                    name: "Project Connect",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project Connect",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fda4a0eb-691d-4eb3-be3a-6aee7d90f3fe",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $22325 | Estimated Completion Date:2022-12-22",
                    map_popup:
                        "  |  | Funding Awarded: $22325 | Estimated Completion Date:2022-12-22",
                    name: "Almond Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Almond Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "46d13346-1e05-443d-8cbf-730945bbb5b0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $32251 | Estimated Completion Date:2022-12-22",
                    map_popup:
                        "  |  | Funding Awarded: $32251 | Estimated Completion Date:2022-12-22",
                    name: "Goshen Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Goshen Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9fb1865e-6657-426f-9aa0-5b023e9bd29b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $26579 | Estimated Completion Date:2022-12-22",
                    map_popup:
                        "  |  | Funding Awarded: $26579 | Estimated Completion Date:2022-12-22",
                    name: "Parksdale Village 2",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parksdale Village 2",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "070df0e3-4235-41ca-ba86-8f3d77471b2a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $72564 | Estimated Completion Date:2026-05-16",
                    map_popup:
                        "  |  | Funding Awarded: $72564 | Estimated Completion Date:2026-05-16",
                    name: "Shelter Care Resources DL",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Shelter Care Resources DL",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e6c9d768-4d16-4f8c-ab39-53de7c980e14",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $59883 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $59883 | Estimated Completion Date:2023-06-30",
                    name: "Digital Divide Outreach",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Divide Outreach",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2e1c15f2-26cd-44f6-895a-bd419418bb74",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $82750 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $82750 | Estimated Completion Date:2023-07-31",
                    name: "SURGE: Technology & Entrepeneurship Development Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "SURGE: Technology & Entrepeneurship Development Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0391ff72-cfec-4c80-ae53-3a51a36a8015",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $87081 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $87081 | Estimated Completion Date:2023-07-31",
                    name: "SURGE: Technology & Entrepeneurship Development Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "SURGE: Technology & Entrepeneurship Development Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7d638e15-3002-4d8d-86f9-050f99a06097",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $95288 | Estimated Completion Date:2026-05-17",
                    map_popup:
                        "  |  | Funding Awarded: $95288 | Estimated Completion Date:2026-05-17",
                    name: "Digital Dreamers Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Dreamers Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d8aa318c-98a4-4bf3-9146-709d4d27f640",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $41650 | Estimated Completion Date:2023-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $41650 | Estimated Completion Date:2023-12-31",
                    name: "Barrio Action Tech Center - Broadband Access",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Barrio Action Tech Center - Broadband Access",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2aa08894-fba4-4542-bbaf-8f9efc56da68",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $72640 | Estimated Completion Date:2024-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $72640 | Estimated Completion Date:2024-12-31",
                    name: "Barrrio Action Tech Center - Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Barrrio Action Tech Center - Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "36d66272-66f9-406e-9c13-c94718c2e107",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $41650 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $41650 | Estimated Completion Date:2022-06-30",
                    name: "Bell Gardens Tech Center-Broadband Access",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bell Gardens Tech Center-Broadband Access",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "853e48e9-b183-46f5-b08a-90ebceaf72f1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $72640 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $72640 | Estimated Completion Date:2022-06-30",
                    name: "Bell Gardens Tech Center-Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bell Gardens Tech Center-Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c136de06-e496-4e69-bca6-8552265e390e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $83466 | Estimated Completion Date:2021-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $83466 | Estimated Completion Date:2021-06-30",
                    name: "Bell Tech Center-Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bell Tech Center-Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2bc726ca-fc54-4778-bcef-7c593b60cd1f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $41650 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $41650 | Estimated Completion Date:2022-06-30",
                    name: "Cudahy Tech Center - Broadband Access",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cudahy Tech Center - Broadband Access",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a8bbfabd-907c-4982-829c-bd12ae488d89",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $72640 | Estimated Completion Date:2022-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $72640 | Estimated Completion Date:2022-06-30",
                    name: "Cudahy Tech Center - Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cudahy Tech Center - Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1c19966e-2399-4734-a0b2-9ff2953b5e42",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $12685 | Estimated Completion Date:2021-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $12685 | Estimated Completion Date:2021-06-30",
                    name: "Whittier Tech Center-Broadband Access",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Whittier Tech Center-Broadband Access",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "67457c1d-37ed-49c3-a7f2-a03cb0c44707",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $19822 | Estimated Completion Date:2026-06-01",
                    map_popup:
                        "  |  | Funding Awarded: $19822 | Estimated Completion Date:2026-06-01",
                    name: "Digital Literacy Class and Computer Assistance at The Little House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital Literacy Class and Computer Assistance at The Little House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "787cced1-3561-475b-9193-a36cf073d3da",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $61160 | Estimated Completion Date:2026-06-01",
                    map_popup:
                        "  |  | Funding Awarded: $61160 | Estimated Completion Date:2026-06-01",
                    name: "Free Public Wi-Fi at The Little House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Free Public Wi-Fi at The Little House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "50e343d7-3676-4919-9983-4f0d86c60801",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $45460 | Estimated Completion Date:2025-10-25",
                    map_popup:
                        "  |  | Funding Awarded: $45460 | Estimated Completion Date:2025-10-25",
                    name: "I.T. Bookman Community Center Digital Literacy Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "I.T. Bookman Community Center Digital Literacy Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b550a66a-181f-443b-9b4f-5eb0182b68de",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $51250 | Estimated Completion Date:2023-07-31",
                    map_popup:
                        "  |  | Funding Awarded: $51250 | Estimated Completion Date:2023-07-31",
                    name: "Tech Exchange: Call Center Broadband Signups",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Call Center Broadband Signups",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cafbc30c-30d7-4985-92ed-753730a99c32",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $76000 | Estimated Completion Date:2024-08-31",
                    map_popup:
                        "  |  | Funding Awarded: $76000 | Estimated Completion Date:2024-08-31",
                    name: "Tech Exchange: Contra Costa County Digital Literacy- CCC Library",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Contra Costa County Digital Literacy- CCC Library",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bdfdda57-2961-4848-b5ef-228384600012",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $76000 | Estimated Completion Date:2024-08-31",
                    map_popup:
                        "  |  | Funding Awarded: $76000 | Estimated Completion Date:2024-08-31",
                    name: "Tech Exchange: Contra Costa County Digital Literacy- Community Sites",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Contra Costa County Digital Literacy- Community Sites",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e2299929-337a-4673-a549-79e4410ed2c3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $116000 | Estimated Completion Date:2023-05-15",
                    map_popup:
                        "  |  | Funding Awarded: $116000 | Estimated Completion Date:2023-05-15",
                    name: "Tech Exchange: Oakland Broadband Access at the Tech Hub",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: Oakland Broadband Access at the Tech Hub",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "15c5ca12-676d-4164-99b6-eb4de0c5fec7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $38039 | Estimated Completion Date:2025-10-11",
                    map_popup:
                        "  |  | Funding Awarded: $38039 | Estimated Completion Date:2025-10-11",
                    name: "Tech Exchange: San Francisco Digital Literacy- Community Sites",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: San Francisco Digital Literacy- Community Sites",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e4083542-ec87-4cee-9c6a-6c8e221c5f47",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $38039 | Estimated Completion Date:2024-03-01",
                    map_popup:
                        "  |  | Funding Awarded: $38039 | Estimated Completion Date:2024-03-01",
                    name: "Tech Exchange: San Francisco Digital Literacy- SF Public Library",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: San Francisco Digital Literacy- SF Public Library",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0ff17864-2067-48b6-a1d1-1e52c66622fa",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $135400 | Estimated Completion Date:2025-04-13",
                    map_popup:
                        "  |  | Funding Awarded: $135400 | Estimated Completion Date:2025-04-13",
                    name: "Tech Exchange: San Jose Digital Literacy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tech Exchange: San Jose Digital Literacy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cbaa86f2-1997-43f6-86b9-317df75df8c4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2025-11-01",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2025-11-01",
                    name: "Advancing Tech Equity",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Advancing Tech Equity",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "23b51c3a-81c5-4285-a17b-69941233a1bc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $46320 | Estimated Completion Date:2022-04-01",
                    map_popup:
                        "  |  | Funding Awarded: $46320 | Estimated Completion Date:2022-04-01",
                    name: "Access San Jose",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Access San Jose",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "60c415aa-ed34-4e9d-8f8a-0e0e189b7c17",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $1414725 | Estimated Completion Date:2024-05-30",
                    map_popup:
                        "  |  | Funding Awarded: $1414725 | Estimated Completion Date:2024-05-30",
                    name: "Connecting Californians to Affordable, High-Speed Internet",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connecting Californians to Affordable, High-Speed Internet",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1f6bebf3-1f61-4385-b144-708b33c46799",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $56798 | Estimated Completion Date:2023-12-05",
                    map_popup:
                        "  |  | Funding Awarded: $56798 | Estimated Completion Date:2023-12-05",
                    name: "VSEDC Digital Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "VSEDC Digital Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "54ff0733-8086-4868-a7e1-9864aab4f11b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $109081 | Estimated Completion Date:2021-12-01",
                    map_popup:
                        "  |  | Funding Awarded: $109081 | Estimated Completion Date:2021-12-01",
                    name: "Vietnamese Community Digital Equity",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Vietnamese Community Digital Equity",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a74dad59-cfcf-4a0c-90c3-cc8f6a53a0c9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $77700 | Estimated Completion Date:2026-05-18",
                    map_popup:
                        "  |  | Funding Awarded: $77700 | Estimated Completion Date:2026-05-18",
                    name: "Vietnamese Internet Communication Technology (VICT) Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Vietnamese Internet Communication Technology (VICT) Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "37c2ca09-16fe-4300-ade6-69fe512a13c1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1814045 | Estimated Completion Date:",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1814045 | Estimated Completion Date:",
                    name: "Helendale",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Helendale",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bde15e08-6958-4eb1-9ccc-17448743e5d2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $149851 | Estimated Completion Date:2026-05-29",
                    map_popup:
                        "  |  | Funding Awarded: $149851 | Estimated Completion Date:2026-05-29",
                    name: "VietRISE Technology Library Program",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "VietRISE Technology Library Program",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "76bac5dd-0652-4f46-9c0a-47da261b6f68",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $130603 | Estimated Completion Date:2025-03-27",
                    map_popup:
                        "  |  | Funding Awarded: $130603 | Estimated Completion Date:2025-03-27",
                    name: "Vivalon Talking Tech",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Vivalon Talking Tech",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "131a52f9-2da9-4d00-a9a0-749ade4e1847",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $133500 | Estimated Completion Date:2025-10-28",
                    map_popup:
                        "  |  | Funding Awarded: $133500 | Estimated Completion Date:2025-10-28",
                    name: "Fresno Coalition for Digital Inclusion: Westside Family Preservation Services Network Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno Coalition for Digital Inclusion: Westside Family Preservation Services Network Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "69f0057b-2890-4203-be39-68886c08f8f7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $53584 | Estimated Completion Date:2024-03-11",
                    map_popup:
                        "  |  | Funding Awarded: $53584 | Estimated Completion Date:2024-03-11",
                    name: "Gen-Connect Digital Literacy Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gen-Connect Digital Literacy Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d185117d-a9cf-47a2-93b0-e5fdec8c8be6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $99803 | Estimated Completion Date:2026-05-16",
                    map_popup:
                        "  |  | Funding Awarded: $99803 | Estimated Completion Date:2026-05-16",
                    name: "Girls on the Mic: Digital Literacy & Creative Technology Training",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Girls on the Mic: Digital Literacy & Creative Technology Training",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6a853cc3-b345-4acb-8bab-77ecbdec8905",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $77550 | Estimated Completion Date:2021-03-01",
                    map_popup:
                        "  |  | Funding Awarded: $77550 | Estimated Completion Date:2021-03-01",
                    name: "Girls on the Mic: Digital Literacy &Technology Training for Girls",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Girls on the Mic: Digital Literacy &Technology Training for Girls",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f5935ee8-45fd-4429-8b38-04df89838ea1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $62335 | Estimated Completion Date:2022-06-01",
                    map_popup:
                        "  |  | Funding Awarded: $62335 | Estimated Completion Date:2022-06-01",
                    name: "Youth Institute - Tech Tutor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Youth Institute - Tech Tutor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "68a95296-8a3a-4221-84d2-0b470c2e238f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2026-01-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2026-01-01",
                    name: "Broadband Consortium Pacific Coast - Connecting Communities",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Broadband Consortium Pacific Coast - Connecting Communities",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1d089ada-883d-4f6f-8bc9-394329c090d1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $595650 | Estimated Completion Date:2027-05-31",
                    map_popup:
                        " Consortia |  | Funding Awarded: $595650 | Estimated Completion Date:2027-05-31",
                    name: "CASF funding grant",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "CASF funding grant",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e912d212-072d-4c1b-95f1-13cb9c596efb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $800000 | Estimated Completion Date:2027-02-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $800000 | Estimated Completion Date:2027-02-01",
                    name: "Connected Capital Area Broadband Consortium 2023-2026",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connected Capital Area Broadband Consortium 2023-2026",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7c4f2b02-49b5-4336-8e6c-94340a4469fd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $565582 | Estimated Completion Date:2026-02-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $565582 | Estimated Completion Date:2026-02-01",
                    name: "Gold Country Broadband Consortium",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gold Country Broadband Consortium",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "62f076dd-5bef-42e0-bb4f-1648a3958f36",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2026-02-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2026-02-01",
                    name: "Connected Eastern Sierra Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connected Eastern Sierra Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ab312378-f27a-483f-a2f9-6311b083404d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2026-04-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2026-04-01",
                    name: "Advancing Equitable Broadband Deployment for Los Angeles County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Advancing Equitable Broadband Deployment for Los Angeles County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f9b3b08c-07b4-41b3-ae6f-1a7d753c8c6a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2027-06-16",
                    map_popup:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2027-06-16",
                    name: "West Connect",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "West Connect",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "da13e1eb-d589-479f-9a59-1e32bcc894d2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $999971 | Estimated Completion Date:2028-05-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $999971 | Estimated Completion Date:2028-05-01",
                    name: "Connecting Northeastern California",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connecting Northeastern California",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cb7fd4d8-f001-407c-b9b0-e80c93b6084a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2027-01-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2027-01-01",
                    name: "San Joaquin Valley Regional Broadband Consortium 2023-2025",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Joaquin Valley Regional Broadband Consortium 2023-2025",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4e2211f7-9049-45fa-b518-9ea88b84d8c2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2026-02-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2026-02-01",
                    name: "Economic Resilience with Broadband Deployment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Economic Resilience with Broadband Deployment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2459a900-2065-4096-a2ee-99c43a02bc03",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2026-02-01",
                    map_popup:
                        " Consortia |  | Funding Awarded: $600000 | Estimated Completion Date:2026-02-01",
                    name: "Connected Tahoe",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connected Tahoe",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ac11e4ca-3292-489e-ab80-97d5f41b6ce0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $2662450 | Estimated Completion Date:2017-12-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $2662450 | Estimated Completion Date:2017-12-01",
                    name: "Connect Anza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connect Anza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "48984301-08bb-4646-8b36-549753973cc8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1796070 | Estimated Completion Date:2021-09-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1796070 | Estimated Completion Date:2021-09-01",
                    name: "Connect Anza Phase II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connect Anza Phase II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a1bbaa3a-62e7-49cc-b347-cf6d3d955d11",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $94919 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $94919 | Estimated Completion Date:2025-12-31",
                    name: "Connect Anza Phase III (RDOF Kicker)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connect Anza Phase III (RDOF Kicker)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "965fd97a-3bc9-4b88-a338-db8f4369b78e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $35816 | Estimated Completion Date:2011-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $35816 | Estimated Completion Date:2011-05-01",
                    name: "Blanchard",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Blanchard",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f2c634dc-b881-456e-bf16-6b2e761d9294",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $57596 | Estimated Completion Date:2011-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $57596 | Estimated Completion Date:2011-05-01",
                    name: "Grenada",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Grenada",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "43833663-4099-4ec3-aced-debcfddc10e6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $2420 | Estimated Completion Date:2011-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $2420 | Estimated Completion Date:2011-05-01",
                    name: "Mt. Wilson",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mt. Wilson",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "be85f19a-69d1-45bc-b1e4-231841f2608c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $137416 | Estimated Completion Date:2012-06-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $137416 | Estimated Completion Date:2012-06-01",
                    name: "Lodi",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lodi",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1ae72be5-061a-4798-a40d-60e0b3c0ad5a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $49869 | Estimated Completion Date:2012-06-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $49869 | Estimated Completion Date:2012-06-01",
                    name: "Easton",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Easton",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "82674ebd-501e-40b8-88d6-621670f50b9e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $36393 | Estimated Completion Date:2012-06-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $36393 | Estimated Completion Date:2012-06-01",
                    name: "Clovis",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Clovis",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cc6d3813-0680-44b6-8994-f334721deb9f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $93896 | Estimated Completion Date:2011-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $93896 | Estimated Completion Date:2011-05-01",
                    name: "Warner Springs",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Warner Springs",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "48509b60-0347-4dec-9aca-cb61bff6bcc0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1154469 | Estimated Completion Date:2012-10-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1154469 | Estimated Completion Date:2012-10-01",
                    name: "Tranquility and West Fresno",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tranquility and West Fresno",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "395277a9-c55d-42ba-8738-e033d76c6375",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1238550 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1238550 | Estimated Completion Date:2025-12-31",
                    name: "El Dorado North",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "El Dorado North",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "df4b9a00-78e5-48c2-914c-0f65e5080adf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1218497 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1218497 | Estimated Completion Date:2025-12-31",
                    name: "Tuolumne and Mariposa",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tuolumne and Mariposa",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3c932e00-f13e-47a1-98d7-30a23dc5fb1b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $519260 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $519260 | Estimated Completion Date:2025-12-31",
                    name: "Rural Fresno",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Rural Fresno",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "aebdc65d-0c46-4252-84e4-5a9909c31e1e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $511170 | Estimated Completion Date:2019-12-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $511170 | Estimated Completion Date:2019-12-01",
                    name: "Fresno Co. Coalinga-Huron Gigabit",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fresno Co. Coalinga-Huron Gigabit",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0283f574-75d5-45a2-83c6-ef3df4ce7d0e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $197185 | Estimated Completion Date:2020-09-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $197185 | Estimated Completion Date:2020-09-01",
                    name: "Highland Orchid Drive",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Highland Orchid Drive",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2455e767-87d8-4c73-be95-a1b248aa5d86",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $2120390 | Estimated Completion Date:2021-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $2120390 | Estimated Completion Date:2021-05-01",
                    name: "Country Meadows Mobile Home Park",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Country Meadows Mobile Home Park",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c57536e8-0b44-41ec-8a1f-b05ed5fa98b7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1445032 | Estimated Completion Date:2024-10-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1445032 | Estimated Completion Date:2024-10-01",
                    name: "El Dorado Estates",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "El Dorado Estates",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "73aca808-3398-45ba-a2dd-373bafef5168",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $784322 | Estimated Completion Date:2022-12-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $784322 | Estimated Completion Date:2022-12-01",
                    name: "Monterey Manor Mobile Home Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Monterey Manor Mobile Home Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "88d10a31-e38b-410b-ba80-e64108f87824",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $543530 | Estimated Completion Date:2021-12-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $543530 | Estimated Completion Date:2021-12-01",
                    name: "Villa Montclair Mobile Home Park",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Villa Montclair Mobile Home Park",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "101501b1-002a-41d3-a577-7dae3699bfc7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $967536 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $967536 | Estimated Completion Date:2025-12-31",
                    name: "Kingswood Estates",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Kingswood Estates",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2c2e3d95-ca42-4fef-8e4c-0de51ee0a969",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $745365 | Estimated Completion Date:2023-05-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $745365 | Estimated Completion Date:2023-05-31",
                    name: "River Oaks",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "River Oaks",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2827ae9c-310c-4da0-8c60-7d91b988e0cf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $62000 | Estimated Completion Date:2009-11-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $62000 | Estimated Completion Date:2009-11-01",
                    name: "Livingston",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Livingston",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "721197e0-78c5-4414-b2b5-54c9198b2d30",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Middle-Mile | Funding Awarded: $202557 | Estimated Completion Date:2026-02-01",
                    map_popup:
                        " Infrastructure | Middle-Mile | Funding Awarded: $202557 | Estimated Completion Date:2026-02-01",
                    name: "Petrolia",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Petrolia",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "97ca1460-ddc0-45f4-b1d7-69ef96f5e8ab",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $545690 | Estimated Completion Date:2017-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $545690 | Estimated Completion Date:2017-05-01",
                    name: "Shingletown",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Shingletown",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6e0e1dd4-5daf-4d74-a5ea-1e657d4c2407",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $5650000 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $5650000 | Estimated Completion Date:2025-12-31",
                    name: "Summits to the Sea",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Summits to the Sea",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4f295c79-6988-4118-ade3-67eebe53cc9f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Middle-Mile | Funding Awarded: $6659967 | Estimated Completion Date:2014-05-01",
                    map_popup:
                        " Infrastructure | Middle-Mile | Funding Awarded: $6659967 | Estimated Completion Date:2014-05-01",
                    name: "Central Valley Independent Network, LLC middle mile fiber-optics network infrast",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Central Valley Independent Network, LLC middle mile fiber-optics network infrast",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4ad67237-d6cd-42ec-b952-b36b73d12a43",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $117000 | Estimated Completion Date:2016-07-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $117000 | Estimated Completion Date:2016-07-01",
                    name: "Alpine",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Alpine",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "440ebe2a-5364-4137-ae02-2e2c3324de5a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $1458886 | Estimated Completion Date:2022-03-01",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $1458886 | Estimated Completion Date:2022-03-01",
                    name: "Lytle Creek",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lytle Creek",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2ad85c28-3b25-47b3-a48a-bf384a4923de",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $1262567 | Estimated Completion Date:2022-03-01",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $1262567 | Estimated Completion Date:2022-03-01",
                    name: "Desert Shores",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Desert Shores",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "271a77b8-a1e4-44fe-ab21-7c24df2a0232",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $399702 | Estimated Completion Date:2022-03-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $399702 | Estimated Completion Date:2022-03-01",
                    name: "Taft Cluster Project in Kern County",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Taft Cluster Project in Kern County",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4a89129e-ffab-43a6-a60b-43679f3398c4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $10912973 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $10912973 | Estimated Completion Date:2025-12-31",
                    name: "Northeast Project Phase I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Northeast Project Phase I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0685169a-4e82-4705-a8ea-a294d518d98d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1428479 | Estimated Completion Date:2024-02-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1428479 | Estimated Completion Date:2024-02-01",
                    name: "Smith River",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Smith River",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f4b2be8b-6c61-45a2-a3d8-96744ebdb8a3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $497427 | Estimated Completion Date:2024-03-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $497427 | Estimated Completion Date:2024-03-01",
                    name: "Crescent City",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Crescent City",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f8f76da8-32c4-455d-9f0c-eb9cc3fd92db",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $68168 | Estimated Completion Date:2012-03-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $68168 | Estimated Completion Date:2012-03-01",
                    name: "Del Norte",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Del Norte",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "43637874-8715-408e-8f18-eae9fd8790db",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $95919 | Estimated Completion Date:2012-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $95919 | Estimated Completion Date:2012-05-01",
                    name: "Alpine",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Alpine",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4cea7cab-0789-41ed-81b6-f4f5d669abc7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $2233542 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $2233542 | Estimated Completion Date:2025-12-31",
                    name: "Olinda",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Olinda",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d7cc9670-2ba7-4aa1-b324-2da02ff79172",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $8223340 | Estimated Completion Date:2023-07-01",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $8223340 | Estimated Completion Date:2023-07-01",
                    name: "Hoopa Valley Broadband Initiative",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hoopa Valley Broadband Initiative",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "24931185-6038-46a8-933c-9c9b433018c4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $5753240 | Estimated Completion Date:2012-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $5753240 | Estimated Completion Date:2012-05-01",
                    name: "Hwy 36 Hubmboldt-Trinity Counties",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hwy 36 Hubmboldt-Trinity Counties",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b44a0ab8-53e5-4493-87d6-981a5493684c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $17422572 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $17422572 | Estimated Completion Date:2025-12-31",
                    name: "Klamath River Rural Broadband Initiative",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Klamath River Rural Broadband Initiative",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "27f19da4-c9f3-433a-9ad6-7d4ecb6ab425",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $889093 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $889093 | Estimated Completion Date:2025-12-31",
                    name: "Mobile Home Park 1",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mobile Home Park 1",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "305bc139-6f3d-4400-867f-35e74af1ce85",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $29482766 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $29482766 | Estimated Completion Date:2025-12-31",
                    name: "Aromas-San Juan Project.",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Aromas-San Juan Project.",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a0c9e48e-eb1d-4457-96aa-e0db6aa386b3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Middle-Mile | Funding Awarded: $285992 | Estimated Completion Date:2023-05-01",
                    map_popup:
                        " Infrastructure | Middle-Mile | Funding Awarded: $285992 | Estimated Completion Date:2023-05-01",
                    name: "Kernville Interconnect Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Kernville Interconnect Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cf265d60-72db-4137-9f16-7fb35bbfa58b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $621280 | Estimated Completion Date:2024-04-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $621280 | Estimated Completion Date:2024-04-01",
                    name: "Buckeye-Banner Mountain South Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Buckeye-Banner Mountain South Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5a37f8cf-28bd-45f0-b100-7cd3cbb6478d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $195299 | Estimated Completion Date:2014-12-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $195299 | Estimated Completion Date:2014-12-01",
                    name: "Pinnacles Monument",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pinnacles Monument",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c445d699-ae91-4d34-98ab-1661052e67ac",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $1512163 | Estimated Completion Date:2022-04-01",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $1512163 | Estimated Completion Date:2022-04-01",
                    name: "Keddie",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Keddie",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3e8bd9bc-2031-4e3e-b032-0937092d417e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $2183427 | Estimated Completion Date:2022-03-01",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $2183427 | Estimated Completion Date:2022-03-01",
                    name: "Mohawk Vista",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mohawk Vista",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1832bb0e-9a97-4fdc-8677-797576c57b06",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $2777071 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $2777071 | Estimated Completion Date:2025-12-31",
                    name: "Lake Davis",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lake Davis",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "91a3a1b4-11bc-4ab1-87f0-f6a46bf0b417",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $3574494 | Estimated Completion Date:2022-07-01",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $3574494 | Estimated Completion Date:2022-07-01",
                    name: "Elysian Valley-Johnstonville",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Elysian Valley-Johnstonville",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a512381b-5e81-46ec-b8b1-7b37df384e85",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $3707475 | Estimated Completion Date:2024-10-01",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $3707475 | Estimated Completion Date:2024-10-01",
                    name: "Scott Road Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Scott Road Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f0a95a19-da11-495c-9566-705d2147ac03",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $5016256 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $5016256 | Estimated Completion Date:2025-12-31",
                    name: "Long Valley - Spring Garden Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Long Valley - Spring Garden Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5c510d1e-d92a-429a-881b-5eae48f79f53",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $4887905 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $4887905 | Estimated Completion Date:2025-12-31",
                    name: "Sierra Valley",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sierra Valley",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fd8cf322-d2de-486b-81a8-8cf7c828b866",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure |  | Funding Awarded: $1941754 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure |  | Funding Awarded: $1941754 | Estimated Completion Date:2025-12-31",
                    name: "Mohawk Valley",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mohawk Valley",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8853b4ca-1d19-410f-a17d-dbe726acc0f5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $506199 | Estimated Completion Date:2012-11-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $506199 | Estimated Completion Date:2012-11-01",
                    name: "Mojave Air and Space Port Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mojave Air and Space Port Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1af3f8f3-7f00-40d6-927c-8cb393b4933b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $12583343 | Estimated Completion Date:2017-09-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $12583343 | Estimated Completion Date:2017-09-01",
                    name: "Kern County High Desert",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Kern County High Desert",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5f624aa9-b4bf-4889-9cb0-6d20bdfeb0a2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $3426357 | Estimated Completion Date:2015-03-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $3426357 | Estimated Completion Date:2015-03-01",
                    name: "Boron",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Boron",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "552c0cef-3b08-46a2-b247-e41b722098c0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $4650593 | Estimated Completion Date:2017-09-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $4650593 | Estimated Completion Date:2017-09-01",
                    name: "Mono County Underserved",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mono County Underserved",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "836dfa44-df29-4dc5-9cbc-425eeb8dafc7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $2037721 | Estimated Completion Date:2017-09-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $2037721 | Estimated Completion Date:2017-09-01",
                    name: "Five Mining Communities",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Five Mining Communities",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a96dd0e4-5323-4ebd-8f7f-258b79832e51",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $6580007 | Estimated Completion Date:2018-09-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $6580007 | Estimated Completion Date:2018-09-01",
                    name: "Gigafy Mono",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gigafy Mono",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4ba1c26b-aa39-45a7-a4e0-6040bd80b83f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $7687016 | Estimated Completion Date:2018-09-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $7687016 | Estimated Completion Date:2018-09-01",
                    name: "Gigafy Occidental",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gigafy Occidental",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fba07c19-0006-4fce-ab01-8ab536457f54",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $36690800 | Estimated Completion Date:2022-09-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $36690800 | Estimated Completion Date:2022-09-01",
                    name: "Gigafy Phelan",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gigafy Phelan",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "210d0c5c-42cb-484a-ad5c-b9b1b1edb8d5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $7603656 | Estimated Completion Date:2023-08-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $7603656 | Estimated Completion Date:2023-08-01",
                    name: "Gigafy Williams",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gigafy Williams",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ca1db7e6-35b3-4eb1-981f-216a3e2f62c2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $7565012 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $7565012 | Estimated Completion Date:2025-12-31",
                    name: "Gigafy Nevada City",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gigafy Nevada City",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3f608296-0e6e-47b2-bcf3-2ac7ca3a903a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $6151870 | Estimated Completion Date:2024-08-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $6151870 | Estimated Completion Date:2024-08-01",
                    name: "Gigafy Backus II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gigafy Backus II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bfbbf557-9b5a-4b15-8ba8-dad2465c52f0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Middle-Mile | Funding Awarded: $10640000 | Estimated Completion Date:2018-05-01",
                    map_popup:
                        " Infrastructure | Middle-Mile | Funding Awarded: $10640000 | Estimated Completion Date:2018-05-01",
                    name: "Connect Central Coast",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Connect Central Coast",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2b6e9bae-73f9-452e-80cc-dc2215b1b404",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $177954 | Estimated Completion Date:",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $177954 | Estimated Completion Date:",
                    name: "Paradise Road",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Paradise Road",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "76e66e44-0ae0-42dd-a06e-b069d43eb4ff",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1154780 | Estimated Completion Date:2015-09-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1154780 | Estimated Completion Date:2015-09-01",
                    name: "Auberry project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Auberry project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f253778a-b25d-462a-8cf0-eb6c3f4d4c58",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $898574 | Estimated Completion Date:2017-08-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $898574 | Estimated Completion Date:2017-08-01",
                    name: "Big Creek",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Big Creek",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "71e55edd-91bd-48de-94f8-9e08eedcb749",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1755042 | Estimated Completion Date:2025-12-31",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1755042 | Estimated Completion Date:2025-12-31",
                    name: "Beasore-Central Camp",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Beasore-Central Camp",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1712f9dd-e2d2-44b6-af86-4c366dd0078f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1027380 | Estimated Completion Date:2018-05-01",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1027380 | Estimated Completion Date:2018-05-01",
                    name: "Cressman",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cressman",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "59285ba2-1e08-4e86-b7dc-0fd034d7514e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Infrastructure | Last-Mile | Funding Awarded: $1937380 | Estimated Completion Date:",
                    map_popup:
                        " Infrastructure | Last-Mile | Funding Awarded: $1937380 | Estimated Completion Date:",
                    name: "Wrightwood",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Wrightwood",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "afced334-c2fe-4842-a0a4-b8fb6589abab",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $34593 | Estimated Completion Date:2017-12-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $34593 | Estimated Completion Date:2017-12-31",
                    name: "Armstrong Place Senior Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Armstrong Place Senior Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "99085bac-0c96-4142-964d-0c389054b7ec",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30038 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $30038 | Estimated Completion Date:2019-06-30",
                    name: "Chestnut Linden Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Chestnut Linden Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "80eb292c-0b05-4888-b96e-cdbbe8ad7306",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23550 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $23550 | Estimated Completion Date:2019-06-30",
                    name: "Emeryvilla",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Emeryvilla",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e8b13910-d2bd-4fcf-b7fb-f0a522d83009",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27382 | Estimated Completion Date:2017-12-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $27382 | Estimated Completion Date:2017-12-31",
                    name: "Geraldine Johnson Senior Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Geraldine Johnson Senior Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "16c897e7-c0f3-4745-b2fc-af742e6b7201",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25399 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $25399 | Estimated Completion Date:2019-06-30",
                    name: "Ironhorse at Central",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ironhorse at Central",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a8cec0c2-4053-43b2-ac5f-b94521fae8f2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25550 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $25550 | Estimated Completion Date:2019-06-30",
                    name: "Natoma Family Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Natoma Family Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ea729d02-3f7c-439f-82e7-08819a92f40d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $20520 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $20520 | Estimated Completion Date:2019-06-30",
                    name: "Richmond City Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Richmond City Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8cac5a6c-2665-4109-96cd-ce648c03dcb6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33130 | Estimated Completion Date:2017-12-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $33130 | Estimated Completion Date:2017-12-31",
                    name: "St. Joseph's Senior Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "St. Joseph's Senior Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3dc330e7-431e-44b5-a092-70146c200148",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28450 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $28450 | Estimated Completion Date:2019-06-30",
                    name: "Fargo Senior Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fargo Senior Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "937fe0b7-9b5c-4780-8666-84f1379b704d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25420 | Estimated Completion Date:2019-05-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $25420 | Estimated Completion Date:2019-05-31",
                    name: "Harrison Street Senior Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Harrison Street Senior Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b951e933-5c41-4970-9df8-cb7521769273",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24750 | Estimated Completion Date:2019-08-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $24750 | Estimated Completion Date:2019-08-01",
                    name: "Sylvester Rutledge Manor - North Oakland Senior Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sylvester Rutledge Manor - North Oakland Senior Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "15091eb3-6fdb-40b6-a8fa-05ed08ea5fb7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $48975 | Estimated Completion Date:2019-09-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $48975 | Estimated Completion Date:2019-09-30",
                    name: "Westlake Christian Terrace East",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Westlake Christian Terrace East",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "44f8e4fb-0120-421c-9e7d-49ced36a5dff",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28460 | Estimated Completion Date:2019-09-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $28460 | Estimated Completion Date:2019-09-30",
                    name: "Buchanan Park",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Buchanan Park",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dcd01d85-0327-439e-8afd-13d63a5735ac",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16160 | Estimated Completion Date:2019-09-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $16160 | Estimated Completion Date:2019-09-30",
                    name: "Casa Adobe",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Casa Adobe",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "84b68eb9-3b95-467f-89e5-13d49d9d2b4f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $34930 | Estimated Completion Date:2019-12-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $34930 | Estimated Completion Date:2019-12-31",
                    name: "Centertown",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Centertown",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "382e821f-38f4-4b6d-8f76-33c5518d4be7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $41070 | Estimated Completion Date:2019-12-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $41070 | Estimated Completion Date:2019-12-31",
                    name: "Don de Dios",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Don de Dios",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d7ed53ab-1daf-4f64-abd5-704b37daf613",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10500 | Estimated Completion Date:2020-09-04",
                    map_popup:
                        " Housing |  | Funding Awarded: $10500 | Estimated Completion Date:2020-09-04",
                    name: "Drakes Way",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Drakes Way",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "68affae7-c6c6-4cc5-b070-934ea3784d09",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $49080 | Estimated Completion Date:2019-12-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $49080 | Estimated Completion Date:2019-12-20",
                    name: "Elena Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Elena Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6482ab84-0063-4cf1-85be-9860b5cd802c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $41979 | Estimated Completion Date:2020-10-16",
                    map_popup:
                        " Housing |  | Funding Awarded: $41979 | Estimated Completion Date:2020-10-16",
                    name: "Floral Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Floral Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1869a7ca-8b3d-4fbe-aaed-2f337cddaa8e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $40012 | Estimated Completion Date:2020-10-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $40012 | Estimated Completion Date:2020-10-20",
                    name: "Fountain West",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fountain West",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "09cf4cc0-59e5-4fe7-a311-63e3b17b69dc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15890 | Estimated Completion Date:2019-09-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $15890 | Estimated Completion Date:2019-09-30",
                    name: "Golden Oaks",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Golden Oaks",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3ff6f5da-d3d5-4f1d-9a26-e3c46812827b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $48815 | Estimated Completion Date:2020-03-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $48815 | Estimated Completion Date:2020-03-31",
                    name: "Los Robles",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Los Robles",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "213b36e6-7b64-42a7-a851-fc102ab79e17",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $14765 | Estimated Completion Date:2019-09-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $14765 | Estimated Completion Date:2019-09-30",
                    name: "Point Reyes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Point Reyes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c0254aac-cbdf-4fe6-99d8-f19d039aa50d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $49935 | Estimated Completion Date:2019-12-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $49935 | Estimated Completion Date:2019-12-31",
                    name: "Pollard Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pollard Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b773cb2e-6b40-40b2-b0d2-98a30a797090",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $20930 | Estimated Completion Date:2020-05-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $20930 | Estimated Completion Date:2020-05-20",
                    name: "Riviera Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Riviera Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a9980dee-c0b1-4c8a-91b5-25326126738b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $41478 | Estimated Completion Date:2020-07-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $41478 | Estimated Completion Date:2020-07-01",
                    name: "San Clemente Place",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Clemente Place",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "67e4bbf0-af40-42d2-92b8-e7892e2862bd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $14680 | Estimated Completion Date:2019-11-21",
                    map_popup:
                        " Housing |  | Funding Awarded: $14680 | Estimated Completion Date:2019-11-21",
                    name: "Silver Oak",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Silver Oak",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8afacd51-4217-4b60-a949-9156437ed132",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $18513 | Estimated Completion Date:2019-12-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $18513 | Estimated Completion Date:2019-12-31",
                    name: "The Oaks",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Oaks",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2432905b-6d33-44a3-869a-4f5ae0c0ae79",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $47685 | Estimated Completion Date:2020-09-29",
                    map_popup:
                        " Housing |  | Funding Awarded: $47685 | Estimated Completion Date:2020-09-29",
                    name: "Village Avante",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Village Avante",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8d0b41c3-8076-4a8d-80a3-f8ded8e103f5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $35197 | Estimated Completion Date:2020-05-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $35197 | Estimated Completion Date:2020-05-20",
                    name: "Vista Park 1",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Vista Park 1",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6f89558d-8125-4687-8dbd-a80f117ea442",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $35517 | Estimated Completion Date:2020-05-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $35517 | Estimated Completion Date:2020-05-20",
                    name: "Vista Park 2",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Vista Park 2",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ab5a85e4-5c8a-4f6c-b94f-77311423dfe1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $38645 | Estimated Completion Date:2022-02-23",
                    map_popup:
                        " Housing |  | Funding Awarded: $38645 | Estimated Completion Date:2022-02-23",
                    name: "California Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "California Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a4312baf-8f54-4751-b522-723b4eeecdcf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $45260 | Estimated Completion Date:2022-03-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $45260 | Estimated Completion Date:2022-03-30",
                    name: "Noble Tower Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Noble Tower Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "da7b735f-77bc-41d6-b4e1-0290470ee435",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12880 | Estimated Completion Date:2019-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $12880 | Estimated Completion Date:2019-01-31",
                    name: "801 Alma Family Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "801 Alma Family Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "00005dd9-be2d-4810-b721-7b7c0c960528",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $18030 | Estimated Completion Date:2018-07-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $18030 | Estimated Completion Date:2018-07-01",
                    name: "Altenheim",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Altenheim",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "43dc1914-a50e-44b4-84b7-3d28adf23f88",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12880 | Estimated Completion Date:2019-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $12880 | Estimated Completion Date:2019-01-31",
                    name: "Carlow Court Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Carlow Court Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cb4fd90f-3876-4a24-9fbd-0a796a720f28",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15615 | Estimated Completion Date:2018-07-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $15615 | Estimated Completion Date:2018-07-01",
                    name: "Cottonwood Place Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cottonwood Place Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "37a03f5b-d407-4a84-b60c-8e01581224fc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12830 | Estimated Completion Date:2018-07-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $12830 | Estimated Completion Date:2018-07-01",
                    name: "Studio 819 Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Studio 819 Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "74369236-8dc4-4b3a-a717-7e1101821a93",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12480 | Estimated Completion Date:2018-07-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $12480 | Estimated Completion Date:2018-07-01",
                    name: "Wexford Way",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Wexford Way",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ec72947a-cfbd-499e-aa10-ef6128eb6fc8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $41612 | Estimated Completion Date:2018-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $41612 | Estimated Completion Date:2018-06-30",
                    name: "Bishop Swing Community House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bishop Swing Community House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0cdc6406-d570-4ce3-8adb-adb89e3b6284",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $35547 | Estimated Completion Date:2018-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $35547 | Estimated Completion Date:2018-06-30",
                    name: "Canon Barcus Community House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Canon Barcus Community House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "64747dac-0619-401b-b7c5-f4879620a565",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $36092 | Estimated Completion Date:2018-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $36092 | Estimated Completion Date:2018-06-30",
                    name: "Canon Kip Community House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Canon Kip Community House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "989d43d6-4399-4dc2-91c1-9f76dfc48d58",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25053 | Estimated Completion Date:2020-03-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $25053 | Estimated Completion Date:2020-03-20",
                    name: "Casa Feliz Studios",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Casa Feliz Studios",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b463e8a3-4f4d-46de-8499-3816b00d076f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $11858 | Estimated Completion Date:2020-02-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $11858 | Estimated Completion Date:2020-02-15",
                    name: "Creekview inn",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Creekview inn",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4bd2eebb-09ee-4bdd-b8f0-079fc0be21aa",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22712 | Estimated Completion Date:2017-03-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $22712 | Estimated Completion Date:2017-03-10",
                    name: "Curtner Studios Digital Connections",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Curtner Studios Digital Connections",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b3cde4da-ff4d-463a-966a-1d8a5d506536",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27062 | Estimated Completion Date:2020-03-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $27062 | Estimated Completion Date:2020-03-30",
                    name: "Fourth Street Apts",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fourth Street Apts",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "620117b5-d98c-4106-8055-2f5aae7e2621",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27069 | Estimated Completion Date:2020-03-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $27069 | Estimated Completion Date:2020-03-30",
                    name: "Japantown Senior Apts",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Japantown Senior Apts",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d74699c8-4d07-4f9f-acbe-b2b9d3191a57",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26770 | Estimated Completion Date:2020-03-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $26770 | Estimated Completion Date:2020-03-30",
                    name: "Orchard Parkview",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Orchard Parkview",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ff7b78d2-0a20-4804-be38-eee02d018d99",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $19223 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $19223 | Estimated Completion Date:2018-01-31",
                    name: "Carmelitos Housing Development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Carmelitos Housing Development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6b583992-a006-449d-a75a-7f1fc4547939",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $19223 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $19223 | Estimated Completion Date:2018-01-31",
                    name: "Nueva Maravilla Housing Development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Nueva Maravilla Housing Development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5887b930-8c61-4652-b0b5-7c8c4d3c1ee2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $110309 | Estimated Completion Date:2024-03-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $110309 | Estimated Completion Date:2024-03-01",
                    name: "HACSB Digital Literacy Centers Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "HACSB Digital Literacy Centers Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "141f57da-e996-4bb7-a291-b91e90ec2d4f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21043 | Estimated Completion Date:2024-10-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $21043 | Estimated Completion Date:2024-10-31",
                    name: "Maplewood homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Maplewood homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a78e202b-3683-49a5-b591-2708ff501b4a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $8363 | Estimated Completion Date:2018-09-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $8363 | Estimated Completion Date:2018-09-30",
                    name: "Ceres Court Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ceres Court Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b59098ad-a3c3-4503-8cdf-2459333e868f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $9638 | Estimated Completion Date:2018-09-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $9638 | Estimated Completion Date:2018-09-30",
                    name: "Ceres Way Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ceres Way Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9306a143-5a24-4a87-96d1-d9cef6417e6d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12483 | Estimated Completion Date:2017-08-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $12483 | Estimated Completion Date:2017-08-31",
                    name: "Puerto del Sol Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Puerto del Sol Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c4d3d095-254a-4142-8953-a638df52986a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10637 | Estimated Completion Date:2018-09-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $10637 | Estimated Completion Date:2018-09-30",
                    name: "Woodglen Vista Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Woodglen Vista Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "61d1395c-6bd8-444e-b240-6cbf240b80a8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25118 | Estimated Completion Date:2018-08-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $25118 | Estimated Completion Date:2018-08-31",
                    name: "Lemon Hill",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lemon Hill",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "eeaa3683-0694-434f-904e-3cc4496d0768",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25824 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $25824 | Estimated Completion Date:2019-06-30",
                    name: "Moore Village Mutual Housing Community",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Moore Village Mutual Housing Community",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e0a8a9b1-e20f-4510-8fd9-7b9ab0f9c7eb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22764 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $22764 | Estimated Completion Date:2019-06-30",
                    name: "Mutual Housing at Dixianne",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mutual Housing at Dixianne",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d7e05b50-b487-4b4d-b076-c06755b35c43",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28891 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $28891 | Estimated Completion Date:2019-06-30",
                    name: "Mutual Housing at Norwood",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mutual Housing at Norwood",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "469feb49-dfb7-441f-b317-1f36ed17607a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27997 | Estimated Completion Date:2018-08-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $27997 | Estimated Completion Date:2018-08-31",
                    name: "Mutual Housing at Sky Park",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mutual Housing at Sky Park",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "14e98f9e-deaf-4f8f-ba81-f9b88e928806",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24763 | Estimated Completion Date:2018-08-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $24763 | Estimated Completion Date:2018-08-31",
                    name: "Mutual Housing at Spring Lake",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mutual Housing at Spring Lake",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8e0bea24-7242-41a9-97ad-d1af641ef447",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $31964 | Estimated Completion Date:2018-08-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $31964 | Estimated Completion Date:2018-08-31",
                    name: "Mutual Housing at the Highlands",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mutual Housing at the Highlands",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8beb8304-1812-44f9-8ed0-2a3ef8001f4a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26251 | Estimated Completion Date:2018-08-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $26251 | Estimated Completion Date:2018-08-31",
                    name: "New Harmony",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "New Harmony",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "34d76170-4e1a-4d84-ab5f-9fe1710a214a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $19722 | Estimated Completion Date:2018-08-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $19722 | Estimated Completion Date:2018-08-31",
                    name: "Owendale",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Owendale",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6f07d72e-0f8e-48a5-9b7a-73e67ddbc689",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23272 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $23272 | Estimated Completion Date:2019-06-30",
                    name: "Tremont Green Mutual Housing Community",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tremont Green Mutual Housing Community",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3fc5181f-5fcb-4b29-b032-0e63624c7576",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22411 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $22411 | Estimated Completion Date:2019-06-30",
                    name: "Twin Pines Mutual Housing Community",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Twin Pines Mutual Housing Community",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d936e55b-f44f-4742-a2b7-455d2edf6518",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $80214 | Estimated Completion Date:2022-11-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $80214 | Estimated Completion Date:2022-11-15",
                    name: "Lockwood Learning Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lockwood Learning Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2c286b76-d94c-44bb-9a07-f68a9df63f3f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $9212 | Estimated Completion Date:2019-08-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $9212 | Estimated Completion Date:2019-08-15",
                    name: "Ocean View Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ocean View Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "61a9d883-0fcc-43ba-8de5-209e4434ccb5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $6726 | Estimated Completion Date:2019-08-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $6726 | Estimated Completion Date:2019-08-15",
                    name: "Oceanside Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Oceanside Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f4e780c3-0ca2-40ec-b431-41b7a80d2ebf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $7023 | Estimated Completion Date:2016-11-09",
                    map_popup:
                        " Housing |  | Funding Awarded: $7023 | Estimated Completion Date:2016-11-09",
                    name: "575 Vallejo Street Senior Apartments Adoption",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "575 Vallejo Street Senior Apartments Adoption",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9ea20ca4-2848-42de-80db-517a06977f7c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $6772 | Estimated Completion Date:2016-11-03",
                    map_popup:
                        " Housing |  | Funding Awarded: $6772 | Estimated Completion Date:2016-11-03",
                    name: "Acacia Lane Senior Apartments Adoption",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Acacia Lane Senior Apartments Adoption",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "aeaedaca-6fb3-4569-9e36-6db51b31194b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $9030 | Estimated Completion Date:2016-11-17",
                    map_popup:
                        " Housing |  | Funding Awarded: $9030 | Estimated Completion Date:2016-11-17",
                    name: "Casa Grande Senior Apartments Adoption",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Casa Grande Senior Apartments Adoption",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9b053916-0698-4e8d-be85-16e426708ac2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $3512 | Estimated Completion Date:2016-11-18",
                    map_popup:
                        " Housing |  | Funding Awarded: $3512 | Estimated Completion Date:2016-11-18",
                    name: "Caulfield Lane Senior Apartments Adoption",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Caulfield Lane Senior Apartments Adoption",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9a448539-bd6a-43ad-b8c4-9436b4655234",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $7776 | Estimated Completion Date:2016-11-04",
                    map_popup:
                        " Housing |  | Funding Awarded: $7776 | Estimated Completion Date:2016-11-04",
                    name: "Kellgren Senior Apartments Adoption",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Kellgren Senior Apartments Adoption",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8ed48fa0-1ec5-444f-a69f-13bde88f491c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $31660 | Estimated Completion Date:2020-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $31660 | Estimated Completion Date:2020-07-31",
                    name: "Hunters Point West",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hunters Point West",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cc41527d-9b65-4aad-831e-548b37a952dd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $48002 | Estimated Completion Date:2021-11-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $48002 | Estimated Completion Date:2021-11-30",
                    name: "Westbrook",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Westbrook",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a963883f-4724-4855-822e-a0bbdaa14cbd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $40756 | Estimated Completion Date:2017-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $40756 | Estimated Completion Date:2017-06-30",
                    name: "Arboleda Apartments Adoption",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Arboleda Apartments Adoption",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1b242ce5-52af-4f41-98f9-c1257d3d7c45",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33479 | Estimated Completion Date:2019-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $33479 | Estimated Completion Date:2019-07-31",
                    name: "Beth Asher",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Beth Asher",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4e642535-fdf7-4bc2-b617-fe41b54e0257",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $39991 | Estimated Completion Date:2019-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $39991 | Estimated Completion Date:2019-07-31",
                    name: "Columbia Park Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Columbia Park Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "81ae2541-2d93-443d-879d-b22c91986f99",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $31527 | Estimated Completion Date:2019-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $31527 | Estimated Completion Date:2019-07-31",
                    name: "Lawrence Moore Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lawrence Moore Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "85d6bbda-5ddd-4b24-96c6-51140e5b092c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29978 | Estimated Completion Date:2019-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $29978 | Estimated Completion Date:2019-07-31",
                    name: "Linda Glen",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Linda Glen",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "028d4a71-a009-40b9-a94b-fb22c34e81c4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $48535 | Estimated Completion Date:2017-09-24",
                    map_popup:
                        " Housing |  | Funding Awarded: $48535 | Estimated Completion Date:2017-09-24",
                    name: "Merritt Crossing Adoption",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Merritt Crossing Adoption",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4439b38a-a843-4329-97ea-da21423c47f1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33838 | Estimated Completion Date:2019-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $33838 | Estimated Completion Date:2019-06-30",
                    name: "Orchards Senior Homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Orchards Senior Homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1a4d8092-436d-431f-8af5-7ac006a85009",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28770 | Estimated Completion Date:2019-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $28770 | Estimated Completion Date:2019-07-31",
                    name: "Sacramento Senior Homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sacramento Senior Homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d8896f32-70c6-45c0-97fa-3c39476a291b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $49807 | Estimated Completion Date:2018-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $49807 | Estimated Completion Date:2018-08-30",
                    name: "Satellite Central",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Satellite Central",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "80aa71f3-10b3-4a20-b17d-271224fd7aa1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $49679 | Estimated Completion Date:2017-09-24",
                    map_popup:
                        " Housing |  | Funding Awarded: $49679 | Estimated Completion Date:2017-09-24",
                    name: "Strawberry Creek Lodge Adoption",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Strawberry Creek Lodge Adoption",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "afc916d9-ae7c-4ee9-9a09-c60a26f5a648",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27173 | Estimated Completion Date:2019-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $27173 | Estimated Completion Date:2019-07-31",
                    name: "Stuart Pratt Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Stuart Pratt Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a6c643da-eef7-4b0f-b808-3215bb5d9ca5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $48547 | Estimated Completion Date:2018-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $48547 | Estimated Completion Date:2018-08-30",
                    name: "Valdez Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Valdez Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "53f65044-1d02-479f-8443-f7fb2607c6f0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $20806 | Estimated Completion Date:2017-12-05",
                    map_popup:
                        " Housing |  | Funding Awarded: $20806 | Estimated Completion Date:2017-12-05",
                    name: "Parc Grove Commons",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parc Grove Commons",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "714d202c-e52b-4bb8-8385-49e8b7b36745",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $18504 | Estimated Completion Date:2017-12-05",
                    map_popup:
                        " Housing |  | Funding Awarded: $18504 | Estimated Completion Date:2017-12-05",
                    name: "Viking Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Viking Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "719c1ac4-03aa-4f05-b215-3102053eb459",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $34506 | Estimated Completion Date:2020-02-29",
                    map_popup:
                        " Housing |  | Funding Awarded: $34506 | Estimated Completion Date:2020-02-29",
                    name: "Robert B Pitts Residences",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Robert B Pitts Residences",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "69f69242-7f5b-4878-86d4-e70025cf1d39",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12918 | Estimated Completion Date:2017-12-21",
                    map_popup:
                        " Housing |  | Funding Awarded: $12918 | Estimated Completion Date:2017-12-21",
                    name: "Patio Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Patio Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a49a81dc-9339-488d-b422-88276580c806",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $41188 | Estimated Completion Date:2019-07-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $41188 | Estimated Completion Date:2019-07-15",
                    name: "Washington Courtyards",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Washington Courtyards",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8352695f-4b46-43bc-bcf3-d53b25fb2fd6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29370 | Estimated Completion Date:2016-03-07",
                    map_popup:
                        " Housing |  | Funding Awarded: $29370 | Estimated Completion Date:2016-03-07",
                    name: "Laurel Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Laurel Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3da41d6d-3e87-4b04-9abd-e0c64240ade6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $44100 | Estimated Completion Date:2017-10-27",
                    map_popup:
                        " Housing |  | Funding Awarded: $44100 | Estimated Completion Date:2017-10-27",
                    name: "Villa Mirage",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Villa Mirage",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b78d4457-af19-4af0-ad2f-cfde9c965f2f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $37351 | Estimated Completion Date:2017-03-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $37351 | Estimated Completion Date:2017-03-15",
                    name: "Dudley Street Senior Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Dudley Street Senior Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8bddbf2a-c74f-42c5-a34c-76321c98c053",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $55350 | Estimated Completion Date:2021-11-24",
                    map_popup:
                        " Housing |  | Funding Awarded: $55350 | Estimated Completion Date:2021-11-24",
                    name: "Dutton Flats",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Dutton Flats",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "db70ad41-6055-4227-a3f2-f7b664ba2f68",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $7020 | Estimated Completion Date:2021-02-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $7020 | Estimated Completion Date:2021-02-28",
                    name: "Villa Del Mar",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Villa Del Mar",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "81b74dcb-ce96-407a-91ec-27c941858297",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $34020 | Estimated Completion Date:2017-09-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $34020 | Estimated Completion Date:2017-09-20",
                    name: "Butterfield Retirement",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Butterfield Retirement",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b4190c82-c0dc-49dc-bd3b-bc9e0a2e6091",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12600 | Estimated Completion Date:2016-07-27",
                    map_popup:
                        " Housing |  | Funding Awarded: $12600 | Estimated Completion Date:2016-07-27",
                    name: "Montgomery Oaks",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Montgomery Oaks",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3fb2a384-a1f9-4d2b-8d8c-2a20959baf68",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22963 | Estimated Completion Date:2016-10-03",
                    map_popup:
                        " Housing |  | Funding Awarded: $22963 | Estimated Completion Date:2016-10-03",
                    name: "Valle Naranjal Farmwork Housing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Valle Naranjal Farmwork Housing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "42bb810f-f3ff-4b7a-a452-bd8dc2bca354",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22063 | Estimated Completion Date:2017-05-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $22063 | Estimated Completion Date:2017-05-31",
                    name: "227 Bay",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "227 Bay",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "00435114-1bf4-4b0b-a598-ba8f3036e747",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30076 | Estimated Completion Date:2018-01-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $30076 | Estimated Completion Date:2018-01-15",
                    name: "Cedar Nettleton",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cedar Nettleton",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "73534ebb-82bf-441f-9103-94170e3d2727",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $85000 | Estimated Completion Date:2017-06-27",
                    map_popup:
                        " Housing |  | Funding Awarded: $85000 | Estimated Completion Date:2017-06-27",
                    name: "Cypress Cove",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cypress Cove",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a69bfb47-c7f1-429d-aeee-b86f791eb1d0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $41400 | Estimated Completion Date:2018-07-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $41400 | Estimated Completion Date:2018-07-10",
                    name: "Mission Cove",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mission Cove",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "90f4c889-6b84-428f-8fbd-f084dcc4ceee",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $34200 | Estimated Completion Date:2018-02-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $34200 | Estimated Completion Date:2018-02-28",
                    name: "North Park LGBT Senior",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "North Park LGBT Senior",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7031b580-b6d0-4590-959c-934341f42345",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15600 | Estimated Completion Date:2017-02-09",
                    map_popup:
                        " Housing |  | Funding Awarded: $15600 | Estimated Completion Date:2017-02-09",
                    name: "Northwest Manors II (Mountain)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Northwest Manors II (Mountain)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e911c051-8ed0-4cd2-ab9e-7f9339c6bbf8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10800 | Estimated Completion Date:2017-01-18",
                    map_popup:
                        " Housing |  | Funding Awarded: $10800 | Estimated Completion Date:2017-01-18",
                    name: "Northwest Manors II (Raymond)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Northwest Manors II (Raymond)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "880d082b-f8ba-42bf-83a3-e8e531eb7574",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $59400 | Estimated Completion Date:2018-11-09",
                    map_popup:
                        " Housing |  | Funding Awarded: $59400 | Estimated Completion Date:2018-11-09",
                    name: "Sunridge Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sunridge Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9f7df878-b8dc-4b82-88f1-b5222866c4dc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $7192 | Estimated Completion Date:2018-11-06",
                    map_popup:
                        " Housing |  | Funding Awarded: $7192 | Estimated Completion Date:2018-11-06",
                    name: "1410 Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "1410 Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "60bec9e2-bc0f-4d8c-b308-310516fdc1c2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23686 | Estimated Completion Date:2015-11-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $23686 | Estimated Completion Date:2015-11-01",
                    name: "Central Avenue Village Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Central Avenue Village Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d4097d59-f36e-4245-b7ff-299655c90bbe",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33694 | Estimated Completion Date:2017-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $33694 | Estimated Completion Date:2017-06-30",
                    name: "Juanita Tate Legacy Towers",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Juanita Tate Legacy Towers",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3f5469a3-31a4-42da-9d5e-90d023335f78",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10605 | Estimated Completion Date:2018-11-09",
                    map_popup:
                        " Housing |  | Funding Awarded: $10605 | Estimated Completion Date:2018-11-09",
                    name: "One Wilkins Place",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "One Wilkins Place",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6350247f-2621-43bb-962e-75c003e0b897",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $7650 | Estimated Completion Date:2018-11-12",
                    map_popup:
                        " Housing |  | Funding Awarded: $7650 | Estimated Completion Date:2018-11-12",
                    name: "Roberta II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Roberta II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "89d5c514-b620-4c48-9937-cdc64d1ace2c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10350 | Estimated Completion Date:2018-11-09",
                    map_popup:
                        " Housing |  | Funding Awarded: $10350 | Estimated Completion Date:2018-11-09",
                    name: "Roberta Stephens Apartments I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Roberta Stephens Apartments I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c6143521-0b5e-4471-b862-d249b01cb797",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30125 | Estimated Completion Date:2018-03-06",
                    map_popup:
                        " Housing |  | Funding Awarded: $30125 | Estimated Completion Date:2018-03-06",
                    name: "Buchanan Park",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Buchanan Park",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "88be81ff-7606-49ee-8e34-d66c95b2ab9c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21287 | Estimated Completion Date:2017-03-22",
                    map_popup:
                        " Housing |  | Funding Awarded: $21287 | Estimated Completion Date:2017-03-22",
                    name: "Casa Adobe",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Casa Adobe",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "19368a8f-e4b5-4dd9-9ab1-231a384fdf8e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $40620 | Estimated Completion Date:2019-06-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $40620 | Estimated Completion Date:2019-06-28",
                    name: "Cochrane Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cochrane Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6cb2ef06-5eb2-449f-a201-4e3b39abdfdf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $31013 | Estimated Completion Date:2018-06-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $31013 | Estimated Completion Date:2018-06-28",
                    name: "Don De Dios",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Don De Dios",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "241283d9-a612-4d2f-8b9f-97086b0a4b9e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $13833 | Estimated Completion Date:2019-06-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $13833 | Estimated Completion Date:2019-06-20",
                    name: "Drakes Way",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Drakes Way",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f261ed7e-30b5-43d2-aea9-bffdd312c5ae",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23140 | Estimated Completion Date:2017-04-12",
                    map_popup:
                        " Housing |  | Funding Awarded: $23140 | Estimated Completion Date:2017-04-12",
                    name: "Floral Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Floral Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d53a4179-16e4-4a53-8182-96874c639dc4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30793 | Estimated Completion Date:2017-08-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $30793 | Estimated Completion Date:2017-08-31",
                    name: "Fountain West",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fountain West",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9bb3998b-d359-455c-a360-b28b694f3908",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28975 | Estimated Completion Date:2017-11-14",
                    map_popup:
                        " Housing |  | Funding Awarded: $28975 | Estimated Completion Date:2017-11-14",
                    name: "Golden Oaks",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Golden Oaks",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "02df9e71-7437-4667-9138-08982c2ab628",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26098 | Estimated Completion Date:2016-09-16",
                    map_popup:
                        " Housing |  | Funding Awarded: $26098 | Estimated Completion Date:2016-09-16",
                    name: "Palm Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Palm Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "88dbf5bf-5153-409c-a046-b3365bcf27b4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16075 | Estimated Completion Date:2018-03-22",
                    map_popup:
                        " Housing |  | Funding Awarded: $16075 | Estimated Completion Date:2018-03-22",
                    name: "Point Reyes Family Homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Point Reyes Family Homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d551b97e-69d0-4a5e-923b-1c013928ff0c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $49650 | Estimated Completion Date:2017-08-24",
                    map_popup:
                        " Housing |  | Funding Awarded: $49650 | Estimated Completion Date:2017-08-24",
                    name: "Pollard Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pollard Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1b1eefb5-9111-4787-9f28-015c17881e5b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15313 | Estimated Completion Date:2016-03-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $15313 | Estimated Completion Date:2016-03-10",
                    name: "Rodeo Gateway",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Rodeo Gateway",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "01ea3fde-c50c-4592-bca6-dc83c7d35d08",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29736 | Estimated Completion Date:2016-04-21",
                    map_popup:
                        " Housing |  | Funding Awarded: $29736 | Estimated Completion Date:2016-04-21",
                    name: "San Clemente",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Clemente",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f64a2c1d-6b58-4537-bf52-cc74b490822e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12573 | Estimated Completion Date:2016-09-21",
                    map_popup:
                        " Housing |  | Funding Awarded: $12573 | Estimated Completion Date:2016-09-21",
                    name: "Silver Oak",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Silver Oak",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c749ee70-6e91-49f7-8abd-0ee42e129c10",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15428 | Estimated Completion Date:2017-06-22",
                    map_popup:
                        " Housing |  | Funding Awarded: $15428 | Estimated Completion Date:2017-06-22",
                    name: "The Oaks Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Oaks Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f9821367-12c5-4353-a423-09e7aed785fb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33600 | Estimated Completion Date:2019-06-06",
                    map_popup:
                        " Housing |  | Funding Awarded: $33600 | Estimated Completion Date:2019-06-06",
                    name: "Village Avante",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Village Avante",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bd12fcca-3fec-455f-8496-ae1f024a07f4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30493 | Estimated Completion Date:2016-08-25",
                    map_popup:
                        " Housing |  | Funding Awarded: $30493 | Estimated Completion Date:2016-08-25",
                    name: "Vista Park I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Vista Park I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "da1e718c-f2f4-4786-b753-12f92644e465",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30493 | Estimated Completion Date:2016-09-13",
                    map_popup:
                        " Housing |  | Funding Awarded: $30493 | Estimated Completion Date:2016-09-13",
                    name: "Vista Park II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Vista Park II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "24e8c4d8-8100-42a4-9730-f3f1930ce228",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27925 | Estimated Completion Date:2017-03-21",
                    map_popup:
                        " Housing |  | Funding Awarded: $27925 | Estimated Completion Date:2017-03-21",
                    name: "Avalon Senior",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Avalon Senior",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "12746bae-63dc-4eea-bef6-6a31a0a17404",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $13633 | Estimated Completion Date:2017-01-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $13633 | Estimated Completion Date:2017-01-26",
                    name: "Drasnin Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Drasnin Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5018a561-66de-4584-931e-d0cf88101211",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12175 | Estimated Completion Date:2017-02-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $12175 | Estimated Completion Date:2017-02-02",
                    name: "Effie's House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Effie's House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e88f42f9-d43a-4a66-86cd-19d23c1bc16e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $20848 | Estimated Completion Date:2017-02-09",
                    map_popup:
                        " Housing |  | Funding Awarded: $20848 | Estimated Completion Date:2017-02-09",
                    name: "Hugh Taylor House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hugh Taylor House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "062fa9c3-b4ce-45af-8ee3-184efa7a3a40",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $19865 | Estimated Completion Date:2016-12-19",
                    map_popup:
                        " Housing |  | Funding Awarded: $19865 | Estimated Completion Date:2016-12-19",
                    name: "Jack London Gateway Senior",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Jack London Gateway Senior",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b598f864-5a1f-41c4-8a11-8c07fc018325",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $11580 | Estimated Completion Date:2017-06-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $11580 | Estimated Completion Date:2017-06-01",
                    name: "Lillie Mae Jones",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lillie Mae Jones",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5e2237d4-7ffd-4806-8da9-f695752c835d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $18088 | Estimated Completion Date:2018-02-14",
                    map_popup:
                        " Housing |  | Funding Awarded: $18088 | Estimated Completion Date:2018-02-14",
                    name: "Madrone Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Madrone Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a8e82077-214d-4c8e-a9f1-ab2d0f864dbd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $13050 | Estimated Completion Date:2017-08-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $13050 | Estimated Completion Date:2017-08-02",
                    name: "Marcus Garvey",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Marcus Garvey",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6be80891-4e82-48f3-9404-f124efcba4d4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16975 | Estimated Completion Date:2017-01-25",
                    map_popup:
                        " Housing |  | Funding Awarded: $16975 | Estimated Completion Date:2017-01-25",
                    name: "Oak Park",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Oak Park",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ff9fce5f-3b2f-4031-8eba-68b2a35a2595",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26094 | Estimated Completion Date:2016-11-17",
                    map_popup:
                        " Housing |  | Funding Awarded: $26094 | Estimated Completion Date:2016-11-17",
                    name: "Prosperity Place (aka 1110 Jackson)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Prosperity Place (aka 1110 Jackson)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "85cc4ac8-a4fc-4eef-9803-6a2b6ff13383",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10853 | Estimated Completion Date:2016-04-11",
                    map_popup:
                        " Housing |  | Funding Awarded: $10853 | Estimated Completion Date:2016-04-11",
                    name: "Seven Directions",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Seven Directions",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d06f6286-b80d-443e-9b26-88877323fca3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15300 | Estimated Completion Date:2017-06-13",
                    map_popup:
                        " Housing |  | Funding Awarded: $15300 | Estimated Completion Date:2017-06-13",
                    name: "Slim Jenkins Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Slim Jenkins Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5e1eb5f2-e28b-4969-8f22-47223779abb0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10175 | Estimated Completion Date:2017-06-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $10175 | Estimated Completion Date:2017-06-01",
                    name: "Swans Market",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Swans Market",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a9c0beed-d0eb-4cfb-81dd-92385d6a0ff9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $36575 | Estimated Completion Date:2017-09-21",
                    map_popup:
                        " Housing |  | Funding Awarded: $36575 | Estimated Completion Date:2017-09-21",
                    name: "Eden Essei Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Eden Essei Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "19df3dbc-5ce5-44fd-83d4-5d4e28ba7cdf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24375 | Estimated Completion Date:2018-04-04",
                    map_popup:
                        " Housing |  | Funding Awarded: $24375 | Estimated Completion Date:2018-04-04",
                    name: "Hayward Senior",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hayward Senior",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "98fc5b35-3156-47b3-ac4b-a66f1eff402a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $31983 | Estimated Completion Date:2018-12-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $31983 | Estimated Completion Date:2018-12-28",
                    name: "Josephine Lum Lodge AB",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Josephine Lum Lodge AB",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "629215e2-8ea5-4fdb-96b4-ed22aebf9261",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29505 | Estimated Completion Date:2018-12-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $29505 | Estimated Completion Date:2018-12-28",
                    name: "Josephine Lum Lodge CD",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Josephine Lum Lodge CD",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b8764b4b-2066-4326-b3ce-2bf2cce4b2cc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33975 | Estimated Completion Date:2018-01-18",
                    map_popup:
                        " Housing |  | Funding Awarded: $33975 | Estimated Completion Date:2018-01-18",
                    name: "Sequoia Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sequoia Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3b629c13-1798-4ed0-bdef-6ad231a42e04",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25358 | Estimated Completion Date:2018-01-24",
                    map_popup:
                        " Housing |  | Funding Awarded: $25358 | Estimated Completion Date:2018-01-24",
                    name: "Warner Creek",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Warner Creek",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5ed735df-26ba-4bda-9e17-9c2ea7855c33",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10151 | Estimated Completion Date:2018-11-27",
                    map_popup:
                        " Housing |  | Funding Awarded: $10151 | Estimated Completion Date:2018-11-27",
                    name: "Wheeler Manor 650 5th",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Wheeler Manor 650 5th",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3d7e4813-f73e-49e9-a482-3d970d77840c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $35708 | Estimated Completion Date:2018-11-27",
                    map_popup:
                        " Housing |  | Funding Awarded: $35708 | Estimated Completion Date:2018-11-27",
                    name: "Wheeler Manor 651 6th",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Wheeler Manor 651 6th",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "38f7c5dd-e3fd-4474-9c9d-74e820bc40b3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $38685 | Estimated Completion Date:2017-01-24",
                    map_popup:
                        " Housing |  | Funding Awarded: $38685 | Estimated Completion Date:2017-01-24",
                    name: "Bishop Swing Community House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bishop Swing Community House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f9471969-cac9-424e-9974-779a745b2b81",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21408 | Estimated Completion Date:2017-01-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $21408 | Estimated Completion Date:2017-01-10",
                    name: "Canon Barcus Community House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Canon Barcus Community House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "60b91521-12bf-45a7-b81a-d100b1219d2d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30848 | Estimated Completion Date:2016-12-21",
                    map_popup:
                        " Housing |  | Funding Awarded: $30848 | Estimated Completion Date:2016-12-21",
                    name: "Canon Kip Community House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Canon Kip Community House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d57e63c4-43bd-4567-ad35-267510fa1d75",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26148 | Estimated Completion Date:2016-01-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $26148 | Estimated Completion Date:2016-01-28",
                    name: "Bay Avenue Senior",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bay Avenue Senior",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4767001a-64f1-4e6b-890a-172666ef80a0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29048 | Estimated Completion Date:2016-06-21",
                    map_popup:
                        " Housing |  | Funding Awarded: $29048 | Estimated Completion Date:2016-06-21",
                    name: "Betty Ann Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Betty Ann Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6175f173-ec7f-4485-b98d-43a45b479c82",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16200 | Estimated Completion Date:2016-01-06",
                    map_popup:
                        " Housing |  | Funding Awarded: $16200 | Estimated Completion Date:2016-01-06",
                    name: "Casa Feliz Studios",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Casa Feliz Studios",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "63baf1e0-27bc-4cf0-aa02-ae068367baef",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $8025 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $8025 | Estimated Completion Date:",
                    name: "Creekview Inn",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Creekview Inn",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "46e24457-e21d-4178-ac26-2ebf6a06cb05",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $53533 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $53533 | Estimated Completion Date:",
                    name: "Curtner Studios",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Curtner Studios",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cb6b7028-f8ef-4096-ae7b-c6ede6438838",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $32733 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $32733 | Estimated Completion Date:",
                    name: "El Paseo",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "El Paseo",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ced5a5a8-ad35-4658-b068-6d1e4b9d9d67",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12468 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $12468 | Estimated Completion Date:",
                    name: "Guadalupe Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Guadalupe Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6e8ba16b-1bf7-4649-a2a2-f98ff4afdd65",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33037 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $33037 | Estimated Completion Date:",
                    name: "Murphy Ranch",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Murphy Ranch",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b615cef9-5475-4af7-b98a-d00450033a61",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17330 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $17330 | Estimated Completion Date:",
                    name: "Orchard Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Orchard Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c480237a-f16b-4238-bb4f-d0f26c840b4e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10047 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $10047 | Estimated Completion Date:",
                    name: "Paula Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Paula Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "21788b6c-738d-4cdf-a20d-0882a3720c6e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15425 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $15425 | Estimated Completion Date:",
                    name: "Troy Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Troy Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "19ba168e-ef3b-48fe-876b-2f0e0812035d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $18395 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $18395 | Estimated Completion Date:",
                    name: "Villa Montgomery",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Villa Montgomery",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "23e60d78-1bfc-4eeb-8233-0d67a7785933",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26840 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $26840 | Estimated Completion Date:",
                    name: "Bay Family",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Bay Family",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d7842c80-c88c-4141-bdda-702028b985ce",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $35640 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $35640 | Estimated Completion Date:",
                    name: "La Amistad",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "La Amistad",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a68b009e-05f5-4ec4-81ac-9d605565d0d8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25850 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $25850 | Estimated Completion Date:",
                    name: "Meridian Family",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Meridian Family",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e3208b9e-6609-4af1-87ad-6efa459921ea",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $85050 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $85050 | Estimated Completion Date:",
                    name: "Perris Isle Senior",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Perris Isle Senior",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5fd97bb0-8ceb-4729-9ad3-07055d9709a4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29750 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $29750 | Estimated Completion Date:",
                    name: "Sunnyview I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sunnyview I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ac103a1b-3459-4242-bc75-9563cb9db564",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29750 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $29750 | Estimated Completion Date:",
                    name: "Sunnyview II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sunnyview II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d0356e44-cccd-4b15-9bf4-ebc7234225ce",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:",
                    name: "Maldonado Migrant Center",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Maldonado Migrant Center",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c6193267-7b80-4a2e-8eb8-9e4dad4ac53a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27840 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $27840 | Estimated Completion Date:",
                    name: "El Cortez",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "El Cortez",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cce9b448-0c0d-471e-b372-7d62d476fcb3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $58690 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $58690 | Estimated Completion Date:",
                    name: "Independent Towers (Independent Square)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Independent Towers (Independent Square)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2693492d-4500-4773-b940-48f754f54126",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $200977 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $200977 | Estimated Completion Date:",
                    name: "San Fernando Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Fernando Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "37bafd8d-a7b8-4920-a001-2f788ec4bc7a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $11925 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $11925 | Estimated Completion Date:",
                    name: "Buena Vida Family",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Buena Vida Family",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "23991c02-523e-45f5-8e3e-d0cdc2c40673",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $44963 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $44963 | Estimated Completion Date:",
                    name: "Westview",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Westview",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6817aa36-cfe9-4677-9e34-4a17a4ff8d80",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $74800 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $74800 | Estimated Completion Date:",
                    name: "Arivn FLC",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Arivn FLC",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "267132f6-3fbf-4b70-bc61-7b8b7d6b4749",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22150 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $22150 | Estimated Completion Date:",
                    name: "Baker Street",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Baker Street",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b3614d28-b4d4-47dc-a021-4c594b63dd3d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $31200 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $31200 | Estimated Completion Date:",
                    name: "Green Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Green Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a71592c0-4823-4f55-b443-ec7efa710625",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30000 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $30000 | Estimated Completion Date:",
                    name: "Homer Harrison",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Homer Harrison",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f8c87a50-924c-4236-b3bd-e35187ee6d15",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $36000 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $36000 | Estimated Completion Date:",
                    name: "Park Place Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Park Place Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "60316ce5-7fc2-4dde-8d1c-3514689afd16",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27300 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $27300 | Estimated Completion Date:",
                    name: "Parkview",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parkview",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0b30030d-62af-4695-ac67-320d9f593f1f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33000 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $33000 | Estimated Completion Date:",
                    name: "Pinewood Glen",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pinewood Glen",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6bb35a36-43f1-4efc-8939-ff94561188d0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $36900 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $36900 | Estimated Completion Date:",
                    name: "Plaza Towers Annex",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Plaza Towers Annex",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "28e3e805-3729-4785-b8ca-4ecd63de57ab",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $19200 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $19200 | Estimated Completion Date:",
                    name: "Quincy St. Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Quincy St. Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "311dbd2c-9a9c-4275-a77f-43fc72c3ee3d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $18000 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $18000 | Estimated Completion Date:",
                    name: "Residence at Old Town Kern",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Residence at Old Town Kern",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b1784ce6-ce1e-4545-ac97-a507d1a72636",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30000 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $30000 | Estimated Completion Date:",
                    name: "Residence at West Columbus",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Residence at West Columbus",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "784aed57-e41e-419d-a8f5-8b973b1b61a0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:",
                    name: "Village Park Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Village Park Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "88f0ce56-3d67-4260-9981-484f610c523e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33800 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $33800 | Estimated Completion Date:",
                    name: "Lompoc Gardens I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lompoc Gardens I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "892edc7c-d989-4a32-8f70-5e0f7e3d515c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33075 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $33075 | Estimated Completion Date:",
                    name: "Lompoc Gardens II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lompoc Gardens II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b53b1500-8335-47bd-af7b-3381d6c09c96",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:",
                    name: "Parkside Garden Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parkside Garden Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "de5dfbe8-33d9-4289-a3bb-d495659220f5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15932 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $15932 | Estimated Completion Date:",
                    name: "BEVERLY MANOR",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "BEVERLY MANOR",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3abca17d-f6ac-4e80-b3ff-72d3c38b46ed",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12286 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $12286 | Estimated Completion Date:",
                    name: "GRACE MANOR",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "GRACE MANOR",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5993264d-15dc-44be-8ee9-22579e9c151b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $8576 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $8576 | Estimated Completion Date:",
                    name: "METRO WEST APARTMENTS",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "METRO WEST APARTMENTS",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "37ce2123-31ae-48dc-a50e-f1b7e4660f59",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28273 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $28273 | Estimated Completion Date:",
                    name: "The Verona",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Verona",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f1c3b2f0-7616-4be9-86e8-bb500c410ffd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $35675 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $35675 | Estimated Completion Date:",
                    name: "180 Beamer",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "180 Beamer",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1fd4a676-99da-4d52-8cc2-ab9590bea7ba",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25660 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $25660 | Estimated Completion Date:",
                    name: "623 Vernon",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "623 Vernon",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6cf53260-64b7-4dc3-91c9-9f0230f23805",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16415 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $16415 | Estimated Completion Date:",
                    name: "Mather Veterans Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mather Veterans Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cf03008d-dc43-40db-ac74-f2f74176e57f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29320 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $29320 | Estimated Completion Date:",
                    name: "Sunset Valley Duplexes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sunset Valley Duplexes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9032e53c-fe04-4ff3-a55f-48583b45ae1c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22589 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $22589 | Estimated Completion Date:",
                    name: "Celestina Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Celestina Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "99f375c9-7a36-49e4-a2ea-8c0013aa1369",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26770 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $26770 | Estimated Completion Date:",
                    name: "Fetters Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fetters Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8d3d37ed-169f-40db-b62b-2d74e7870b12",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30443 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $30443 | Estimated Completion Date:",
                    name: "Donner Lofts",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Donner Lofts",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "72aa112a-e981-406b-b8b3-4a22cb80ce03",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28833 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $28833 | Estimated Completion Date:",
                    name: "Foster Square",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Foster Square",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bb53f608-f7a3-485a-8c0a-346a73eb64cf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23400 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $23400 | Estimated Completion Date:",
                    name: "6800 Mission",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "6800 Mission",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9b663904-71cc-42e5-b739-9743d3ef93ec",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23572 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $23572 | Estimated Completion Date:",
                    name: "Onizuka Crossing",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Onizuka Crossing",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "03df0cdd-1e0b-42ff-9fbf-51d735a1a17c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $39794 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $39794 | Estimated Completion Date:",
                    name: "Sequoia Belle Haven",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sequoia Belle Haven",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "be7e7300-1037-4e45-9a6d-2d98a7ad1b19",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30035 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $30035 | Estimated Completion Date:",
                    name: "Lemon Hill Townhomes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lemon Hill Townhomes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e7dd4969-21c5-40c1-a5a6-32d36130c61c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $43085 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $43085 | Estimated Completion Date:",
                    name: "Mutual Housing at Foothill Farms",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mutual Housing at Foothill Farms",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bd939c16-8609-44d3-977e-2da70835bc07",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $20625 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $20625 | Estimated Completion Date:",
                    name: "Arroyo Grande Villas",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Arroyo Grande Villas",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3eec59ab-0d74-4789-92c4-805a265ae781",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23925 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $23925 | Estimated Completion Date:",
                    name: "Magnolia Park Townhomes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Magnolia Park Townhomes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e5748741-cbce-42da-aadd-a6b14ab74d62",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $63700 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $63700 | Estimated Completion Date:",
                    name: "Napa Park Homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Napa Park Homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c1fa78c5-8f17-4a97-8209-b5da94599d5d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30955 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $30955 | Estimated Completion Date:",
                    name: "Oak Creek Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Oak Creek Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bf299091-e1eb-45d5-a408-c55b0b84ef02",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23875 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $23875 | Estimated Completion Date:",
                    name: "Pecan Court Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pecan Court Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6a5d85df-d0f2-4f94-8be0-f4676ff6dc6a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $64350 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $64350 | Estimated Completion Date:",
                    name: "The Reserve of Napa",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Reserve of Napa",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6b55402d-c558-4aca-b731-bf8ad7aaa99e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15600 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $15600 | Estimated Completion Date:",
                    name: "Villa de Adobe Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Villa de Adobe Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e56226b4-0498-40f2-ae99-9c60ba4fb797",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33672 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $33672 | Estimated Completion Date:",
                    name: "The Woodlands Apartments II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Woodlands Apartments II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0203cc44-0cbb-4a12-bf79-fc04aa78ba2d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10800 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $10800 | Estimated Completion Date:",
                    name: "Atascadero Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Atascadero Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "31a295b9-e408-44e9-a725-0c29b1c939fe",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $7200 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $7200 | Estimated Completion Date:",
                    name: "Belridge Street Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Belridge Street Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4e98a280-bc01-44bb-8f53-eb1c17978124",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $14750 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $14750 | Estimated Completion Date:",
                    name: "Brizzolara Street",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Brizzolara Street",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "275d897c-a2e0-47d7-bee7-0c917b743fd0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30600 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $30600 | Estimated Completion Date:",
                    name: "Canyon Creek Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Canyon Creek Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c86b601c-6f19-407a-947e-190f448170d9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $94500 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $94500 | Estimated Completion Date:",
                    name: "Casa de los Carneros",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Casa de los Carneros",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "79b9b8d5-4bc9-4bd6-8c8a-1ac956e4ff85",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $47945 | Estimated Completion Date:",
                    map_popup:
                        " Housing |  | Funding Awarded: $47945 | Estimated Completion Date:",
                    name: "Casas de las Flores",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Casas de las Flores",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "87d7399e-3f96-4779-9f20-713802e9a9cf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16800 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $16800 | Estimated Completion Date:2017-08-30",
                    name: "Cawelti Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cawelti Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1524e813-07e8-4bad-81f3-8fe951a85915",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16800 | Estimated Completion Date:2019-09-07",
                    map_popup:
                        " Housing |  | Funding Awarded: $16800 | Estimated Completion Date:2019-09-07",
                    name: "Chapel Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Chapel Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6e0347c7-d5aa-4177-8cf0-466d310205f7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21000 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $21000 | Estimated Completion Date:2017-08-30",
                    name: "College Park",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "College Park",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "77ee7fc7-17e6-4c54-b5c3-be6a498cd12c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21600 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $21600 | Estimated Completion Date:2017-08-30",
                    name: "Courtland Street Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Courtland Street Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e56e427e-075e-4858-97dc-30c0fbaf9775",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:2018-07-11",
                    map_popup:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:2018-07-11",
                    name: "Creston Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Creston Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "44d1e5e2-6666-4984-b83b-e1ab346f5aff",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $52250 | Estimated Completion Date:2018-12-19",
                    map_popup:
                        " Housing |  | Funding Awarded: $52250 | Estimated Completion Date:2018-12-19",
                    name: "Dahlia Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Dahlia Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e6fa511c-2234-4a74-8914-3ae7ef41666c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $31350 | Estimated Completion Date:2018-11-05",
                    map_popup:
                        " Housing |  | Funding Awarded: $31350 | Estimated Completion Date:2018-11-05",
                    name: "Dahlia Court II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Dahlia Court II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4f72d38c-0395-49fd-87f9-43a86d01c25f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $14750 | Estimated Completion Date:2024-07-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $14750 | Estimated Completion Date:2024-07-10",
                    name: "Ellwood",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ellwood",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1d7c7541-30a9-4aa5-a56d-f62c486f8c0f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30800 | Estimated Completion Date:2018-11-05",
                    map_popup:
                        " Housing |  | Funding Awarded: $30800 | Estimated Completion Date:2018-11-05",
                    name: "Isle Vista Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Isle Vista Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bfc18793-b366-42e0-b35b-8e58206138df",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $47000 | Estimated Completion Date:2023-04-17",
                    map_popup:
                        " Housing |  | Funding Awarded: $47000 | Estimated Completion Date:2023-04-17",
                    name: "Jardin de las Rosas",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Jardin de las Rosas",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "760e3238-eb47-4caf-bdf2-399a9ec7850a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $9600 | Estimated Completion Date:2019-02-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $9600 | Estimated Completion Date:2019-02-01",
                    name: "La Brisa Marina",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "La Brisa Marina",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6bd1cd34-6be9-4afe-a8ff-aaebf31e8324",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17400 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $17400 | Estimated Completion Date:2017-08-30",
                    name: "Lachen Tara",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lachen Tara",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e9fc838b-84d0-41a6-9124-d9d415eab297",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28050 | Estimated Completion Date:2018-11-05",
                    map_popup:
                        " Housing |  | Funding Awarded: $28050 | Estimated Completion Date:2018-11-05",
                    name: "Ladera Street Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ladera Street Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "246c348e-8926-4ae6-a340-5592791bf7f2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $29250 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $29250 | Estimated Completion Date:2017-08-30",
                    name: "Los Adobes de Maria I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Los Adobes de Maria I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "25d741c1-6f07-4b0b-92b1-d4c0fd097cd3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24000 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $24000 | Estimated Completion Date:2017-08-30",
                    name: "Los Robles Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Los Robles Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a1d64d7f-b698-4a58-a0c1-8a3eaf909f7f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $76000 | Estimated Completion Date:2017-10-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $76000 | Estimated Completion Date:2017-10-26",
                    name: "Mariposa Town Homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mariposa Town Homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "25520874-5f95-4514-ad1e-651f539742dd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12000 | Estimated Completion Date:2018-12-19",
                    map_popup:
                        " Housing |  | Funding Awarded: $12000 | Estimated Completion Date:2018-12-19",
                    name: "Oak Forest Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Oak Forest Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6b293db2-062e-4674-8a34-c0c0eb8adaa3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $12600 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $12600 | Estimated Completion Date:2017-08-30",
                    name: "Oceanside Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Oceanside Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "77bfd847-0339-48b2-ac0d-1edb7c5bf12a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15600 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $15600 | Estimated Completion Date:2017-08-30",
                    name: "Pacific View Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pacific View Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "23d52545-7f29-4403-919b-b56c0ccf1a55",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $18410 | Estimated Completion Date:2023-04-17",
                    map_popup:
                        " Housing |  | Funding Awarded: $18410 | Estimated Completion Date:2023-04-17",
                    name: "Pismo Creek Bungalows",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pismo Creek Bungalows",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "762fefe5-432c-4495-86b0-6a5bcb3a20ab",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $36000 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $36000 | Estimated Completion Date:2017-08-30",
                    name: "River View Townhomes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "River View Townhomes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2bca25ff-5fb6-48ef-94a5-a9c31c02da8d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $49025 | Estimated Completion Date:2019-10-24",
                    map_popup:
                        " Housing |  | Funding Awarded: $49025 | Estimated Completion Date:2019-10-24",
                    name: "Rolling Hills Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Rolling Hills Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7d44f901-3dde-4bcd-b081-d062f3a8db1c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $48000 | Estimated Completion Date:2023-04-17",
                    map_popup:
                        " Housing |  | Funding Awarded: $48000 | Estimated Completion Date:2023-04-17",
                    name: "Rolling Hills II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Rolling Hills II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c66eac1c-8924-426c-a120-3735b4a762c5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17400 | Estimated Completion Date:2019-07-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $17400 | Estimated Completion Date:2019-07-26",
                    name: "Sea Breeze Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sea Breeze Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3482f22b-ba5c-4ec1-be96-741cfdeaf449",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $7200 | Estimated Completion Date:2019-04-09",
                    map_popup:
                        " Housing |  | Funding Awarded: $7200 | Estimated Completion Date:2019-04-09",
                    name: "Sea Haven Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sea Haven Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "03fec1db-b510-4109-a4a4-0b1b8d6a9fef",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $7200 | Estimated Completion Date:2019-02-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $7200 | Estimated Completion Date:2019-02-01",
                    name: "Sequoia Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sequoia Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bedb45f4-2c45-4d5e-9f0f-31cdb067716f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27180 | Estimated Completion Date:2018-12-19",
                    map_popup:
                        " Housing |  | Funding Awarded: $27180 | Estimated Completion Date:2018-12-19",
                    name: "Storke Ranch Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Storke Ranch Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a0c7dc3a-9563-428d-ad13-bea6b7a17b71",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17400 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $17400 | Estimated Completion Date:2017-08-30",
                    name: "Templeton Place",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Templeton Place",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "886fa38a-a415-46be-987b-fc495f16d391",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $40140 | Estimated Completion Date:2023-04-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $40140 | Estimated Completion Date:2023-04-01",
                    name: "Templeton Place",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Templeton Place",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "41e90788-b540-4b9d-b468-a0e6f342cca1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16800 | Estimated Completion Date:2017-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $16800 | Estimated Completion Date:2017-08-30",
                    name: "The Villas at Higuera",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Villas at Higuera",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "35f3837a-93bf-49ef-9e97-fe922b358982",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21000 | Estimated Completion Date:2018-12-19",
                    map_popup:
                        " Housing |  | Funding Awarded: $21000 | Estimated Completion Date:2018-12-19",
                    name: "Valentine Court I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Valentine Court I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dfde705d-f593-49f4-a7d3-9087caaf0393",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $10800 | Estimated Completion Date:2019-05-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $10800 | Estimated Completion Date:2019-05-10",
                    name: "Valentine Court II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Valentine Court II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ab1d0ba6-355b-4a3a-9b67-ab650e0b0406",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $5400 | Estimated Completion Date:2019-05-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $5400 | Estimated Completion Date:2019-05-10",
                    name: "Valentine Court III",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Valentine Court III",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8d8a9bfe-18b3-4d63-b151-d74ef9b7ad2e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15200 | Estimated Completion Date:2018-06-07",
                    map_popup:
                        " Housing |  | Funding Awarded: $15200 | Estimated Completion Date:2018-06-07",
                    name: "Victoria Street Bungalows",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Victoria Street Bungalows",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8f4e9cf4-caa8-40f0-b54d-d29ce6e1b653",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $53950 | Estimated Completion Date:2018-12-19",
                    map_popup:
                        " Housing |  | Funding Awarded: $53950 | Estimated Completion Date:2018-12-19",
                    name: "Villa La Esperanza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Villa La Esperanza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "95ccd623-6c34-4abe-b863-8480e2cab0df",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23696 | Estimated Completion Date:2024-04-12",
                    map_popup:
                        " Housing |  | Funding Awarded: $23696 | Estimated Completion Date:2024-04-12",
                    name: "575 Vallejo St Senior Apartments Residential Broadband",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "575 Vallejo St Senior Apartments Residential Broadband",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4e032dc8-a4c7-44bc-b0bc-623ff2967cde",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $18103 | Estimated Completion Date:2024-03-29",
                    map_popup:
                        " Housing |  | Funding Awarded: $18103 | Estimated Completion Date:2024-03-29",
                    name: "579 Vallejo St Senior Apartments Residential Broadband",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "579 Vallejo St Senior Apartments Residential Broadband",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "944452ad-035a-4eec-b35a-53ca0a4885ac",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $20619 | Estimated Completion Date:2016-01-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $20619 | Estimated Completion Date:2016-01-28",
                    name: "Casa Grande",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Casa Grande",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "13eb9d46-9c0b-442c-b363-7a0802d60209",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $9661 | Estimated Completion Date:2016-01-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $9661 | Estimated Completion Date:2016-01-28",
                    name: "Caulfield Lane",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Caulfield Lane",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5d398df0-5634-4a96-824a-14f63563d036",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17128 | Estimated Completion Date:2024-04-12",
                    map_popup:
                        " Housing |  | Funding Awarded: $17128 | Estimated Completion Date:2024-04-12",
                    name: "Don Bennet Senior Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Don Bennet Senior Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ba3885bc-49d2-4a79-802f-9b4b95f9a42e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17280 | Estimated Completion Date:2023-12-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $17280 | Estimated Completion Date:2023-12-01",
                    name: "Linda Tunis Senior Apartments Residential Broadband",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Linda Tunis Senior Apartments Residential Broadband",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f22ed7c2-4b06-4be4-8fe8-f5f1beeba099",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $6492 | Estimated Completion Date:2015-06-24",
                    map_popup:
                        " Housing |  | Funding Awarded: $6492 | Estimated Completion Date:2015-06-24",
                    name: "10 Toussin",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "10 Toussin",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5226a1cd-ccff-46b5-8218-71a6a37afc48",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $9300 | Estimated Completion Date:2015-06-23",
                    map_popup:
                        " Housing |  | Funding Awarded: $9300 | Estimated Completion Date:2015-06-23",
                    name: "167 Edith",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "167 Edith",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ad3e2177-4e9b-4a2b-b6d8-722c1c021cdb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $9197 | Estimated Completion Date:2015-06-23",
                    map_popup:
                        " Housing |  | Funding Awarded: $9197 | Estimated Completion Date:2015-06-23",
                    name: "210 Douglas",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "210 Douglas",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c952981e-0dd6-4647-955a-24ed9ff2e862",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $14566 | Estimated Completion Date:2015-06-22",
                    map_popup:
                        " Housing |  | Funding Awarded: $14566 | Estimated Completion Date:2015-06-22",
                    name: "575 Vallejo",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "575 Vallejo",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1d79175a-09f2-4c27-9282-db63eff8fdb9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $11419 | Estimated Completion Date:2015-06-23",
                    map_popup:
                        " Housing |  | Funding Awarded: $11419 | Estimated Completion Date:2015-06-23",
                    name: "579 Vallejo",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "579 Vallejo",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "58781514-810e-4df5-a60d-f6db550a9244",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $80580 | Estimated Completion Date:2023-09-08",
                    map_popup:
                        " Housing |  | Funding Awarded: $80580 | Estimated Completion Date:2023-09-08",
                    name: "Sango Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sango Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8d0590dd-c6cf-4f02-a52e-1ffd830ce923",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25152 | Estimated Completion Date:2019-02-25",
                    map_popup:
                        " Housing |  | Funding Awarded: $25152 | Estimated Completion Date:2019-02-25",
                    name: "Friendship Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Friendship Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2f454ef6-7e60-4d74-afe8-088dbab0f2b3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $41520 | Estimated Completion Date:2019-02-25",
                    map_popup:
                        " Housing |  | Funding Awarded: $41520 | Estimated Completion Date:2019-02-25",
                    name: "Nevin Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Nevin Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "887b3790-41c7-4b9e-96a7-c0b34efa8198",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $43080 | Estimated Completion Date:2019-02-25",
                    map_popup:
                        " Housing |  | Funding Awarded: $43080 | Estimated Completion Date:2019-02-25",
                    name: "Triangle Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Triangle Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ffe14e60-c851-40fd-96dc-4d9127014ba7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $39601 | Estimated Completion Date:2018-06-04",
                    map_popup:
                        " Housing |  | Funding Awarded: $39601 | Estimated Completion Date:2018-06-04",
                    name: "Hunters Point East",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hunters Point East",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "22196c1c-c232-4b27-b433-33919e901b2b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $36967 | Estimated Completion Date:2018-03-23",
                    map_popup:
                        " Housing |  | Funding Awarded: $36967 | Estimated Completion Date:2018-03-23",
                    name: "Hunters Point West",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hunters Point West",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d453876b-0188-4fc5-9a60-75246c434eef",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $66941 | Estimated Completion Date:2019-08-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $66941 | Estimated Completion Date:2019-08-30",
                    name: "Westbrook Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Westbrook Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2e7f123d-27b8-48d3-8ca3-c8912af34d79",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23734 | Estimated Completion Date:2017-03-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $23734 | Estimated Completion Date:2017-03-02",
                    name: "Lakeside Senior Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lakeside Senior Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e56db556-1ce8-441c-aa3d-3593d7c1203a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16537 | Estimated Completion Date:2017-05-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $16537 | Estimated Completion Date:2017-05-28",
                    name: "Lawrence Moore",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lawrence Moore",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5dda0e60-df22-4116-a683-b1adb045b46f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15457 | Estimated Completion Date:2017-03-04",
                    map_popup:
                        " Housing |  | Funding Awarded: $15457 | Estimated Completion Date:2017-03-04",
                    name: "Linda Glen",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Linda Glen",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2a3277ed-219f-47fd-9465-e6c94b8fbee4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16844 | Estimated Completion Date:2017-04-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $16844 | Estimated Completion Date:2017-04-30",
                    name: "Sacramento Senior Homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sacramento Senior Homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "eb2c38c1-097c-493f-932d-b00a2e7c087f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $55970 | Estimated Completion Date:2023-11-21",
                    map_popup:
                        " Housing |  | Funding Awarded: $55970 | Estimated Completion Date:2023-11-21",
                    name: "Satellite St. Andrew's Manor, LLC",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Satellite St. Andrew's Manor, LLC",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "604ff21a-a891-4533-937a-bf267ddc0b8d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $20293 | Estimated Completion Date:2016-10-14",
                    map_popup:
                        " Housing |  | Funding Awarded: $20293 | Estimated Completion Date:2016-10-14",
                    name: "Amistad House",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Amistad House",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5d1bfed8-69c1-4e59-a7eb-fae718f22bb6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17920 | Estimated Completion Date:2017-06-09",
                    map_popup:
                        " Housing |  | Funding Awarded: $17920 | Estimated Completion Date:2017-06-09",
                    name: "Beth Asher",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Beth Asher",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "00a72cc6-15b5-44d1-bd0e-48d3ed45baca",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33339 | Estimated Completion Date:2016-10-14",
                    map_popup:
                        " Housing |  | Funding Awarded: $33339 | Estimated Completion Date:2016-10-14",
                    name: "Satellite Central",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Satellite Central",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e8bd51a7-1fd5-41d4-82ca-a1037e153699",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $16582 | Estimated Completion Date:2017-05-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $16582 | Estimated Completion Date:2017-05-30",
                    name: "Stuart Pratt",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Stuart Pratt",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "09b5f9aa-b25c-4293-adf2-8b85ca5fdc9f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26394 | Estimated Completion Date:2016-08-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $26394 | Estimated Completion Date:2016-08-31",
                    name: "Valdez Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Valdez Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3a54941e-e79d-4cb2-bc1b-fac9f49f22ab",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $33000 | Estimated Completion Date:2023-04-11",
                    map_popup:
                        " Housing |  | Funding Awarded: $33000 | Estimated Completion Date:2023-04-11",
                    name: "Annadale Commons",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Annadale Commons",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5478b008-8002-46be-87fb-4635f635f8b9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26600 | Estimated Completion Date:2016-04-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $26600 | Estimated Completion Date:2016-04-20",
                    name: "CALIENTE CREEK PARTNERS",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "CALIENTE CREEK PARTNERS",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e5604610-f0b6-4947-859c-e0ad8c5793d7",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22800 | Estimated Completion Date:2016-04-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $22800 | Estimated Completion Date:2016-04-20",
                    name: "Cottonwood Creek",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cottonwood Creek",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bded37ea-ae02-4eb2-bbac-9b9f730f7f57",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:2018-05-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:2018-05-02",
                    name: "Gateway Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Gateway Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0d3e645f-ea66-4e10-b16e-222e54c1827f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25200 | Estimated Completion Date:2018-05-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $25200 | Estimated Completion Date:2018-05-02",
                    name: "Goshen Village II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Goshen Village II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dae0d62e-6657-4dac-a2f7-d995b1a2dbf3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $31200 | Estimated Completion Date:2016-05-05",
                    map_popup:
                        " Housing |  | Funding Awarded: $31200 | Estimated Completion Date:2016-05-05",
                    name: "NORTH PARK APARTMENTS HOUSING CORPORATION",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "NORTH PARK APARTMENTS HOUSING CORPORATION",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1b2b6053-a058-4689-929a-b41c227181a5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $128000 | Estimated Completion Date:2024-01-12",
                    map_popup:
                        " Housing |  | Funding Awarded: $128000 | Estimated Completion Date:2024-01-12",
                    name: "Nupchi Xo\u2019oy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Nupchi Xo\u2019oy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0dd2fe97-aade-4958-8147-1fa5f2c5d205",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:2018-05-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:2018-05-02",
                    name: "Parksdale Village II",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parksdale Village II",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6c07a9d6-da61-48d4-a80f-8750abf3a58b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $35200 | Estimated Completion Date:2017-04-13",
                    map_popup:
                        " Housing |  | Funding Awarded: $35200 | Estimated Completion Date:2017-04-13",
                    name: "RANCHO LINDO PARTNERS",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "RANCHO LINDO PARTNERS",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "cb835cdb-1414-4270-9746-cc755287110a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28600 | Estimated Completion Date:2017-04-13",
                    map_popup:
                        " Housing |  | Funding Awarded: $28600 | Estimated Completion Date:2017-04-13",
                    name: "ROLLING HILLS PARTNERS",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "ROLLING HILLS PARTNERS",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4c21441a-a2f9-4fcd-a2ce-03a98bc25cd0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:2018-05-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:2018-05-02",
                    name: "Sand Creek",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sand Creek",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e67368b0-a28f-4d87-8142-6048a8a216ba",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $68900 | Estimated Completion Date:2023-11-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $68900 | Estimated Completion Date:2023-11-01",
                    name: "Sugar Pine Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sugar Pine Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6c3b7be2-8403-46e5-be5f-519186e0a0ca",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $26400 | Estimated Completion Date:2016-04-19",
                    map_popup:
                        " Housing |  | Funding Awarded: $26400 | Estimated Completion Date:2016-04-19",
                    name: "SUNRISE VILLA PARTNERS",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "SUNRISE VILLA PARTNERS",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4beb37fa-cabd-4a90-b9c3-50f3d2d4149d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:2016-04-22",
                    map_popup:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:2016-04-22",
                    name: "Villa Del Rey",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Villa Del Rey",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "62629a92-32da-43dd-be4d-55557f515b18",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24000 | Estimated Completion Date:2016-04-22",
                    map_popup:
                        " Housing |  | Funding Awarded: $24000 | Estimated Completion Date:2016-04-22",
                    name: "VILLA HERMOSA PARTNERS",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "VILLA HERMOSA PARTNERS",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7f88f8c6-4d0a-40ec-9651-5fc47aa412f5",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:2018-05-02",
                    map_popup:
                        " Housing |  | Funding Awarded: $28800 | Estimated Completion Date:2018-05-02",
                    name: "Viscaya Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Viscaya Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c3be6b2f-3f33-45e6-a7cf-f001d508bdfd",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $25960 | Estimated Completion Date:2018-11-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $25960 | Estimated Completion Date:2018-11-26",
                    name: "Inyo Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Inyo Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "449d7515-8afc-433f-8ddb-05961ac9b221",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $14866 | Estimated Completion Date:2018-11-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $14866 | Estimated Completion Date:2018-11-26",
                    name: "Pacific Gardens",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pacific Gardens",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6c512e0f-0794-4a28-b0b0-db21953e3ae6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $43560 | Estimated Completion Date:2016-04-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $43560 | Estimated Completion Date:2016-04-01",
                    name: "Parc Grove Northwest",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parc Grove Northwest",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0b1ad269-3a8c-4d93-ae4c-7e5f628d1843",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15114 | Estimated Completion Date:2021-02-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $15114 | Estimated Completion Date:2021-02-28",
                    name: "Yosemite Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Yosemite Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "73343946-a442-474a-b0ee-5d3b4ce1a344",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $6373 | Estimated Completion Date:2020-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $6373 | Estimated Completion Date:2020-07-31",
                    name: "Charles Cobb Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Charles Cobb Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "07356e06-c296-4626-84aa-ee3b8c5ce22e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $13612 | Estimated Completion Date:2020-07-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $13612 | Estimated Completion Date:2020-07-31",
                    name: "New Genesis Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "New Genesis Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c31aa594-c398-4bde-b8f9-4f2c442221a1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $113400 | Estimated Completion Date:2024-01-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $113400 | Estimated Completion Date:2024-01-20",
                    name: "Aparicio Apartments I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Aparicio Apartments I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "06ebf358-eb96-4673-8a16-bd3b5a1db37e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $61040 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $61040 | Estimated Completion Date:2018-01-31",
                    name: "Central Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Central Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "06d70b2b-1673-4218-87b7-5603a00cb98d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $22386 | Estimated Completion Date:2017-12-27",
                    map_popup:
                        " Housing |  | Funding Awarded: $22386 | Estimated Completion Date:2017-12-27",
                    name: "Creekside Village",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Creekside Village",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "772c3c4e-dc61-4069-8740-0383d7ab34aa",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:2018-01-31",
                    name: "Cypress Court",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cypress Court",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6af4a41f-e870-4c5d-8526-10d6da5d4b14",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $83850 | Estimated Completion Date:2023-04-20",
                    map_popup:
                        " Housing |  | Funding Awarded: $83850 | Estimated Completion Date:2023-04-20",
                    name: "Homebase on G",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Homebase on G",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "89059e7e-0cc5-4806-9e89-3e6605710abe",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15600 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $15600 | Estimated Completion Date:2018-01-31",
                    name: "Leland Park",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Leland Park",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "4291a2bf-451e-4c94-927e-144b89242149",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $126000 | Estimated Completion Date:2023-08-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $126000 | Estimated Completion Date:2023-08-01",
                    name: "Lompoc Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Lompoc Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a7cb94be-e8e7-4ec1-bcce-dc375f4d8230",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15210 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $15210 | Estimated Completion Date:2018-01-31",
                    name: "Parkview Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Parkview Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0bfb2ccd-79f8-442c-bbbd-94c0e7f7a2bb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $19173 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $19173 | Estimated Completion Date:2018-01-31",
                    name: "Pescadero Lofts",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pescadero Lofts",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f140e1f7-4532-46dd-b8e1-9906effa76dc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27730 | Estimated Completion Date:2017-12-27",
                    map_popup:
                        " Housing |  | Funding Awarded: $27730 | Estimated Completion Date:2017-12-27",
                    name: "Rancho Hermosa",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Rancho Hermosa",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "687fad66-0ecc-405e-8bd2-5e0704275098",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21600 | Estimated Completion Date:2018-01-31",
                    map_popup:
                        " Housing |  | Funding Awarded: $21600 | Estimated Completion Date:2018-01-31",
                    name: "Santa Rita Village I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Santa Rita Village I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8757eac6-19a1-45da-b7f9-d1a2cdcaf14f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $139700 | Estimated Completion Date:2023-08-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $139700 | Estimated Completion Date:2023-08-01",
                    name: "Stanley Horn Homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Stanley Horn Homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "129c31c6-89fb-402d-b8c9-441c54ecf23c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $24299 | Estimated Completion Date:2016-12-14",
                    map_popup:
                        " Housing |  | Funding Awarded: $24299 | Estimated Completion Date:2016-12-14",
                    name: "Kristen Court Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Kristen Court Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "eee35664-21bd-4434-b44b-9f2e26ac9818",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $4462 | Estimated Completion Date:2015-09-18",
                    map_popup:
                        " Housing |  | Funding Awarded: $4462 | Estimated Completion Date:2015-09-18",
                    name: "The Stanford Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "The Stanford Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "44a54920-e02e-4f12-bea2-f5adf74422f1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $35215 | Estimated Completion Date:2017-11-17",
                    map_popup:
                        " Housing |  | Funding Awarded: $35215 | Estimated Completion Date:2017-11-17",
                    name: "430 Turk",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "430 Turk",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "d58c6fc7-9a7a-45d5-9692-8007b538305f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $15037 | Estimated Completion Date:2017-12-11",
                    map_popup:
                        " Housing |  | Funding Awarded: $15037 | Estimated Completion Date:2017-12-11",
                    name: "951 Eddy",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "951 Eddy",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "16ab8c89-bf4e-4c10-b052-585c94f8bbe0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23972 | Estimated Completion Date:2017-12-08",
                    map_popup:
                        " Housing |  | Funding Awarded: $23972 | Estimated Completion Date:2017-12-08",
                    name: "Aarti Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Aarti Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8345df37-5d8f-4a48-af6d-1a67cecc13db",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $53673 | Estimated Completion Date:2017-12-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $53673 | Estimated Completion Date:2017-12-15",
                    name: "Alexander Residence",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Alexander Residence",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3dd9aea6-0b3c-4ab9-8c0c-77df7b895747",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $39726 | Estimated Completion Date:2017-12-04",
                    map_popup:
                        " Housing |  | Funding Awarded: $39726 | Estimated Completion Date:2017-12-04",
                    name: "Antonia Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Antonia Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3f590810-0d80-4568-a9ff-201cabc938f3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $23640 | Estimated Completion Date:2017-12-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $23640 | Estimated Completion Date:2017-12-01",
                    name: "Buena Vista Terrace",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Buena Vista Terrace",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9640fa9b-0a56-45fe-a03a-e3e93b95a1a1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $63472 | Estimated Completion Date:2018-02-23",
                    map_popup:
                        " Housing |  | Funding Awarded: $63472 | Estimated Completion Date:2018-02-23",
                    name: "Civic Center Residence",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Civic Center Residence",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fe234f43-f6c2-4d4d-85e6-a36cdc4a6a25",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $45547 | Estimated Completion Date:2017-06-26",
                    map_popup:
                        " Housing |  | Funding Awarded: $45547 | Estimated Completion Date:2017-06-26",
                    name: "Dalt Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Dalt Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "628fc336-8d5b-46d2-82a2-5b96d7f7e40c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $32795 | Estimated Completion Date:2017-12-15",
                    map_popup:
                        " Housing |  | Funding Awarded: $32795 | Estimated Completion Date:2017-12-15",
                    name: "Maria Manor",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Maria Manor",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "e7a2b78b-ef43-449a-bca6-c594a9194ed2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $14220 | Estimated Completion Date:2017-09-22",
                    map_popup:
                        " Housing |  | Funding Awarded: $14220 | Estimated Completion Date:2017-09-22",
                    name: "Mosaica (Senior)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Mosaica (Senior)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "56e1939a-9ff2-45a1-b720-659bcd65d6c8",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $30252 | Estimated Completion Date:2017-06-01",
                    map_popup:
                        " Housing |  | Funding Awarded: $30252 | Estimated Completion Date:2017-06-01",
                    name: "Ritz Hotel",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Ritz Hotel",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f05daa8a-7eec-4603-8c01-de57a09af5c2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27767 | Estimated Completion Date:2017-06-29",
                    map_popup:
                        " Housing |  | Funding Awarded: $27767 | Estimated Completion Date:2017-06-29",
                    name: "SOMA Family Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "SOMA Family Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3b9735d9-aa18-42f2-984b-383dbee450fb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $31344 | Estimated Completion Date:2017-06-30",
                    map_popup:
                        " Housing |  | Funding Awarded: $31344 | Estimated Completion Date:2017-06-30",
                    name: "SOMA Studios",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "SOMA Studios",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "67bf9ef4-80b0-4d73-b903-114ee59c3428",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $45900 | Estimated Completion Date:2018-08-23",
                    map_popup:
                        " Housing |  | Funding Awarded: $45900 | Estimated Completion Date:2018-08-23",
                    name: "Banneker Homes",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Banneker Homes",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8e4b5317-f9be-4ba6-a0bc-e70e9bc7ac4c",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $17288 | Estimated Completion Date:2018-04-03",
                    map_popup:
                        " Housing |  | Funding Awarded: $17288 | Estimated Completion Date:2018-04-03",
                    name: "Delta Plaza",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Delta Plaza",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5fe32b8b-9ec5-4625-b2c8-736c1fd4b801",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $5750 | Estimated Completion Date:2018-04-03",
                    map_popup:
                        " Housing |  | Funding Awarded: $5750 | Estimated Completion Date:2018-04-03",
                    name: "Dewey Apartments",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Dewey Apartments",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ddbf183d-58f5-4b4b-bd00-386ab959f327",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $21600 | Estimated Completion Date:2018-05-11",
                    map_popup:
                        " Housing |  | Funding Awarded: $21600 | Estimated Completion Date:2018-05-11",
                    name: "Diamond Cove Townhomes I-A",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Diamond Cove Townhomes I-A",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "58d0f9ad-e47f-402f-a737-3432df725180",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $14360 | Estimated Completion Date:2018-06-04",
                    map_popup:
                        " Housing |  | Funding Awarded: $14360 | Estimated Completion Date:2018-06-04",
                    name: "Diamond Cove Townhomes I-B",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Diamond Cove Townhomes I-B",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dc626c52-066d-4085-b7e2-fb657db27056",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $11675 | Estimated Completion Date:2018-04-03",
                    map_popup:
                        " Housing |  | Funding Awarded: $11675 | Estimated Completion Date:2018-04-03",
                    name: "Villa Isabella",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Villa Isabella",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "139b43cc-76a9-4347-b937-f13777aa035a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:2018-11-28",
                    map_popup:
                        " Housing |  | Funding Awarded: $27000 | Estimated Completion Date:2018-11-28",
                    name: "Villa Monterey",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Villa Monterey",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "71b0bb16-3431-4570-b841-06b32297001f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $43200 | Estimated Completion Date:2018-08-10",
                    map_popup:
                        " Housing |  | Funding Awarded: $43200 | Estimated Completion Date:2018-08-10",
                    name: "Whispering Pines",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Whispering Pines",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6d01b231-8570-4f65-9b6b-7877fd70a5f9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $20850 | Estimated Completion Date:2016-01-13",
                    map_popup:
                        " Housing |  | Funding Awarded: $20850 | Estimated Completion Date:2016-01-13",
                    name: "Washington Courtyards",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Washington Courtyards",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "9c6b0c89-1cc3-4132-85e5-e44c30de53bf",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        " Housing |  | Funding Awarded: $32113 | Estimated Completion Date:2016-01-12",
                    map_popup:
                        " Housing |  | Funding Awarded: $32113 | Estimated Completion Date:2016-01-12",
                    name: "West Capitol",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "West Capitol",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1c7e0810-33e0-4334-9ab8-1bed65105d95",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2021-11-23",
                    map_popup:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2021-11-23",
                    name: "Project 1: Technical Feasibility Study for Broadband Deployment on the Rancheria",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 1: Technical Feasibility Study for Broadband Deployment on the Rancheria",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ad1b1a4c-e233-4a97-96db-5c5e61cf7793",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2021-11-23",
                    map_popup:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2021-11-23",
                    name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships on the Rancheria",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships on the Rancheria",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "17790e3a-a026-40c9-889d-816066fca6d0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2021-11-23",
                    map_popup:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2021-11-23",
                    name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development on \nthe Rancheria",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development on \nthe Rancheria",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "561af9f9-4dfd-4410-9036-188da5345011",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $98000 | Estimated Completion Date:2021-02-23",
                    map_popup:
                        "  |  | Funding Awarded: $98000 | Estimated Completion Date:2021-02-23",
                    name: "Working with Communities for Sustainable Broadband",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Working with Communities for Sustainable Broadband",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "fc69c374-2219-481e-b196-86f08e716431",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2021-05-23",
                    map_popup:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2021-05-23",
                    name: "Project 1: Technical Feasibility Study for Broadband Deployment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 1: Technical Feasibility Study for Broadband Deployment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "33cdf651-52e1-4371-9c7e-23c1dbe7f43a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2021-05-23",
                    map_popup:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2021-05-23",
                    name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "56d82280-c025-4b10-a0ec-9673df993c92",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2021-05-23",
                    map_popup:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2021-05-23",
                    name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a1ea7bfd-c46b-4e47-a4a4-ea84f7f6e411",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $149850 | Estimated Completion Date:2023-01-12",
                    map_popup:
                        "  |  | Funding Awarded: $149850 | Estimated Completion Date:2023-01-12",
                    name: "Hoopa Valley Broadband Initiative Communications Studies",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Hoopa Valley Broadband Initiative Communications Studies",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a54a1dd5-19a1-4bc9-9e5c-786339dc04ba",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $60000 | Estimated Completion Date:2022-01-12",
                    map_popup:
                        "  |  | Funding Awarded: $60000 | Estimated Completion Date:2022-01-12",
                    name: "La Jolla Tribal Connectivity Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "La Jolla Tribal Connectivity Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "59a42c42-125f-4ddf-8eec-0c36569dfbeb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $60000 | Estimated Completion Date:2021-06-12",
                    map_popup:
                        "  |  | Funding Awarded: $60000 | Estimated Completion Date:2021-06-12",
                    name: "Project 1: Resighini Rancheria Broadband, Feasibility and Market Studies",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 1: Resighini Rancheria Broadband, Feasibility and Market Studies",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7c88634f-a165-45a1-a21d-24a3451c1a7b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $40000 | Estimated Completion Date:2021-10-12",
                    map_popup:
                        "  |  | Funding Awarded: $40000 | Estimated Completion Date:2021-10-12",
                    name: "Project 2: Resighini Rancheria Broadband Fiber, Wireless and Network Engineering Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 2: Resighini Rancheria Broadband Fiber, Wireless and Network Engineering Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "889f29a0-e72e-4f8d-b4a5-cab2b2fd700d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2022-12-04",
                    map_popup:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2022-12-04",
                    name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "1cddb7b5-d35a-4676-9509-c6e40dd00ce0",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2021-12-04",
                    map_popup:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2021-12-04",
                    name: "Project 1: Technical Feasibility Study for Broadband Deployment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 1: Technical Feasibility Study for Broadband Deployment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ddd1a841-7a04-405f-9225-5da7e26293e4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2022-06-04",
                    map_popup:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2022-06-04",
                    name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f4cddbc4-dd25-41bc-a57d-67ae6ab3b825",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $104200 | Estimated Completion Date:2021-09-04",
                    map_popup:
                        "  |  | Funding Awarded: $104200 | Estimated Completion Date:2021-09-04",
                    name: "Working With Communities For Sustainable Broadband\n(Bishop Indian Tribal Council)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Working With Communities For Sustainable Broadband\n(Bishop Indian Tribal Council)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "42a5dbf2-bda7-4c0c-9a60-a548fc78f6df",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $99500 | Estimated Completion Date:2022-06-04",
                    map_popup:
                        "  |  | Funding Awarded: $99500 | Estimated Completion Date:2022-06-04",
                    name: "Fort Independence Tribe Sustainable Broadband",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fort Independence Tribe Sustainable Broadband",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "156fbb5b-9f9e-4af4-9d3e-4b5a58cf8333",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2021-12-04",
                    map_popup:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2021-12-04",
                    name: "Project 1: Technical Feasibility Study for Broadband Deployment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 1: Technical Feasibility Study for Broadband Deployment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c62a2968-b583-4246-96cf-a023e1497503",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2022-06-04",
                    map_popup:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2022-06-04",
                    name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8c1e5dd1-cdf6-4977-ac11-0870c7422fa3",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2022-12-04",
                    map_popup:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2022-12-04",
                    name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "245ff623-b6b1-4f05-aa8e-53dfca3de813",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2022-06-04",
                    map_popup:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2022-06-04",
                    name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "08c84f20-a8ae-42e7-8219-e4383285b570",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2022-12-04",
                    map_popup:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2022-12-04",
                    name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 3: Financial and Organizational Feasibility Study for Broadband Development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "23dcd221-d765-4f63-9a8b-beea970d2c1d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2022-03-10",
                    map_popup:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2022-03-10",
                    name: "Project 1: Technical Feasibility Study for Broadband Deployment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 1: Technical Feasibility Study for Broadband Deployment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "148c78a6-48c8-4502-a32a-92f29f095234",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2022-09-10",
                    map_popup:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2022-09-10",
                    name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Project 2: Feasibility Study to Investigate Potential Broadband Partnerships",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5de17be5-43ce-44fa-8ed5-c8bc936ee559",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $90000 | Estimated Completion Date:2022-09-10",
                    map_popup:
                        "  |  | Funding Awarded: $90000 | Estimated Completion Date:2022-09-10",
                    name: "Santa Ynez Band of Chumash Indians Phase I",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Santa Ynez Band of Chumash Indians Phase I",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7e132ad2-cfc8-4c24-bef8-518186fc2e02",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $134400 | Estimated Completion Date:2022-05-13",
                    map_popup:
                        "  |  | Funding Awarded: $134400 | Estimated Completion Date:2022-05-13",
                    name: "EBKI Broadband Deployment Studies Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "EBKI Broadband Deployment Studies Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "30f8499f-aa0f-40e0-9aca-9244036a9aae",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $80000 | Estimated Completion Date:2022-11-30",
                    map_popup:
                        "  |  | Funding Awarded: $80000 | Estimated Completion Date:2022-11-30",
                    name: "HVPUD Pro Forma Financial Analysis\n",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "HVPUD Pro Forma Financial Analysis\n",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2b8eb68a-c25b-4ccb-979b-13183f2fd429",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $70000 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $70000 | Estimated Completion Date:2023-03-31",
                    name: "HVPUD - NOC Feasibility Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "HVPUD - NOC Feasibility Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "139fa109-af14-4394-99a4-7aa001e12cea",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2022-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $49750 | Estimated Completion Date:2022-09-30",
                    name: "Technical Feasibility Study for Broadband Deployment",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Technical Feasibility Study for Broadband Deployment",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8aee2162-2007-4da4-8772-95f0fbee3cf9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2022-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2022-09-30",
                    name: "Feasibility Study to Investigate Potential Broadband Partnerships",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Feasibility Study to Investigate Potential Broadband Partnerships",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7edf63d6-56cf-4742-9cb0-677271dabf2e",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2022-12-30",
                    map_popup:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2022-12-30",
                    name: "Financial and Organizational Feasibility Study for Broadband Development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Financial and Organizational Feasibility Study for Broadband Development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0f1f072b-a268-4f60-b8f6-b9b4b4bde5d9",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2022-10-31",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2022-10-31",
                    name: "Community Broadband Internet Feasibility Study & Implementation Plan",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Community Broadband Internet Feasibility Study & Implementation Plan",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "285a02b4-0449-4974-94f2-79aff93b9a5a",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2022-11-30",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2022-11-30",
                    name: "Tribal Technical Smart Cyber Infrastructure Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tribal Technical Smart Cyber Infrastructure Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b31738db-0a08-49d3-a97d-d7287d5bd343",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50000 | Estimated Completion Date:2023-01-31",
                    map_popup:
                        "  |  | Funding Awarded: $50000 | Estimated Completion Date:2023-01-31",
                    name: "Reliable emergency connectivity solutions and roadmap for future-forward Tribal broadband network development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Reliable emergency connectivity solutions and roadmap for future-forward Tribal broadband network development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3ccabc05-cbe7-4cb3-aeb0-f6b5e384708d",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2022-12-31",
                    name: "Tribal Broadband Vision and Strategy Plan",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tribal Broadband Vision and Strategy Plan",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "75a9c969-cf7d-4dab-a4ec-fc5ebc8ffa3b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $41000 | Estimated Completion Date:2023-03-31",
                    map_popup:
                        "  |  | Funding Awarded: $41000 | Estimated Completion Date:2023-03-31",
                    name: "Government IT Broadband Network Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Government IT Broadband Network Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "a1d11e57-898f-4941-9225-7d540594f2a1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-04-01",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-04-01",
                    name: "Broadband Feasibility Study Toro Peak 2022-2023",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Broadband Feasibility Study Toro Peak 2022-2023",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0b5ca6f5-c8c1-4f8d-b503-01ae56bd9b21",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $60000 | Estimated Completion Date:2024-08-31",
                    map_popup:
                        "  |  | Funding Awarded: $60000 | Estimated Completion Date:2024-08-31",
                    name: "Tribal Broadband  Feasibility Study: Investigation of Potential Partnerships and Implementation Plan for Broadband Infrastructure.",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tribal Broadband  Feasibility Study: Investigation of Potential Partnerships and Implementation Plan for Broadband Infrastructure.",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b83df2f5-5673-405b-a073-0a08f2012d57",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-01-31",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-01-31",
                    name: "CRIT Broadband Service Delivery Feasibility Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "CRIT Broadband Service Delivery Feasibility Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "19f240db-bb86-4227-ba27-d9baa7d3f7e1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2023-02-28",
                    map_popup:
                        "  |  | Funding Awarded: $49625 | Estimated Completion Date:2023-02-28",
                    name: "Feasibility Study to Investigate Potential Broadband Partners",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Feasibility Study to Investigate Potential Broadband Partners",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5456de85-25af-4cc4-b7b0-22ecb48e51e1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2023-02-28",
                    map_popup:
                        "  |  | Funding Awarded: $50625 | Estimated Completion Date:2023-02-28",
                    name: "Financial and Organizational Feasibility Study for Broadband Development",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Financial and Organizational Feasibility Study for Broadband Development",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "5a87d544-a41b-43e5-a26f-cfd2ee248301",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $45000 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $45000 | Estimated Completion Date:2022-12-31",
                    name: "Wireless Broadband Feasibility Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Wireless Broadband Feasibility Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "795cff02-0d6f-475e-afb8-7730d08761de",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $40000 | Estimated Completion Date:2023-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $40000 | Estimated Completion Date:2023-09-30",
                    name: "Government Transition to 7Tribes Network from All Tribal Networks",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Government Transition to 7Tribes Network from All Tribal Networks",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3b5479f3-9437-4942-8e9f-cbad5b8f1969",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-08-31",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-08-31",
                    name: "Tribal Broadband Vision and Strategy Plan",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tribal Broadband Vision and Strategy Plan",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "c016ad6f-0060-44f2-831f-7a74e72c21dc",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-08-31",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-08-31",
                    name: "5-Year Financial Model Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "5-Year Financial Model Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "2ca12986-1322-442e-8624-d57c7186ffcb",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $149200 | Estimated Completion Date:2023-04-15",
                    map_popup:
                        "  |  | Funding Awarded: $149200 | Estimated Completion Date:2023-04-15",
                    name: "Organizational and Legal Models for Tribal Broadband Operations",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Organizational and Legal Models for Tribal Broadband Operations",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "80601cb0-e942-441b-9c9d-ae9e367a1f11",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $149500 | Estimated Completion Date:2023-01-30",
                    map_popup:
                        "  |  | Funding Awarded: $149500 | Estimated Completion Date:2023-01-30",
                    name: "Sustainable Broadband for Bridgeport Indian Colony",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Sustainable Broadband for Bridgeport Indian Colony",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "312850db-6db1-4eea-9b8f-68a702575df1",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $50000 | Estimated Completion Date:2022-12-31",
                    map_popup:
                        "  |  | Funding Awarded: $50000 | Estimated Completion Date:2022-12-31",
                    name: "Los Coyotes Band of Cahuilla & Cupeno Indians Broadband Feasibility Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Los Coyotes Band of Cahuilla & Cupeno Indians Broadband Feasibility Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "bf7babec-ad52-4b83-b209-25e7bd7e6a08",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $85000 | Estimated Completion Date:2022-12-16",
                    map_popup:
                        "  |  | Funding Awarded: $85000 | Estimated Completion Date:2022-12-16",
                    name: "San Pasqual Broadband Feasibility Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "San Pasqual Broadband Feasibility Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7fdd9a45-6af8-44f5-abb7-9b4b40df0307",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-09-30",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-09-30",
                    name: "Tolowa Dee-Ni' Nation Broadband Study (Outreach, Technical Analysis and Wireless Spectrum)",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Tolowa Dee-Ni' Nation Broadband Study (Outreach, Technical Analysis and Wireless Spectrum)",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "ff153312-98f2-4984-974d-a0689552a8d2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-06-30",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2023-06-30",
                    name: "Fort Bidwell Indian Community Tribal Technical Assistance",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Fort Bidwell Indian Community Tribal Technical Assistance",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0e53558b-b66d-4690-b522-7d7e2fb67d5b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2024-04-26",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2024-04-26",
                    name: "HVPUD Pro Forma Financial Analysis\n",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "HVPUD Pro Forma Financial Analysis\n",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dca4c108-aa09-4807-8c5a-1201b8b160e4",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:",
                    name: "lipay Nation of Santa Ysabel Tribal Technical Assistance",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "lipay Nation of Santa Ysabel Tribal Technical Assistance",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dffcadd3-78ce-4d10-a267-bd7f13d4e1ce",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2024-01-23",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:2024-01-23",
                    name: "Middletown Rancheria Middle Mile Tower Feasibility",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Middletown Rancheria Middle Mile Tower Feasibility",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "7d5996e7-6118-4f22-9635-894dd648b0e6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:",
                    name: "North Fork Rancheria Broadband Planning, Feasibility and Sustainability Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "North Fork Rancheria Broadband Planning, Feasibility and Sustainability Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "8aefb27d-9793-4727-8cf8-d6863877abc2",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $277000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $277000 | Estimated Completion Date:",
                    name: "Round Valley Indian Tribes FTTH Project Description",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Round Valley Indian Tribes FTTH Project Description",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "98e89502-7e30-44ea-a7f4-a84bb925d40f",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $144900 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $144900 | Estimated Completion Date:",
                    name: "Digital 299 Tribal Fiber Network",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Digital 299 Tribal Fiber Network",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f5812bde-229d-4b07-88de-ca7726d0d996",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:",
                    name: "HPUL Fiber Broadband Report",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "HPUL Fiber Broadband Report",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "0aadac7b-3b99-444a-8fab-a8afa79df5fa",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    name: "Broadband Methodology and Management Plan",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Broadband Methodology and Management Plan",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "f78fcfdf-08c9-47af-b48a-976fc7def548",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $150000 | Estimated Completion Date:",
                    name: "Paskenta Wireless Connectivity Feasibility Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Paskenta Wireless Connectivity Feasibility Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "6daf8e3f-1c04-483a-a995-7ed946dbc20b",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:2026-12-01",
                    map_popup:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:2026-12-01",
                    name: "Enterprise Rancheria Sports and Entertainment (S&E) Complex Broadband Network",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Enterprise Rancheria Sports and Entertainment (S&E) Complex Broadband Network",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "61b7cdfe-8065-4ec1-9eee-95c52f6185ec",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:2025-08-29",
                    map_popup:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:2025-08-29",
                    name: "North Fork Rancheria Broadband Network Design",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "North Fork Rancheria Broadband Network Design",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "dcc33fb5-7c8c-4d14-8676-e380b46c0aee",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    name: "Big Sandy Tribal Fiber to Premise and Sustainability Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Big Sandy Tribal Fiber to Premise and Sustainability Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "67d25466-9ac4-4da1-8db5-55e913efda29",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $227560 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $227560 | Estimated Completion Date:",
                    name: "Cold Springs Rancheria Broadband Network Operations Model Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Cold Springs Rancheria Broadband Network Operations Model Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "3734573b-b6ee-4a31-ba20-ecdec052f841",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:2026-04-30",
                    map_popup:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:2026-04-30",
                    name: "Iipay Nation Fiber Pre-Engineering Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Iipay Nation Fiber Pre-Engineering Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "b88f3375-9719-4316-be88-94a090fc6956",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    name: "Pauma Band of Luise\u00f1o Indians Fiber Pre-Engineering Study",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Pauma Band of Luise\u00f1o Indians Fiber Pre-Engineering Study",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "41017ef4-9bed-4e75-9c8b-e543e18d84d6",
        },
        {
            createdtime: "2025-11-10T15:40:38.348",
            descriptors: {
                en: {
                    description:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    map_popup:
                        "  |  | Funding Awarded: $250000 | Estimated Completion Date:",
                    name: "Broadband Feasibility Study and Partnership Project",
                },
            },
            graph_id: "0284696e-975b-4b80-addc-f14391f6bb09",
            graph_publication_id: "b5932949-95e8-4138-b790-c23bbe5cee9c",
            legacyid: null,
            name: "Broadband Feasibility Study and Partnership Project",
            principaluser_id: null,
            resource_instance_lifecycle_state_id:
                "9375c9a7-dad2-4f14-a5c1-d7e329fdde4f",
            resourceinstanceid: "22ec3554-8a5e-4e7c-b9d3-e1845488112c",
        },
    ],
});
provide("datatypesToAdvancedSearchFacets", datatypesToAdvancedSearchFacets);
provide("graphs", graphs);
provide("getNodesForGraphId", getNodesForGraphId);

watchEffect(async () => {
    try {
        isLoading.value = true;
        fetchError.value = null;

        seedRootGroup();

        await Promise.all([fetchGraphs(), fetchFacets()]);
    } catch (error) {
        fetchError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
});

async function getNodesForGraphId(graphId: string): Promise<unknown[]> {
    const cachedNodes = graphIdsToNodes.value[graphId];
    if (cachedNodes) {
        return cachedNodes;
    }

    const isAlreadyRequested = Boolean(inflightLoads.get(graphId));
    if (isAlreadyRequested) {
        return await inflightLoads.get(graphId)!;
    }

    const pendingNodesRequest = fetchNodesForGraphId(graphId)
        .then((nodesMap) => {
            const nodes = Object.values(nodesMap);

            graphIdsToNodes.value = {
                ...graphIdsToNodes.value,
                [graphId]: nodes,
            };
            inflightLoads.delete(graphId);

            return nodes;
        })
        .catch((error) => {
            inflightLoads.delete(graphId);
            fetchError.value = error as Error;

            throw error;
        });

    inflightLoads.set(graphId, pendingNodesRequest);
    return await pendingNodesRequest;
}

async function fetchFacets() {
    const facets = await getAdvancedSearchFacets();

    datatypesToAdvancedSearchFacets.value = facets.reduce(
        (
            datatypeToAdvancedSearchFacets: Record<
                string,
                AdvancedSearchFacet[]
            >,
            advancedSearchFacet: AdvancedSearchFacet,
        ) => {
            const existingFacetsForDatatype =
                datatypeToAdvancedSearchFacets[
                    advancedSearchFacet.datatype_id
                ] ?? [];
            datatypeToAdvancedSearchFacets[advancedSearchFacet.datatype_id] =
                existingFacetsForDatatype.concat([advancedSearchFacet]);

            return datatypeToAdvancedSearchFacets;
        },
        {},
    );
}

async function fetchGraphs() {
    graphs.value = await getGraphs();
}

function seedRootGroup() {
    if (query) {
        rootGroupPayload.value = structuredClone(query);
    } else {
        rootGroupPayload.value = {
            graph_slug: undefined,
            logic: "AND",
            clauses: [],
            groups: [],
            aggregations: [],
        };
    }
}

async function search() {
    const results = await getSearchResults(rootGroupPayload.value!);
    console.log("Search results:", results);
}
</script>

<template>
    <div class="advanced-search">
        <Skeleton
            v-if="isLoading"
            style="height: 100%"
        />

        <Message
            v-else-if="fetchError"
            severity="error"
        >
            {{ fetchError.message }}
        </Message>

        <div v-else>
            <QueryGroup :group-payload="rootGroupPayload!" />

            <Button
                icon="pi pi-search"
                size="large"
                :label="$gettext('Search')"
                style="margin-top: 1rem; align-self: flex-start"
                @click="search"
            />
            <SearchResultsView :results="searchResults"></SearchResultsView>
        </div>
    </div>
</template>

<style scoped>
.advanced-search {
    width: 100%;
    height: 100%;
    background: var(--p-content-background);
    color: var(--p-text-color);
    display: flex;
    flex-direction: column;
}
.advanced-search > div {
    height: 100%;
    display: flex;
    flex-direction: column;
}
</style>
