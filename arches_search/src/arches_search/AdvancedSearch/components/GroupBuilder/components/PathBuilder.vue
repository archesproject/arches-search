<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import Select from "primevue/select";

type GraphSummary = {
    id?: string;
    graphid?: string;
    slug?: string;
    name?: string;
    label?: string;
    [key: string]: unknown;
};

type NodeSummary = {
    alias?: string;
    name?: string;
    label?: string;
    [key: string]: unknown;
};

const props = defineProps<{
    anchorGraph: GraphSummary;
    pathSequence?: readonly (readonly [string, string])[];
    maxPathSegments?: number;
    showAnchorGraphDropdown?: boolean;
}>();

const emit = defineEmits<{
    (event: "update:pathSequence", value: [string, string][]): void;
}>();

const { $gettext } = useGettext();

const getNodesForGraphId =
    inject<(graphId: string) => Promise<NodeSummary[]>>("getNodesForGraphId");

if (!getNodesForGraphId) {
    throw new Error("PathBuilder is missing getNodesForGraphId injection.");
}

const isLoading = ref(false);
const configurationError = ref<Error | null>(null);
const nodesForAnchorGraph = ref<NodeSummary[]>([]);

const anchorGraphSlug = computed<string>(function getAnchorGraphSlug() {
    return String(props.anchorGraph.slug ?? "");
});

const anchorGraphIdentifier = computed<string | null>(
    function getAnchorGraphIdentifier() {
        const rawIdentifier = props.anchorGraph.graphid ?? props.anchorGraph.id;
        const identifierString =
            rawIdentifier !== undefined && rawIdentifier !== null
                ? String(rawIdentifier)
                : "";

        return identifierString || null;
    },
);

const anchorGraphOptionForDisplay = computed<GraphSummary>(
    function getAnchorGraphOptionForDisplay() {
        const fallbackLabel =
            props.anchorGraph.label ??
            props.anchorGraph.name ??
            props.anchorGraph.slug ??
            "";

        return {
            ...props.anchorGraph,
            label: String(fallbackLabel),
        };
    },
);

const shouldShowAnchorGraphDropdown = computed<boolean>(
    function getShouldShowAnchorGraphDropdown() {
        return Boolean(props.showAnchorGraphDropdown);
    },
);

const selectedNodeAlias = computed<string>({
    get(): string {
        const pathSequenceRaw = props.pathSequence;

        if (!Array.isArray(pathSequenceRaw) || pathSequenceRaw.length === 0) {
            return "";
        }

        const firstSegment = pathSequenceRaw[0];

        if (!Array.isArray(firstSegment) || firstSegment.length < 2) {
            return "";
        }

        const segmentGraphSlug = String(firstSegment[0] ?? "");
        const segmentNodeAlias = String(firstSegment[1] ?? "");

        if (segmentGraphSlug !== anchorGraphSlug.value) {
            return "";
        }

        return segmentNodeAlias;
    },
    set(nextAliasRaw: string): void {
        const normalizedAlias =
            typeof nextAliasRaw === "string" ? nextAliasRaw : "";

        const graphSlug = anchorGraphSlug.value;

        const nextPath: [string, string][] = graphSlug
            ? [[graphSlug, normalizedAlias]]
            : [];

        emit("update:pathSequence", nextPath);
    },
});

watch(
    anchorGraphIdentifier,
    async function loadNodesForAnchorGraph(nextGraphIdentifier) {
        if (!nextGraphIdentifier) {
            nodesForAnchorGraph.value = [];
            return;
        }

        try {
            isLoading.value = true;
            configurationError.value = null;

            const fetchedNodes = await getNodesForGraphId(nextGraphIdentifier);
            nodesForAnchorGraph.value = Array.isArray(fetchedNodes)
                ? fetchedNodes
                : [];
        } catch (error) {
            configurationError.value = error as Error;
        } finally {
            isLoading.value = false;
        }
    },
    { immediate: true },
);
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
            :model-value="anchorGraphOptionForDisplay"
            :options="[anchorGraphOptionForDisplay]"
            option-label="label"
            disabled
        />

        <Select
            v-model="selectedNodeAlias"
            option-label="name"
            option-value="alias"
            :options="nodesForAnchorGraph"
            :placeholder="$gettext('Select node...')"
            :disabled="nodesForAnchorGraph.length === 0"
            :loading="isLoading"
        />
    </div>
</template>

<style scoped>
.path-builder {
    display: flex;
    gap: 0.5rem;
}
</style>
