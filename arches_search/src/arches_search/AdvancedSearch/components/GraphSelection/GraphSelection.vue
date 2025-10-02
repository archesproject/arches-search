<script setup lang="ts">
import { defineEmits, ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Skeleton from "primevue/skeleton";
import Message from "primevue/message";

import { getGraphs } from "@/arches_search/AdvancedSearch/components/GraphSelection/api.ts";

const { $gettext } = useGettext();

const emit = defineEmits<{
    (e: "graph-selected", graphSlug: string): void;
}>();

const graphs = ref([]);
const isLoading = ref(true);
const configurationError = ref();

const selectedGraph = ref(null);

const placeholderToken = "%{graph}";
const translatedSentence = $gettext("I want to find %{graph} that have...");

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

watch(selectedGraph, (newGraph) => {
    if (newGraph) {
        emit("graph-selected", newGraph);
    }
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
            <span>{{ translatedSentence.split(placeholderToken)[0] }}</span>
            <Select
                v-model="selectedGraph"
                :options="graphs"
                :placeholder="$gettext('Select a graph...')"
                option-label="name"
                option-value="slug"
            />
            <span>{{ translatedSentence.split(placeholderToken)[1] }}</span>
        </div>
    </div>
</template>
