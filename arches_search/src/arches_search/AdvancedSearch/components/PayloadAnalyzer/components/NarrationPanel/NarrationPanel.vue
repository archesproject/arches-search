<script setup lang="ts">
import { toRef } from "vue";

import Message from "openvue/message";
import Skeleton from "openvue/skeleton";
import Textarea from "openvue/textarea";

import { useQueryDescription } from "@/arches_search/AdvancedSearch/composables/useQueryDescription.ts";

import type {
    AdvancedSearchFacet,
    GraphModel,
    GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

const { payload, graphs, datatypesToAdvancedSearchFacets } = defineProps<{
    payload: GroupPayload;
    graphs: GraphModel[];
    datatypesToAdvancedSearchFacets: Record<string, AdvancedSearchFacet[]>;
}>();

const { description, isLoading, fetchError } = useQueryDescription({
    payload: toRef(() => payload),
    graphs: toRef(() => graphs),
    datatypesToAdvancedSearchFacets: toRef(
        () => datatypesToAdvancedSearchFacets,
    ),
});
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
        :model-value="description"
        rows="38"
        readonly
    />
</template>
