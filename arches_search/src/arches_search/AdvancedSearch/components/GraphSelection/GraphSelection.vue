<script setup lang="ts">
import { defineEmits, defineProps, ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Skeleton from "primevue/skeleton";
import Message from "primevue/message";

import { getGraphs } from "@/arches_search/AdvancedSearch/components/GraphSelection/api.ts";

const { $gettext } = useGettext();

const { initialGraphSlug } = defineProps<{
    initialGraphSlug?: string | null;
}>();

const emit = defineEmits<{
    (
        e: "update:selectedGraph",
        graphObject: { [key: string]: unknown } | null,
    ): void;
}>();

const configurationError = ref<Error>();
const graphs = ref<{ [key: string]: unknown }[]>([]);
const isLoading = ref(true);
const selectedGraph = ref<{ [key: string]: unknown } | null>();
const selectedGraphSlug = ref<string | null>();

watchEffect(async () => {
    isLoading.value = true;
    configurationError.value = undefined;

    try {
        graphs.value = await getGraphs();
    } catch (error) {
        configurationError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
});

watch(
    () => [graphs.value, initialGraphSlug],
    () => {
        if (!graphs.value.length) {
            return;
        }

        if (initialGraphSlug && selectedGraphSlug.value == null) {
            selectedGraphSlug.value = initialGraphSlug;
        }
    },
    { immediate: true, deep: false },
);

watch(selectedGraphSlug, (newGraphSlug) => {
    if (!newGraphSlug) {
        selectedGraph.value = null;
        emit("update:selectedGraph", null);
        return;
    }

    const matchedGraph =
        graphs.value.find((graphItem) => graphItem.slug === newGraphSlug) ||
        null;

    selectedGraph.value = matchedGraph;
    emit("update:selectedGraph", matchedGraph);
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
                option-label="name"
                option-value="slug"
                :options="graphs"
                :placeholder="$gettext('Select a graph...')"
                :show-clear="true"
            />
        </div>
    </div>
</template>
