<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";

import { useGettext } from "vue3-gettext";

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

const props = defineProps<{
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

const anchorGraph = computed<GraphModel | null>(() => {
    return (
        graphs.value.find(
            (graphModel) => graphModel.slug === props.anchorGraphSlug,
        ) ?? null
    );
});

const relationshipLeadinText = computed(() => {
    const anchorGraphName = anchorGraph.value?.name ?? "";
    if (!anchorGraphName) {
        return $gettext("Relate to");
    }
    return $gettext("Relate %{outer} to", { outer: anchorGraphName });
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
    return props.innerGraphSlug.length > 0;
});

const hasSelectedRelationshipPath = computed(() => {
    return props.relationship.path.length > 0;
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
    return (
        props.relationship.traversal_quantifiers[0] ?? TRAVERSAL_QUANTIFIER_ANY
    );
});

const pathSequenceForPathBuilder = computed<PathSequence>(() => {
    const firstSegment = props.relationship.path[0];
    if (!firstSegment) {
        return [];
    }
    return [[firstSegment[0], firstSegment[1]]];
});

watch(
    () => props.anchorGraphSlug,
    (nextAnchorGraphSlug, previousAnchorGraphSlug) => {
        if (!previousAnchorGraphSlug) {
            return;
        }

        if (nextAnchorGraphSlug === previousAnchorGraphSlug) {
            return;
        }

        if (props.innerGraphSlug) {
            emit("update:innerGraphSlug", "");
        }

        if (props.relationship.path.length > 0) {
            emit("update:relationship", { ...props.relationship, path: [] });
        }
    },
);

watch(
    () => anchorGraph.value?.graphid ?? "",
    async (anchorGraphId) => {
        isLoadingRelatableTree.value = true;
        hasLoadedRelatableTree.value = false;
        relatableTreeError.value = null;
        relatableNodesTreeResponse.value = null;

        if (!anchorGraphId) {
            isLoadingRelatableTree.value = false;
            hasLoadedRelatableTree.value = true;
            return;
        }

        try {
            relatableNodesTreeResponse.value =
                await getRelatableNodesTreeForGraphId(anchorGraphId);
        } catch (caughtError) {
            relatableTreeError.value = caughtError as Error;
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
        if (!props.innerGraphSlug) {
            if (options.length === 1) {
                emit("update:innerGraphSlug", options[0]!.value);
            }
            return;
        }

        const innerGraphSlugIsStillValid = options.some(
            (option) => option.value === props.innerGraphSlug,
        );

        if (!innerGraphSlugIsStillValid) {
            emit("update:innerGraphSlug", "");
            if (props.relationship.path.length > 0) {
                emit("update:relationship", {
                    ...props.relationship,
                    path: [],
                });
            }
        }
    },
    { immediate: true },
);

watch(
    () => props.innerGraphSlug,
    (nextInnerGraphSlug, previousInnerGraphSlug) => {
        if (!previousInnerGraphSlug) {
            return;
        }

        if (nextInnerGraphSlug === previousInnerGraphSlug) {
            return;
        }

        emit("update:relationship", { ...props.relationship, path: [] });
    },
);

function onChangeRelatedGraphSlug(nextGraphSlug: string): void {
    emit("update:innerGraphSlug", nextGraphSlug);
}

function onUpdatePathSequence(nextPathSequence: PathSequence): void {
    if (nextPathSequence.length === 0) {
        emit("update:relationship", { ...props.relationship, path: [] });
        return;
    }

    const [firstGraphSlug, firstNodeAlias] = nextPathSequence[0]!;

    emit("update:relationship", {
        ...props.relationship,
        path: [[firstGraphSlug, firstNodeAlias]],
        is_inverse: firstGraphSlug !== props.anchorGraphSlug,
    });
}

function onChangeTraversalQuantifier(nextQuantifier: string): void {
    emit("update:relationship", {
        ...props.relationship,
        traversal_quantifiers: [nextQuantifier as TraversalQuantifier],
    });
}
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
                    :model-value="props.innerGraphSlug"
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
                        :graph-slugs="[
                            props.anchorGraphSlug,
                            props.innerGraphSlug,
                        ]"
                        :path-sequence="pathSequenceForPathBuilder"
                        :restrict-to-resource-instance-datatypes="true"
                        :relationship-between-graphs="[
                            props.anchorGraphSlug,
                            props.innerGraphSlug,
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

.relationship-message {
    flex: 1 1 auto;
}
</style>
