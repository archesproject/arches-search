<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Card from "primevue/card";
import Message from "primevue/message";
import Select from "primevue/select";

import PathBuilder from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/PathBuilder.vue";

import type {
    GraphModel,
    PathSelection,
    RelatableNodesTreeForGraphPairResponse,
    RelatableNodesTreeResponse,
    RelationshipBlock,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext, $pgettext } = useGettext();

const TRAVERSAL_QUANTIFIER_ANY = "ANY";
const TRAVERSAL_QUANTIFIER_ALL = "ALL";
const TRAVERSAL_QUANTIFIER_NONE = "NONE";

const emit = defineEmits<{
    "update:relationship": [RelationshipBlock | null];
    "update:innerGraphSlug": [string];
}>();

const { relationship, anchorGraphSlug, innerGraphSlug } = defineProps<{
    relationship: RelationshipBlock;
    anchorGraphSlug: string;
    innerGraphSlug: string;
}>();

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;
const getRelatableNodesTreeForGraphId = inject<
    (graphId: string) => Promise<RelatableNodesTreeResponse>
>("getRelatableNodesTreeForGraphId")!;
const getRelatableNodesTreeForGraphPair = inject<
    (
        graphId: string,
        otherGraphId: string,
    ) => Promise<RelatableNodesTreeForGraphPairResponse>
>("getRelatableNodesTreeForGraphPair")!;

const isLoadingRelatableTree = ref(false);
const relatableTreeError = ref<Error | null>(null);

const relatableNodesTree = ref<RelatableNodesTreeResponse | null>(null);

const isLoadingPairwiseTree = ref(false);
const pairwiseTreeError = ref<Error | null>(null);

const pairwiseNodesTree = ref<RelatableNodesTreeForGraphPairResponse | null>(
    null,
);

const anchorGraph = computed(() => {
    return graphs.value.find(
        (graphModel) => graphModel.slug === anchorGraphSlug,
    );
});

const innerGraph = computed(() => {
    return graphs.value.find(
        (graphModel) => graphModel.slug === innerGraphSlug,
    );
});

const tagText = computed(() => {
    const name = anchorGraph.value?.name;

    if (name) {
        return $gettext("Relate %{name} to", { name });
    }
    return $gettext("Relate to");
});

const relatableGraphOptions = computed(() =>
    (relatableNodesTree.value?.relatable_graphs ?? [])
        .map((graph) => ({ label: graph.name, value: graph.slug }))
        .sort((left, right) => left.label.localeCompare(right.label)),
);

const traversalQuantifierOptions = computed(() => [
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
]);

const currentTraversalQuantifier = computed(() => {
    return relationship.traversal_quantifier ?? TRAVERSAL_QUANTIFIER_ANY;
});

const selectedRelationshipNode = computed<PathSelection | null>(() => {
    if (!relationship.path.graph_slug || !relationship.path.node_alias) {
        return null;
    }

    return {
        graph_slug: relationship.path.graph_slug,
        node_alias: relationship.path.node_alias,
        is_inverse: relationship.is_inverse,
    };
});

watch(
    () => anchorGraphSlug,
    async (_next, previousSlug) => {
        if (previousSlug) {
            if (innerGraphSlug) {
                emit("update:innerGraphSlug", "");
            }
            if (relationship.path.graph_slug || relationship.path.node_alias) {
                emitPathReset();
            }
        }
        await loadRelatableTree();
    },
    { immediate: true },
);

watch(
    () => innerGraphSlug,
    (_next, previousSlug) => {
        if (!previousSlug) {
            return;
        }
        emitPathReset();
    },
);

watch(
    () => [anchorGraphSlug, innerGraphSlug] as const,
    async () => {
        await loadPairwiseNodesTree();
    },
    { immediate: true },
);

