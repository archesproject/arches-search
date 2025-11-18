<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";

import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import Select from "primevue/select";

const { $gettext } = useGettext();

type GraphSummary = {
    graphid: string;
    slug: string;
    name: string;
    label?: string;
    [key: string]: unknown;
};

type NodeSummary = {
    alias: string;
    name: string;
    label?: string;
    [key: string]: unknown;
};

type PathSequence = readonly (readonly [string, string])[];

const getNodesForGraphId =
    inject<(graphId: string) => Promise<NodeSummary[]>>("getNodesForGraphId");

if (!getNodesForGraphId) {
    throw new Error("PathBuilder is missing getNodesForGraphId injection.");
}

const emit = defineEmits<{
    (event: "update:pathSequence", value: [string, string][]): void;
}>();

const { anchorGraph, pathSequence, showAnchorGraphDropdown } = defineProps<{
    anchorGraph: GraphSummary;
    pathSequence?: PathSequence;
    showAnchorGraphDropdown?: boolean;
}>();

const isLoading = ref(false);
const configurationError = ref<Error | null>(null);
const nodesForAnchorGraph = ref<NodeSummary[]>([]);
const selectedNodeAlias = ref<string>("");

const anchorGraphDisplayOption = computed<GraphSummary>(() => {
    return {
        ...anchorGraph,
        label: anchorGraph.name,
    };
});

const shouldShowAnchorGraphDropdown = computed<boolean>(() => {
    return Boolean(showAnchorGraphDropdown);
});

watch(
    () => anchorGraph.graphid,
    async (nextGraphId) => {
        try {
            isLoading.value = true;
            configurationError.value = null;

            const fetchedNodes = await getNodesForGraphId(nextGraphId);
            nodesForAnchorGraph.value = fetchedNodes;
        } catch (error) {
            configurationError.value = error as Error;
            nodesForAnchorGraph.value = [];
        } finally {
            isLoading.value = false;
        }
    },
    { immediate: true },
);

watch(
    [() => pathSequence, () => anchorGraph.slug],
    () => {
        if (!pathSequence || pathSequence.length === 0) {
            selectedNodeAlias.value = "";
            return;
        }

        const [segmentGraphSlug, segmentNodeAlias] = pathSequence[0];

        if (segmentGraphSlug !== anchorGraph.slug) {
            selectedNodeAlias.value = "";
            return;
        }

        selectedNodeAlias.value = segmentNodeAlias;
    },
    { immediate: true },
);

watch(selectedNodeAlias, (nextAlias) => {
    const nextPath: [string, string][] = [[anchorGraph.slug, nextAlias]];
    emit("update:pathSequence", nextPath);
});
</script>

<template>
    <Message
        v-if="configurationError"
        severity="error"
    >
        {{ configurationError.message }}
    </Message>

    <div
        v-else
        class="path-builder"
    >
        <Select
            v-if="shouldShowAnchorGraphDropdown"
            :model-value="anchorGraphDisplayOption"
            :options="[anchorGraphDisplayOption]"
            option-label="label"
            disabled
        />

        <Select
            v-model="selectedNodeAlias"
            auto-filter-focus
            filter
            option-label="card_x_node_x_widget_label"
            option-value="node_alias"
            :disabled="nodesForAnchorGraph.length === 0"
            :filter-placeholder="$gettext('Search nodes...')"
            :loading="isLoading"
            :options="nodesForAnchorGraph"
            :placeholder="$gettext('Select node...')"
        />
    </div>
</template>

<style scoped>
.path-builder {
    display: flex;
    gap: 0.5rem;
}
</style>
