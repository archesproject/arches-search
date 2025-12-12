<script setup lang="ts">
import { computed, inject, ref, watch, watchEffect } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Card from "primevue/card";
import Message from "primevue/message";
import Select from "primevue/select";
import TreeSelect from "primevue/treeselect";

import type {
    GraphModel,
    GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type RelationshipState = NonNullable<GroupPayload["relationship"]>;
type TraversalQuantifier = RelationshipState["traversal_quantifiers"][number];

type RelationshipPathSequence = readonly (readonly [string, string])[];

type TreeSelectNode = {
    key: string;
    label: string;
    children?: TreeSelectNode[];
    leaf?: boolean;
    data?: {
        id?: string;
        graph_id?: string;
        alias?: string | null;
        name?: string;
        description?: string;
        datatype?: string | null;
        slug?: string | null;
        [key: string]: unknown;
    };
};

type RelatableNodesTreeResponse = {
    target_graph_id: string;
    options: TreeSelectNode[];
};

type SelectionKeyState =
    | boolean
    | { checked?: boolean; partialChecked?: boolean };

type TreeSelectSelectionKeys = Record<string, SelectionKeyState>;

const TRAVERSAL_QUANTIFIER_ANY = "ANY";
const TRAVERSAL_QUANTIFIER_ALL = "ALL";
const TRAVERSAL_QUANTIFIER_NONE = "NONE";

const emit = defineEmits<{
    (event: "update:relationship", value: RelationshipState | null): void;
}>();

const { relationship, anchorGraphSlug, innerGraphSlug, isRoot } = defineProps<{
    relationship: RelationshipState;
    anchorGraphSlug: string;
    innerGraphSlug: string;
    isRoot?: boolean;
}>();

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;
const getRelatableNodesTreeForGraphId = inject<
    (graphId: string) => Promise<RelatableNodesTreeResponse>
>("getRelatableNodesTreeForGraphId")!;

const hasCompatibleRelationshipNodes = ref(true);
const isLoadingRelatableTree = ref(false);

const relatableNodesTreeResponse = ref<RelatableNodesTreeResponse | null>(null);

const selectedSelectionKeys = ref<TreeSelectSelectionKeys>({});

const selectedTreeNodeKey = computed<string | null>(() => {
    const selectionKeysObject = selectedSelectionKeys.value;

    for (const [possibleKey, selectionState] of Object.entries(
        selectionKeysObject,
    )) {
        if (selectionState === true) {
            return possibleKey;
        }

        if (
            typeof selectionState === "object" &&
            selectionState !== null &&
            selectionState.checked === true
        ) {
            return possibleKey;
        }
    }

    return null;
});

const anchorGraph = computed<GraphModel | undefined>(() => {
    return graphs.value.find(
        (graphModel) => graphModel.slug === anchorGraphSlug,
    );
});

const anchorGraphId = computed<string | null>(() => {
    return anchorGraph.value?.graphid
        ? String(anchorGraph.value.graphid)
        : null;
});

const anchorGraphName = computed<string>(() => {
    return anchorGraph.value?.name ? String(anchorGraph.value.name) : "";
});

const relationshipLeadinText = computed<string>(() => {
    return $gettext("Related to %{outer} by", {
        outer: anchorGraphName.value,
    });
});

const graphIdToSlug = computed<Record<string, string>>(() => {
    const mapping: Record<string, string> = {};

    for (const graphModel of graphs.value) {
        if (!graphModel.graphid || !graphModel.slug) {
            continue;
        }

        mapping[String(graphModel.graphid)] = String(graphModel.slug);
    }

    return mapping;
});

const graphIdToLabel = computed<Record<string, string>>(() => {
    const mapping: Record<string, string> = {};

    for (const graphModel of graphs.value) {
        if (!graphModel.graphid) {
            continue;
        }

        const graphLabel =
            (graphModel.name ? String(graphModel.name) : "") ||
            (graphModel.slug ? String(graphModel.slug) : "");

        if (!graphLabel) {
            continue;
        }

        mapping[String(graphModel.graphid)] = graphLabel;
    }

    return mapping;
});

type TreeIndex = {
    nodeByKey: Record<string, TreeSelectNode>;
    parentKeyByKey: Record<string, string | null>;
    nodeKeyByGraphSlugAndAlias: Record<string, string>;
};

const treeIndex = computed<TreeIndex>(() => {
    const nodeByKey: Record<string, TreeSelectNode> = {};
    const parentKeyByKey: Record<string, string | null> = {};
    const nodeKeyByGraphSlugAndAlias: Record<string, string> = {};

    const rootOptions = relatableNodesTreeResponse.value?.options ?? [];

    const stack: Array<{ node: TreeSelectNode; parentKey: string | null }> = [];
    for (const rootNode of rootOptions) {
        stack.push({ node: rootNode, parentKey: null });
    }

    while (stack.length) {
        const stackItem = stack.pop();
        if (!stackItem) {
            continue;
        }

        const currentNode = stackItem.node;
        const parentKey = stackItem.parentKey;

        nodeByKey[currentNode.key] = currentNode;
        parentKeyByKey[currentNode.key] = parentKey;

        const dataGraphId = currentNode.data?.graph_id
            ? String(currentNode.data.graph_id)
            : "";
        const nodeAlias = currentNode.data?.alias
            ? String(currentNode.data.alias)
            : "";

        if (dataGraphId && nodeAlias) {
            const graphSlug = graphIdToSlug.value[dataGraphId] ?? "";
            if (graphSlug) {
                nodeKeyByGraphSlugAndAlias[`${graphSlug}::${nodeAlias}`] =
                    currentNode.key;
            }
        }

        const childNodes = currentNode.children ?? [];
        for (const childNode of childNodes) {
            stack.push({ node: childNode, parentKey: currentNode.key });
        }
    }

    return { nodeByKey, parentKeyByKey, nodeKeyByGraphSlugAndAlias };
});

const hasSelectedRelationshipPath = computed<boolean>(() => {
    return Boolean(selectedTreeNodeKey.value);
});

const traversalQuantifierOptions = computed<{ label: string; value: string }[]>(
    () => {
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
    },
);

const currentTraversalQuantifier = computed<string>(() => {
    const firstQuantifier = relationship.traversal_quantifiers[0];
    if (!firstQuantifier) {
        return TRAVERSAL_QUANTIFIER_ANY;
    }
    return firstQuantifier;
});

watchEffect(async () => {
    const currentAnchorGraphId = anchorGraphId.value;
    if (!currentAnchorGraphId) {
        relatableNodesTreeResponse.value = null;
        hasCompatibleRelationshipNodes.value = true;
        selectedSelectionKeys.value = {};
        return;
    }

    try {
        isLoadingRelatableTree.value = true;
        const response =
            await getRelatableNodesTreeForGraphId(currentAnchorGraphId);
        relatableNodesTreeResponse.value = response;

        hasCompatibleRelationshipNodes.value =
            (response.options ?? []).length > 0;
        if (!hasCompatibleRelationshipNodes.value) {
            selectedSelectionKeys.value = {};
        }
    } finally {
        isLoadingRelatableTree.value = false;
    }
});

watch(
    () => relationship.path,
    (nextPath) => {
        const lastSegment = nextPath?.[nextPath.length - 1];
        if (!lastSegment) {
            selectedSelectionKeys.value = {};
            return;
        }

        const segmentGraphSlug = String(lastSegment[0] ?? "").trim();
        const segmentNodeAlias = String(lastSegment[1] ?? "").trim();

        if (!segmentGraphSlug || !segmentNodeAlias) {
            selectedSelectionKeys.value = {};
            return;
        }

        const expectedKey =
            treeIndex.value.nodeKeyByGraphSlugAndAlias[
                `${segmentGraphSlug}::${segmentNodeAlias}`
            ] ?? null;

        if (!expectedKey) {
            selectedSelectionKeys.value = {};
            return;
        }

        const currentSelectedKey = selectedTreeNodeKey.value;
        if (currentSelectedKey === expectedKey) {
            return;
        }

        selectedSelectionKeys.value = { [expectedKey]: { checked: true } };
    },
    { deep: true },
);

function onChangeTraversalQuantifier(nextQuantifierRaw: string): void {
    const normalizedQuantifier = String(nextQuantifierRaw).toUpperCase();

    let safeQuantifierString = TRAVERSAL_QUANTIFIER_ANY;

    if (normalizedQuantifier === TRAVERSAL_QUANTIFIER_ALL) {
        safeQuantifierString = TRAVERSAL_QUANTIFIER_ALL;
    } else if (normalizedQuantifier === TRAVERSAL_QUANTIFIER_NONE) {
        safeQuantifierString = TRAVERSAL_QUANTIFIER_NONE;
    }

    const safeQuantifier = safeQuantifierString as TraversalQuantifier;

    const updatedRelationship: RelationshipState = {
        ...relationship,
        traversal_quantifiers: [safeQuantifier],
    };

    emit("update:relationship", updatedRelationship);
}

function normalizeSelectionKeys(
    nextModelValue: unknown,
): TreeSelectSelectionKeys {
    if (!nextModelValue) {
        return {};
    }

    if (typeof nextModelValue === "string") {
        const trimmedKey = nextModelValue.trim();
        return trimmedKey ? { [trimmedKey]: { checked: true } } : {};
    }

    if (typeof nextModelValue === "object") {
        return nextModelValue as TreeSelectSelectionKeys;
    }

    return {};
}

function buildPathSequenceFromSelectedKey(
    nextSelectedKey: string,
): RelationshipPathSequence {
    const keysInChainFromLeafToRoot: string[] = [];
    let currentKey: string | null = nextSelectedKey;

    while (currentKey) {
        keysInChainFromLeafToRoot.push(currentKey);
        currentKey = treeIndex.value.parentKeyByKey[currentKey] ?? null;
    }

    const keysInChainFromRootToLeaf = keysInChainFromLeafToRoot.reverse();

    const segments: Array<[string, string]> = [];

    for (const keyInChain of keysInChainFromRootToLeaf) {
        if (keyInChain.startsWith("graph:")) {
            continue;
        }

        const node = treeIndex.value.nodeByKey[keyInChain];
        if (!node) {
            continue;
        }

        const nodeGraphId = node.data?.graph_id
            ? String(node.data.graph_id)
            : "";
        const nodeGraphSlug = nodeGraphId
            ? graphIdToSlug.value[nodeGraphId] ?? ""
            : "";
        const nodeAlias = node.data?.alias ? String(node.data.alias) : "";

        if (!nodeGraphSlug || !nodeAlias) {
            continue;
        }

        segments.push([nodeGraphSlug, nodeAlias]);
    }

    return segments;
}

function deriveIsInverseFromPathSequence(
    nextPathSequence: RelationshipPathSequence,
): boolean {
    const firstSegment = nextPathSequence[0];
    if (!firstSegment) {
        return relationship.is_inverse;
    }

    const firstGraphSlug = String(firstSegment[0] ?? "");
    if (!firstGraphSlug || !anchorGraphSlug) {
        return relationship.is_inverse;
    }

    return firstGraphSlug !== anchorGraphSlug;
}

function onUpdateSelectionKeys(nextModelValue: unknown): void {
    const normalizedSelectionKeys = normalizeSelectionKeys(nextModelValue);
    selectedSelectionKeys.value = normalizedSelectionKeys;

    const nextSelectedKey = selectedTreeNodeKey.value;

    if (!nextSelectedKey) {
        emit("update:relationship", null);
        return;
    }

    if (nextSelectedKey.startsWith("graph:")) {
        selectedSelectionKeys.value = {};
        return;
    }

    const nextPathSequence = buildPathSequenceFromSelectedKey(nextSelectedKey);
    if (nextPathSequence.length === 0) {
        selectedSelectionKeys.value = {};
        return;
    }

    const nextIsInverse = deriveIsInverseFromPathSequence(nextPathSequence);

    const updatedRelationship: RelationshipState = {
        ...relationship,
        path: nextPathSequence.map(
            (segment) => [segment[0], segment[1]] as [string, string],
        ),
        is_inverse: nextIsInverse,
    };

    emit("update:relationship", updatedRelationship);
}

function getGraphLabelPrefixForTreeNode(
    treeNode: TreeSelectNode | undefined,
): string {
    if (!treeNode) {
        return "";
    }

    const nodeGraphId = treeNode.data?.graph_id
        ? String(treeNode.data.graph_id)
        : "";
    if (!nodeGraphId) {
        return "";
    }

    const graphLabel = graphIdToLabel.value[nodeGraphId] ?? "";
    if (!graphLabel) {
        return "";
    }

    return `${graphLabel}: `;
}

function onCloseClick(): void {
    emit("update:relationship", null);
}

void innerGraphSlug;
</script>

<template>
    <Card
        class="relationship-card"
        :style="{
            marginInlineEnd: isRoot ? 0 : '3rem',
        }"
    >
        <template #content>
            <div class="relationship-inline-row">
                <span class="relationship-leadin-text">
                    {{ relationshipLeadinText }}
                </span>

                <TreeSelect
                    v-show="hasCompatibleRelationshipNodes"
                    :model-value="selectedSelectionKeys"
                    :options="relatableNodesTreeResponse?.options ?? []"
                    selection-mode="single"
                    :disabled="isLoadingRelatableTree || !anchorGraphId"
                    class="relationship-tree-select"
                    :placeholder="$gettext('Choose relationship')"
                    :aria-label="$gettext('Relationship path')"
                    @update:model-value="onUpdateSelectionKeys"
                >
                    <template #value="valueSlotProps">
                        <span
                            v-if="
                                valueSlotProps.value &&
                                valueSlotProps.value.length > 0
                            "
                        >
                            {{
                                getGraphLabelPrefixForTreeNode(
                                    valueSlotProps.value[0] as TreeSelectNode,
                                )
                            }}
                            {{ valueSlotProps.value[0].label }}
                        </span>
                        <span v-else>
                            {{ valueSlotProps.placeholder }}
                        </span>
                    </template>
                </TreeSelect>

                <Select
                    v-if="
                        hasCompatibleRelationshipNodes &&
                        hasSelectedRelationshipPath
                    "
                    :model-value="currentTraversalQuantifier"
                    :options="traversalQuantifierOptions"
                    option-label="label"
                    option-value="value"
                    class="relationship-quantifier-select"
                    :placeholder="$gettext('Match requirement')"
                    :aria-label="$gettext('Relationship match requirement')"
                    :title="
                        $gettext(
                            'Decide how many related records must match for this relationship to be considered true.',
                        )
                    "
                    @update:model-value="onChangeTraversalQuantifier"
                />

                <Message
                    v-if="!hasCompatibleRelationshipNodes"
                    severity="error"
                    class="relationship-error-message"
                >
                    {{
                        $gettext(
                            "No compatible relationship nodes exist for the selected record type.",
                        )
                    }}
                </Message>

                <Button
                    variant="text"
                    severity="danger"
                    icon="pi pi-times"
                    class="relationship-inline-close"
                    :aria-label="$gettext('Remove relationship')"
                    @click="onCloseClick"
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
    margin-top: 1rem;
}

.relationship-inline-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    font-size: 1.2rem;
}

.relationship-leadin-text {
    font-weight: 600;
}

.relationship-inline-close {
    margin-inline-start: auto;
}

.relationship-error-message {
    flex: 1 1 auto;
}
</style>
