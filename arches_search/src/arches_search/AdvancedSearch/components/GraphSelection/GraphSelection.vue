<script setup lang="ts">
import { defineEmits, defineProps, ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Skeleton from "primevue/skeleton";
import Message from "primevue/message";

import { getGraphs } from "@/arches_search/AdvancedSearch/components/GraphSelection/api.ts";

const { $gettext } = useGettext();

const props = defineProps<{
    initialGraphSlug?: string | null;
}>();

const emit = defineEmits<{
    (e: "graph-selected", graphObject: { [key: string]: unknown } | null): void;
}>();

const graphs = ref<{ [key: string]: unknown }[]>([]);
const isLoading = ref(true);
const configurationError = ref<unknown>(null);

const selectedGraphSlug = ref<string | null>(null);
const selectedGraph = ref<{ [key: string]: unknown } | null>(null);

watchEffect(async () => {
    isLoading.value = true;
    configurationError.value = null;

    try {
        const fetchedGraphs = await getGraphs();
        graphs.value = Array.isArray(fetchedGraphs) ? fetchedGraphs : [];
    } catch (caughtError) {
        configurationError.value = caughtError;
    } finally {
        isLoading.value = false;
    }
});

/**
 * Hydrate selection from prop once graphs are available,
 * and also if the prop changes later.
 */
watch(
    () => [graphs.value, props.initialGraphSlug] as const,
    () => {
        if (!graphs.value.length) {
            return;
        }
        if (props.initialGraphSlug && selectedGraphSlug.value == null) {
            const exists = graphs.value.some(
                (graphItem) => graphItem.slug === props.initialGraphSlug,
            );
            if (exists) {
                selectedGraphSlug.value = props.initialGraphSlug;
            }
        }
    },
    { immediate: true, deep: false },
);

watch(selectedGraphSlug, (newGraphSlug) => {
    if (!newGraphSlug) {
        selectedGraph.value = null;
        emit("graph-selected", null);
        return;
    }
    const matchedGraph =
        graphs.value.find((graphItem) => graphItem.slug === newGraphSlug) ||
        null;
    selectedGraph.value = matchedGraph;
    emit("graph-selected", matchedGraph);
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
            {{
                configurationError instanceof Error
                    ? configurationError.message
                    : $gettext("There was a problem loading graphs.")
            }}
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
