<script setup lang="ts">
import { computed, inject, ref, useId, watch, watchEffect } from "vue";

import Message from "primevue/message";
import Select from "primevue/select";
import Button from "primevue/button";

import type { Ref } from "vue";

const { pathSequence, anchorGraph } = defineProps<{
    anchorGraph: { [key: string]: unknown };
    pathSequence?: [string, string][];
}>();

const emit = defineEmits<{
    (e: "update:pathSequence", value: [string, string][]): void;
}>();

const graphs = inject<Ref<Record<string, unknown>[]>>("graphs")!;
const getNodesForGraphId =
    inject<(graphId: string) => Promise<{ [key: string]: unknown }[]>>(
        "getNodesForGraphId",
    )!;

const isLoading = ref(false);
const configurationError = ref<Error | undefined>();
const graphIdsToNodes = ref<Record<string, { [key: string]: unknown }[]>>({});
const graphSlugsToGraphIds = ref<Record<string, string>>({});

const localPathSequence = ref<[string, string][]>([...(pathSequence ?? [])]);

const shouldShowAppendButton = computed<boolean>(() => {
    if (!localPathSequence.value.length) {
        return false;
    }

    const [finalGraphSlug, finalNodeAlias] =
        localPathSequence.value[localPathSequence.value.length - 1];

    if (!finalGraphSlug || !finalNodeAlias) {
        return false;
    }

    const finalNode = getNodeForGraphSlugNodeAlias(
        finalGraphSlug,
        finalNodeAlias,
    );
    const finalNodeConfig = finalNode?.config as
        | { [key: string]: unknown }
        | undefined;

    return Boolean(finalNodeConfig?.graphs);
});

watchEffect(() => {
    graphSlugsToGraphIds.value = {};

    for (const graph of graphs.value) {
        graphSlugsToGraphIds.value[graph.slug as string] =
            graph.graphid as string;
    }

    if (localPathSequence.value.length === 0) {
        const initialSlug = anchorGraph.slug as string;
        localPathSequence.value = [[initialSlug, ""]];
    }
});

watch(
    () => pathSequence,
    (updatedPathSequence) => {
        const next = [...(updatedPathSequence ?? [])];
        const hasIncompleteLocal = localPathSequence.value.some(
            (segment) => !segment[0] || !segment[1],
        );
        if (
            !hasIncompleteLocal ||
            next.length >= localPathSequence.value.length
        ) {
            localPathSequence.value = next;
        }
    },
);

watch(
    () => localPathSequence.value,
    (updatedLocalPathSequence) => {
        emit("update:pathSequence", updatedLocalPathSequence);
    },
);

watch(
    () => localPathSequence.value,
    async (updatedLocalPathSequence) => {
        for (const segment of updatedLocalPathSequence) {
            if (segment) {
                await ensureNodesLoadedForSlug(segment[0]);
            }
        }
    },
    { immediate: true },
);

