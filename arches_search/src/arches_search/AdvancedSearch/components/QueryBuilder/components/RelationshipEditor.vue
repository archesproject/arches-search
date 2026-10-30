<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "openvue/message";
import Select from "openvue/select";

import PathBuilder from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/PathBuilder.vue";

import type {
    GraphModel,
    PathSelection,
    RelatableNodesTreeForGraphPairResponse,
    RelatableNodesTreeResponse,
    RelationshipBlock,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const TRAVERSAL_QUANTIFIER_ANY = "ANY";
const TRAVERSAL_QUANTIFIER_ALL = "ALL";
const TRAVERSAL_QUANTIFIER_NONE = "NONE";

const emit = defineEmits<{
    "update:relationship": [RelationshipBlock];
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

const relatableGraphOptions = computed(() =>
    (relatableNodesTree.value?.relatable_graphs ?? [])
        .map((graph) => ({ label: graph.name, value: graph.slug }))
        .sort((left, right) => left.label.localeCompare(right.label)),
);

const traversalQuantifierOptions = computed(() => [
    {
        label: $gettext("at least one related record matches"),
        value: TRAVERSAL_QUANTIFIER_ANY,
    },
    {
        label: $gettext("every related record matches"),
        value: TRAVERSAL_QUANTIFIER_ALL,
    },
]);

const hasChosenLink = computed<boolean>(() =>
    Boolean(
        innerGraphSlug &&
            relationship.path.graph_slug &&
            relationship.path.node_alias,
    ),
);

const isTraversalQuantifierShown = computed<boolean>(
    () =>
        hasChosenLink.value &&
        relationship.traversal_quantifier !== TRAVERSAL_QUANTIFIER_NONE,
);

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

function onChangeTraversalQuantifier(
    nextQuantifier: RelationshipBlock["traversal_quantifier"],
): void {
    emit("update:relationship", {
        ...relationship,
        traversal_quantifier: nextQuantifier,
    });
}
</script>

<template>
    <div class="relationship-editor">
        <Message
            v-if="relatableTreeError"
            severity="error"
            size="small"
        >
            {{ relatableTreeError.message }}
        </Message>

        <template v-else>
            <Select
                v-if="relatableGraphOptions.length > 0"
                class="relationship-editor-model"
                option-label="label"
                option-value="value"
                :model-value="innerGraphSlug"
                :options="relatableGraphOptions"
                :filter="true"
                :disabled="isLoadingRelatableTree"
                :placeholder="$gettext('Select a model')"
                :aria-label="$gettext('Related model')"
                @update:model-value="emit('update:innerGraphSlug', $event)"
            />

            <template v-if="innerGraphSlug">
                <span class="relationship-editor-word">
                    {{
                        $pgettext(
                            "Query condition: 'Related to a [model] via [field]'",
                            "via",
                        )
                    }}
                </span>

                <Message
                    v-if="pairwiseTreeError"
                    severity="error"
                    size="small"
                >
                    {{ pairwiseTreeError.message }}
                </Message>

                <PathBuilder
                    v-else
                    :graph-options-tree="pairwiseNodesTree?.options ?? []"
                    :selected-node="selectedRelationshipNode"
                    :should-prepend-graph-name="true"
                    @update:selected-node="onUpdateSelectedNode"
                />
            </template>

            <Select
                v-if="isTraversalQuantifierShown"
                class="relationship-editor-quantifier"
                option-label="label"
                option-value="value"
                :model-value="relationship.traversal_quantifier"
                :options="traversalQuantifierOptions"
                :aria-label="$gettext('Which related records must match')"
                @update:model-value="onChangeTraversalQuantifier"
            />
        </template>
    </div>
</template>

<style scoped>
.relationship-editor {
    display: contents;
    font-size: 1.2rem;
}

.relationship-editor :deep(.p-select-label) {
    font-size: 1.2rem;
}

.relationship-editor .relationship-editor-word {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    white-space: nowrap;
}
</style>
