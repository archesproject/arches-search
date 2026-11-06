<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "openvue/message";
import Select from "openvue/select";

import PathBuilder from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/PathBuilder.vue";
import { isRelationshipComplete } from "@/arches_search/AdvancedSearch/utils/query-builder.ts";

import {
    QUANTIFIER_ALL,
    QUANTIFIER_ANY,
    QUANTIFIER_NONE,
} from "@/arches_search/AdvancedSearch/types.ts";

import type { Ref } from "vue";
import type {
    GraphModel,
    PathSelection,
    RelatableNodesTreeForGraphPairResponse,
    RelatableNodesTreeResponse,
    RelationshipBlock,
} from "@/arches_search/AdvancedSearch/types.ts";

const UPDATE_RELATIONSHIP_EVENT = "update:relationship" as const;
const UPDATE_INNER_GRAPH_SLUG_EVENT = "update:innerGraphSlug" as const;

const { relationship, anchorGraphSlug, innerGraphSlug } = defineProps<{
    relationship: RelationshipBlock;
    anchorGraphSlug: string;
    innerGraphSlug: string;
}>();

const emit = defineEmits<{
    (
        event: typeof UPDATE_RELATIONSHIP_EVENT,
        relationship: RelationshipBlock,
    ): void;
    (event: typeof UPDATE_INNER_GRAPH_SLUG_EVENT, innerGraphSlug: string): void;
}>();

const graphs = inject<Ref<GraphModel[]>>("graphs")!;
const getRelatableNodesTreeForGraphId = inject<
    (graphId: string) => Promise<RelatableNodesTreeResponse>
>("getRelatableNodesTreeForGraphId")!;
const getRelatableNodesTreeForGraphPair = inject<
    (
        graphId: string,
        otherGraphId: string,
    ) => Promise<RelatableNodesTreeForGraphPairResponse>
>("getRelatableNodesTreeForGraphPair")!;

const { $gettext } = useGettext();

const isLoadingRelatableTree = ref(false);
const relatableTreeError = ref<Error | null>(null);

const relatableNodesTree = ref<RelatableNodesTreeResponse | null>(null);

const pairwiseTreeError = ref<Error | null>(null);

const pairwiseNodesTree = ref<RelatableNodesTreeForGraphPairResponse | null>(
    null,
);

const anchorGraph = computed<GraphModel | undefined>(() =>
    graphs.value.find((graphModel) => graphModel.slug === anchorGraphSlug),
);

const innerGraph = computed<GraphModel | undefined>(() =>
    graphs.value.find((graphModel) => graphModel.slug === innerGraphSlug),
);

// A saved target that is no longer offered is still listed, so it shows.
const relatableGraphOptions = computed<{ label: string; value: string }[]>(
    () => {
        const options = (relatableNodesTree.value?.relatable_graphs ?? []).map(
            (graph) => ({ label: graph.name, value: graph.slug }),
        );
        const isTargetOffered = options.some(
            (option) => option.value === innerGraphSlug,
        );
        if (innerGraphSlug && !isTargetOffered) {
            options.push({
                label: innerGraph.value?.name ?? innerGraphSlug,
                value: innerGraphSlug,
            });
        }
        return options.sort((left, right) =>
            left.label.localeCompare(right.label),
        );
    },
);

const traversalQuantifierOptions = computed<
    { label: string; value: RelationshipBlock["traversal_quantifier"] }[]
>(() => [
    {
        label: $gettext("at least one related record matches"),
        value: QUANTIFIER_ANY,
    },
    {
        label: $gettext("every related record matches"),
        value: QUANTIFIER_ALL,
    },
]);

const hasChosenLink = computed<boolean>(() =>
    isRelationshipComplete(innerGraphSlug, relationship),
);

const isTraversalQuantifierShown = computed<boolean>(
    () =>
        hasChosenLink.value &&
        relationship.traversal_quantifier !== QUANTIFIER_NONE,
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

watch(() => anchorGraphSlug, loadRelatableTree, { immediate: true });

watch(
    () => [anchorGraphSlug, innerGraphSlug] as const,
    async () => {
        await loadPairwiseNodesTree();
    },
    { immediate: true },
);

// A saved target that is not among the related models offered is kept, not
// cleared: clearing it would also drop every condition on the related records.
async function loadRelatableTree(): Promise<void> {
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
        if (!innerGraphSlug && options.length === 1) {
            emit(UPDATE_INNER_GRAPH_SLUG_EVENT, options[0].value);
        }
    } catch (error) {
        relatableTreeError.value = error as Error;
        relatableNodesTree.value = null;
    } finally {
        isLoadingRelatableTree.value = false;
    }
}

async function loadPairwiseNodesTree(): Promise<void> {
    pairwiseTreeError.value = null;

    const graphId = anchorGraph.value?.graphid;
    const otherGraphId = innerGraph.value?.graphid;

    if (!graphId || !otherGraphId) {
        pairwiseNodesTree.value = null;
        return;
    }

    try {
        const pairwiseTree = await getRelatableNodesTreeForGraphPair(
            graphId,
            otherGraphId,
        );
        if (innerGraph.value?.graphid === otherGraphId) {
            pairwiseNodesTree.value = pairwiseTree;
        }
    } catch (error) {
        if (innerGraph.value?.graphid === otherGraphId) {
            pairwiseTreeError.value = error as Error;
            pairwiseNodesTree.value = null;
        }
    }
}

function onUpdateSelectedNode(nextSelectedNode: PathSelection | null): void {
    if (!nextSelectedNode) {
        emit(UPDATE_RELATIONSHIP_EVENT, {
            ...relationship,
            path: {
                type: relationship.path.type,
                graph_slug: "",
                node_alias: "",
            },
        });
        return;
    }
    emit(UPDATE_RELATIONSHIP_EVENT, {
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
    emit(UPDATE_RELATIONSHIP_EVENT, {
        ...relationship,
        traversal_quantifier: nextQuantifier,
    });
}

function onSelectInnerGraph(nextInnerGraphSlug: string): void {
    emit(UPDATE_INNER_GRAPH_SLUG_EVENT, nextInnerGraphSlug);
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
                option-label="label"
                option-value="value"
                :model-value="innerGraphSlug"
                :options="relatableGraphOptions"
                :filter="true"
                :disabled="isLoadingRelatableTree"
                :placeholder="$gettext('Select a model')"
                :aria-label="$gettext('Related model')"
                @update:model-value="onSelectInnerGraph"
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
