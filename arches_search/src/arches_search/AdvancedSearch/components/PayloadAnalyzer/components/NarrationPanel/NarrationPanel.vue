<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Textarea from "primevue/textarea";
import Message from "primevue/message";

import {
    describeAdvancedSearchQuery,
    type NodeMetadataMap,
} from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/components/NarrationPanel/query-narrator.ts";
import { getNodeMetadataForPayload } from "@/arches_search/AdvancedSearch/api.ts";

import type {
    AdvancedSearchFacet,
    GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

type GraphSummary = {
    graphid?: string;
    slug?: string;
    name?: string;
    label?: string;
    [key: string]: unknown;
};

const { $gettext } = useGettext();

const { payload, graphs, datatypesToAdvancedSearchFacets } = defineProps<{
    payload: GroupPayload;
    graphs: GraphSummary[];
    datatypesToAdvancedSearchFacets: Record<string, AdvancedSearchFacet[]>;
}>();

const nodeMetadata = ref<NodeMetadataMap>({} as NodeMetadataMap);
const fetchError = ref<Error | null>(null);

const narration = computed<string>(() => {
    return describeAdvancedSearchQuery({
        payload: payload,
        graphs: graphs,
        datatypesToAdvancedSearchFacets: datatypesToAdvancedSearchFacets,
        gettext: $gettext,
        nodeMetadata: nodeMetadata.value,
    });
});

watch(
    () => payload,
    async (newPayload) => {
        if (!newPayload) {
            nodeMetadata.value = {} as NodeMetadataMap;
            fetchError.value = null;
            return;
        }

        try {
            fetchError.value = null;

            const fetchedMetadata = await getNodeMetadataForPayload(
                newPayload as unknown as { [key: string]: unknown },
            );

            nodeMetadata.value = (fetchedMetadata ?? {}) as NodeMetadataMap;
        } catch (possibleError) {
            fetchError.value = possibleError as Error;
            nodeMetadata.value = {} as NodeMetadataMap;
        }
    },
    { deep: true, immediate: true },
);
</script>

<template>
    <Message
        v-if="fetchError"
        severity="error"
    >
        {{ fetchError.message }}
    </Message>

    <Textarea
        class="payload-analyzer-textarea"
        :model-value="narration"
        rows="38"
        readonly
    />
</template>
