<script setup lang="ts">
import { ref, computed, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import Textarea from "primevue/textarea";

import { describeAdvancedSearchQuery } from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/components/NarrationPanel/query-narrator.ts";
import {
    getNodeMetadataForPayload,
    getResourceNamesForPayload,
} from "@/arches_search/AdvancedSearch/api.ts";

import type {
    AdvancedSearchFacet,
    GraphModel,
    GroupPayload,
    NodeMetadataMap,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { payload, graphs, datatypesToAdvancedSearchFacets } = defineProps<{
    payload: GroupPayload;
    graphs: GraphModel[];
    datatypesToAdvancedSearchFacets: Record<string, AdvancedSearchFacet[]>;
}>();

const nodeMetadata = ref<NodeMetadataMap>({});
const resourceNames = ref<Record<string, string>>({});
const isLoading = ref(false);
const fetchError = ref<Error | null>(null);

const narration = computed(() =>
    describeAdvancedSearchQuery({
        payload,
        graphs,
        datatypesToAdvancedSearchFacets,
        gettext: $gettext,
        nodeMetadata: nodeMetadata.value,
        resourceNames: resourceNames.value,
    }),
);

watchEffect(() => {
    void fetchNarrationData(payload);
});

async function fetchNarrationData(currentPayload: GroupPayload) {
    isLoading.value = true;
    fetchError.value = null;

    try {
        const [fetchedMetadata, fetchedResourceNames] = await Promise.all([
            getNodeMetadataForPayload(currentPayload),
            getResourceNamesForPayload(currentPayload),
        ]);

        console.log("Fetched node metadata:", fetchedMetadata);
        console.log("Fetched resource names:", fetchedResourceNames);
        nodeMetadata.value = (fetchedMetadata ?? {}) as NodeMetadataMap;
        resourceNames.value = (fetchedResourceNames ?? {}) as Record<
            string,
            string
        >;
    } catch (error) {
        if (error instanceof Error) {
            fetchError.value = error;
        } else {
            fetchError.value = new Error(
                $gettext(
                    "An unknown error occurred while fetching node metadata.",
                ),
            );
        }
        nodeMetadata.value = {};
        resourceNames.value = {};
    } finally {
        isLoading.value = false;
    }
}
</script>

<template>
    <Skeleton
        v-if="isLoading"
        class="payload-analyzer-textarea"
    />

    <Message
        v-else-if="fetchError"
        severity="error"
    >
        {{ fetchError.message }}
    </Message>

    <Textarea
        v-else
        class="payload-analyzer-textarea"
        :model-value="narration"
        rows="38"
        readonly
    />
</template>