async function loadRelatableTree() {
    isLoadingRelatableTree.value = true;
    relatableTreeError.value = null;

    const graphId = anchorGraph.value?.graphid;

    if (!graphId) {
        relatableNodesTree.value = null;
        isLoadingRelatableTree.value = false;
        return;
    }

    try {
        relatableNodesTree.value =
            await getRelatableNodesTreeForGraphId(graphId);

        const options = relatableGraphOptions.value;

        if (!innerGraphSlug) {
            if (options.length === 1) {
                emit("update:innerGraphSlug", options[0]!.value);
            }
        } else if (!options.some((option) => option.value === innerGraphSlug)) {
            emit("update:innerGraphSlug", "");

            if (relationship.path.graph_slug || relationship.path.node_alias) {
                emitPathReset();
            }
        }
    } catch (error) {
        relatableTreeError.value = error as Error;
        relatableNodesTree.value = null;
    } finally {
        isLoadingRelatableTree.value = false;
    }
}

async function loadPairwiseNodesTree(): Promise<void> {
    isLoadingPairwiseTree.value = true;
    pairwiseTreeError.value = null;

    const graphId = anchorGraph.value?.graphid;
    const otherGraphId = innerGraph.value?.graphid;

    if (!graphId || !otherGraphId) {
        pairwiseNodesTree.value = null;
        isLoadingPairwiseTree.value = false;
        return;
    }

    try {
        pairwiseNodesTree.value = await getRelatableNodesTreeForGraphPair(
            graphId,
            otherGraphId,
        );
    } catch (error) {
        pairwiseTreeError.value = error as Error;
        pairwiseNodesTree.value = null;
    } finally {
        isLoadingPairwiseTree.value = false;
    }
}

function emitPathReset(): void {
    emit("update:relationship", {
        ...relationship,
        path: {
            type: relationship.path.type,
            graph_slug: "",
            node_alias: "",
        },
    });
}

function onUpdateSelectedNode(nextSelectedNode: PathSelection | null): void {
    if (!nextSelectedNode) {
        emitPathReset();
        return;
    }
    emit("update:relationship", {
        ...relationship,
        path: {
            type: relationship.path.type,
            graph_slug: nextSelectedNode.graph_slug,
            node_alias: nextSelectedNode.node_alias,
        },
        is_inverse: nextSelectedNode.is_inverse ?? false,
    });
}

function onChangeTraversalQuantifier(nextQuantifier: string): void {
    emit("update:relationship", {
        ...relationship,
        traversal_quantifier:
            nextQuantifier as RelationshipBlock["traversal_quantifier"],
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
                    {{ tagText }}
                </span>

                <Select
                    v-if="relatableGraphOptions.length > 0"
                    :model-value="innerGraphSlug"
                    :options="relatableGraphOptions"
                    :filter="true"
                    option-label="label"
                    option-value="value"
                    class="relationship-related-graph-select"
                    :disabled="isLoadingRelatableTree"
                    :placeholder="$gettext('Related record type')"
                    :aria-label="$gettext('Related record type')"
                    @update:model-value="emit('update:innerGraphSlug', $event)"
                />

                <span
                    v-if="innerGraphSlug"
                    class="relationship-leadin-text"
                >
                    {{
                        $pgettext(
                            'relationship editor: "Relate [type] to [type] via [field] and [quantifier]"',
                            "via",
                        )
                    }}
                </span>

                <Message
                    v-if="innerGraphSlug && pairwiseTreeError"
                    severity="error"
                    class="relationship-message"
                >
                    {{ pairwiseTreeError.message }}
                </Message>

                <div
                    v-else-if="innerGraphSlug"
                    class="relationship-path-builder"
                >
                    <PathBuilder
                        :graph-options-tree="pairwiseNodesTree?.options ?? []"
                        :selected-node="selectedRelationshipNode"
                        :should-prepend-graph-name="true"
                        @update:selected-node="onUpdateSelectedNode"
                    />
                </div>

                <span
                    v-if="
                        innerGraphSlug &&
                        relationship.path.graph_slug &&
                        relationship.path.node_alias
                    "
                    class="relationship-leadin-text"
                >
                    {{
                        $pgettext(
                            'relationship editor: "Relate [type] to [type] via [field] and [quantifier]"',
                            "and",
                        )
                    }}
                </span>

                <Select
                    v-if="
                        innerGraphSlug &&
                        relationship.path.graph_slug &&
                        relationship.path.node_alias
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