async function ensureNodesLoadedForSlug(graphSlug: string): Promise<void> {
    const graphId = graphSlugsToGraphIds.value[graphSlug];
    if (!graphId || graphIdsToNodes.value[graphId]) {
        return;
    }

    try {
        isLoading.value = true;
        configurationError.value = undefined;

        const nodes = await getNodesForGraphId(graphId);
        graphIdsToNodes.value = { ...graphIdsToNodes.value, [graphId]: nodes };
    } catch (error) {
        configurationError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
}

function getNodesForGraphSlug(
    graphSlug: string | null,
): { [key: string]: unknown }[] {
    if (!graphSlug) {
        return [];
    }

    const graphId = graphSlugsToGraphIds.value[graphSlug];
    return graphId ? graphIdsToNodes.value[graphId] ?? [] : [];
}

function getNodeForGraphSlugNodeAlias(
    graphSlug: string | null,
    nodeAlias: string | null,
): { [key: string]: unknown } | null {
    if (!graphSlug || !nodeAlias) {
        return null;
    }

    const graphId = graphSlugsToGraphIds.value[graphSlug];
    return (
        graphIdsToNodes.value[graphId]?.find(
            (node) => node.alias === nodeAlias,
        ) ?? null
    );
}

function getPermittedRelationshipGraphs(
    sequenceIndex: number,
): { [key: string]: unknown }[] {
    if (sequenceIndex === 0) {
        return [anchorGraph];
    }

    const previousSegment = localPathSequence.value[sequenceIndex - 1];
    const previousNode = getNodeForGraphSlugNodeAlias(
        previousSegment[0],
        previousSegment[1],
    );
    const previousNodeConfig = previousNode?.config as
        | { [key: string]: unknown }
        | undefined;

    const permittedGraphData: { [key: string]: string }[] =
        (previousNodeConfig?.graphs as { [key: string]: string }[]) || [];

    return graphs.value.reduce<{ [key: string]: unknown }[]>(
        (accumulatedGraphs, graphData) => {
            if (
                permittedGraphData.some(
                    (reference) => reference.graphid === graphData.graphid,
                )
            ) {
                accumulatedGraphs.push(graphData);
            }

            return accumulatedGraphs;
        },
        [],
    );
}

function shouldShowGraphSelect(sequenceIndex: number): boolean {
    return (
        sequenceIndex !== 0 &&
        getPermittedRelationshipGraphs(sequenceIndex).length > 1
    );
}

function updateSegment(
    sequenceIndex: number,
    graphSlug: string,
    nodeAlias: string,
): void {
    const truncatedSequence = localPathSequence.value.slice(
        0,
        sequenceIndex + 1,
    );

    truncatedSequence[sequenceIndex] = [graphSlug, nodeAlias];
    localPathSequence.value = truncatedSequence;
}

function onGraphChanged(sequenceIndex: number, graphSlug: string): void {
    updateSegment(sequenceIndex, graphSlug, "");
}

function onNodeChanged(sequenceIndex: number, nodeAlias: string): void {
    const graphSlug = localPathSequence.value[sequenceIndex][0];
    updateSegment(sequenceIndex, graphSlug, nodeAlias);
}

function addSegment(): void {
    const permittedRelationshipGraphs = getPermittedRelationshipGraphs(
        localPathSequence.value.length,
    );

    if (permittedRelationshipGraphs.length === 1) {
        const graphSlug = permittedRelationshipGraphs[0].slug as string;
        localPathSequence.value = [...localPathSequence.value, [graphSlug, ""]];
        return;
    }

    localPathSequence.value = [...localPathSequence.value, ["", ""]];
}

function removeSegment(sequenceIndex: number): void {
    if (sequenceIndex === 0) {
        return;
    }

    localPathSequence.value = localPathSequence.value.slice(0, sequenceIndex);
}
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
        <div
            v-for="(segment, sequenceIndex) in localPathSequence"
            :key="useId() + segment[0] + segment[1]"
            class="path-segment"
        >
            <Select
                v-if="shouldShowGraphSelect(sequenceIndex)"
                option-label="name"
                option-value="slug"
                :model-value="segment[0]"
                :options="getPermittedRelationshipGraphs(sequenceIndex)"
                :placeholder="$gettext('Select graph...')"
                @update:model-value="
                    (value) => onGraphChanged(sequenceIndex, value)
                "
            />
            <Select
                option-label="name"
                option-value="alias"
                :model-value="segment[1]"
                :options="getNodesForGraphSlug(segment[0])"
                :placeholder="$gettext('Select node...')"
                @update:model-value="
                    (value) => onNodeChanged(sequenceIndex, value)
                "
            />
            <Button
                v-if="sequenceIndex > 0"
                icon="pi pi-times"
                severity="secondary"
                :aria-label="$gettext('Remove segment')"
                @click="removeSegment(sequenceIndex)"
            />
        </div>

        <Button
            v-if="shouldShowAppendButton"
            icon="pi pi-plus"
            :aria-label="$gettext('Add segment')"
            @click="addSegment"
        />
    </div>
</template>

<style scoped>
.path-builder {
    display: flex;
    gap: 0.5rem;
}

.path-segment {
    display: flex;
    gap: 0.5rem;
}
</style>
