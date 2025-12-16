<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";

import { useGettext } from "vue3-gettext";

// import Button from "primevue/button";
import Card from "primevue/card";
import Message from "primevue/message";
import Select from "primevue/select";

import PathBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/PathBuilder.vue";

import type {
    GraphModel,
    GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type RelationshipState = NonNullable<GroupPayload["relationship"]>;
type TraversalQuantifier = RelationshipState["traversal_quantifiers"][number];
type PathSequence = [string, string][];

type RelatableGraphSummary = {
    graph_id: string;
    slug: string;
    name: string;
};

type RelatableNodesTreeResponse = {
    target_graph_id: string;
    relatable_graphs: RelatableGraphSummary[];
    options: Array<{
        key: string;
        label: string;
        children?: unknown[];
        data?: {
            graph_id?: string;
            slug?: string | null;
            [key: string]: unknown;
        };
        [key: string]: unknown;
    }>;
};

const TRAVERSAL_QUANTIFIER_ANY = "ANY";
const TRAVERSAL_QUANTIFIER_ALL = "ALL";
const TRAVERSAL_QUANTIFIER_NONE = "NONE";

const emit = defineEmits<{
    (event: "update:relationship", value: RelationshipState | null): void;
    (event: "update:innerGraphSlug", value: string): void;
}>();

const { relationship, anchorGraphSlug, innerGraphSlug } = defineProps<{
    relationship: RelationshipState;
    anchorGraphSlug: string;
    innerGraphSlug: string;
}>();

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;
const getRelatableNodesTreeForGraphId = inject<
    (graphId: string) => Promise<RelatableNodesTreeResponse>
>("getRelatableNodesTreeForGraphId")!;

const isLoadingRelatableTree = ref(false);
const hasLoadedRelatableTree = ref(false);
const relatableTreeError = ref<Error | null>(null);
const relatableNodesTreeResponse = ref<RelatableNodesTreeResponse | null>(null);

const anchorGraph = computed(() => {
    return graphs.value.find(
        (graphModel) => graphModel.slug === anchorGraphSlug,
    )!;
});

const relationshipLeadinText = computed(() => {
    return $gettext("Relate %{outer} to", { outer: anchorGraph.value.name });
});

const relatableGraphOptions = computed(() => {
    const relatableGraphs =
        relatableNodesTreeResponse.value?.relatable_graphs ?? [];

    return relatableGraphs
        .map((graphSummary) => {
            return { label: graphSummary.name, value: graphSummary.slug };
        })
        .sort((left, right) => left.label.localeCompare(right.label));
});

const hasCompatibleRelationshipGraphs = computed(() => {
    return relatableGraphOptions.value.length > 0;
});

const hasSelectedRelatedGraph = computed(() => {
    return innerGraphSlug.length > 0;
});

const hasSelectedRelationshipPath = computed(() => {
    return relationship.path.length > 0;
});

const traversalQuantifierOptions = computed(() => {
    return [
        {
            label: $gettext("At least one related record must match"),
            value: TRAVERSAL_QUANTIFIER_ANY,
        },
        {
            label: $gettext("Every related record must match"),
            value: TRAVERSAL_QUANTIFIER_ALL,
        },
        {
            label: $gettext("No related records match"),
            value: TRAVERSAL_QUANTIFIER_NONE,
        },
    ];
});

const currentTraversalQuantifier = computed(() => {
    return relationship.traversal_quantifiers[0] ?? TRAVERSAL_QUANTIFIER_ANY;
});

const pathSequenceForPathBuilder = computed<PathSequence>(() => {
    const firstSegment = relationship.path[0];
    if (!firstSegment) {
        return [];
    }
    return [[firstSegment[0], firstSegment[1]]];
});

watch(
    () => anchorGraph.value.graphid,
    async (anchorGraphId) => {
        isLoadingRelatableTree.value = true;
        hasLoadedRelatableTree.value = false;
        relatableTreeError.value = null;

        try {
            relatableNodesTreeResponse.value =
                await getRelatableNodesTreeForGraphId(anchorGraphId);
        } catch (e) {
            relatableTreeError.value = e as Error;
            relatableNodesTreeResponse.value = null;
        } finally {
            isLoadingRelatableTree.value = false;
            hasLoadedRelatableTree.value = true;
        }
    },
    { immediate: true },
);

watch(
    () => relatableGraphOptions.value,
    (options) => {
        if (innerGraphSlug) {
            return;
        }

        if (options.length !== 1) {
            return;
        }

        emit("update:innerGraphSlug", options[0]!.value);
    },
    { immediate: true },
);

watch(
    () => innerGraphSlug,
    (nextInnerGraphSlug, previousInnerGraphSlug) => {
        if (!previousInnerGraphSlug) {
            return;
        }

        if (nextInnerGraphSlug === previousInnerGraphSlug) {
            return;
        }

        emit("update:relationship", { ...relationship, path: [] });
    },
);

function onChangeRelatedGraphSlug(nextGraphSlug: string): void {
    emit("update:innerGraphSlug", nextGraphSlug);
}

function onUpdatePathSequence(nextPathSequence: PathSequence): void {
    if (nextPathSequence.length === 0) {
        emit("update:relationship", { ...relationship, path: [] });
        return;
    }

    const [firstGraphSlug, firstNodeAlias] = nextPathSequence[0]!;

    emit("update:relationship", {
        ...relationship,
        path: [[firstGraphSlug, firstNodeAlias]],
        is_inverse: firstGraphSlug !== anchorGraphSlug,
    });
}

function onChangeTraversalQuantifier(nextQuantifier: string): void {
    emit("update:relationship", {
        ...relationship,
        traversal_quantifiers: [nextQuantifier as TraversalQuantifier],
    });
}

// function onCloseClick(): void {
//     emit("update:relationship", null);
// }
</script>

<template>
    <Card class="relationship-card">
        <template #content>
            <Message
                v-if="relatableTreeError"
                severity="error"
                class="relationship-message"
            >
                {{ relatableTreeError.message }}
            </Message>

            <div
                v-else
                class="relationship-inline-row"
            >
                <span class="relationship-leadin-text">
                    {{ relationshipLeadinText }}
                </span>

                <Select
                    v-if="hasCompatibleRelationshipGraphs"
                    :model-value="innerGraphSlug"
                    :options="relatableGraphOptions"
                    :filter="true"
                    option-label="label"
                    option-value="value"
                    class="relationship-related-graph-select"
                    :disabled="isLoadingRelatableTree"
                    :placeholder="$gettext('Related record type')"
                    :aria-label="$gettext('Related record type')"
                    @update:model-value="onChangeRelatedGraphSlug"
                />

                <span
                    v-if="hasSelectedRelatedGraph"
                    class="relationship-leadin-text"
                >
                    {{ $gettext("via") }}
                </span>

                <div
                    v-if="hasSelectedRelatedGraph"
                    class="relationship-path-builder"
                >
                    <PathBuilder
                        :graph-slugs="[anchorGraphSlug, innerGraphSlug]"
                        :path-sequence="pathSequenceForPathBuilder"
                        :relationship-between-graphs="[
                            anchorGraphSlug,
                            innerGraphSlug,
                        ]"
                        :should-prepend-graph-name="true"
                        @update:path-sequence="onUpdatePathSequence"
                    />
                </div>

                <span
                    v-if="
                        hasSelectedRelatedGraph && hasSelectedRelationshipPath
                    "
                    class="relationship-leadin-text"
                >
                    {{ $gettext("and") }}
                </span>

                <Select
                    v-if="
                        hasSelectedRelatedGraph && hasSelectedRelationshipPath
                    "
                    :model-value="currentTraversalQuantifier"
                    :options="traversalQuantifierOptions"
                    option-label="label"
                    option-value="value"
                    class="relationship-quantifier-select"
                    :placeholder="$gettext('Match requirement')"
                    :aria-label="$gettext('Relationship match requirement')"
                    @update:model-value="onChangeTraversalQuantifier"
                />

                <!-- <Button
                    variant="text"
                    severity="danger"
                    icon="pi pi-times"
                    class="relationship-inline-close"
                    :aria-label="$gettext('Remove relationship')"
                    @click="onCloseClick"
                /> -->
            </div>
        </template>
    </Card>
</template>

<style scoped>
.relationship-card {
    font-size: 1.2rem;
    border: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    box-shadow: none;
    /* margin-inline-start: 5.5rem; */
    /* margin-inline-end: 5.5rem; */
}

.relationship-inline-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.relationship-leadin-text {
    font-weight: 600;
}

.relationship-path-builder {
    display: flex;
}

.relationship-inline-close {
    margin-inline-start: auto;
}

.relationship-message {
    flex: 1 1 auto;
}
</style>
