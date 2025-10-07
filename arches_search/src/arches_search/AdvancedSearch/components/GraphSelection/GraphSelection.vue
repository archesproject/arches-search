<script setup lang="ts">
import { defineEmits, ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Skeleton from "primevue/skeleton";
import Message from "primevue/message";

import { getGraphs } from "@/arches_search/AdvancedSearch/components/GraphSelection/api.ts";

const { $gettext } = useGettext();

const emit = defineEmits<{
    (e: "graph-selected", graphSlug: { [key: string]: unknown } | null): void;
}>();

const graphs = ref<{ [key: string]: unknown }[]>([]);
const isLoading = ref(true);
const configurationError = ref();

const selectedGraphSlug = ref(null);
const selectedGraph = ref<{ [key: string]: unknown } | null>(null);

watchEffect(async () => {
    isLoading.value = true;

    try {
        graphs.value = await getGraphs();
    } catch (error) {
        configurationError.value = error;
    } finally {
        isLoading.value = false;
    }
});

watch(selectedGraphSlug, (graphSlug) => {
    selectedGraph.value =
        graphs.value.find((graph) => graph.slug === graphSlug) || null;
    emit("graph-selected", selectedGraph.value);
});
</script>
<template>
    <div>
        <Skeleton
            v-if="isLoading"
            style="height: 10rem"
        />
        <Message
            v-else-if="configurationError"
            severity="error"
        >
            {{ configurationError.message }}
        </Message>
        <div v-else>
            <span>{{ $gettext("I want to find") }}</span>
            <Select
                v-model="selectedGraphSlug"
                :options="graphs"
                :placeholder="$gettext('Select a graph...')"
                option-label="name"
                option-value="slug"
            />
        </div>
    </div>
</template>
