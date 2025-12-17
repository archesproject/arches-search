<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import TreeSelect from "primevue/treeselect";

import type { GraphModel } from "@/arches_search/AdvancedSearch/types.ts";

type NodeSummary = {
    id: string;
    alias: string;
    name: string;
    datatype: string;
    sortorder: number;
    card_x_node_x_widget_label: string;
    semantic_parent_id: string | null;
    graph_slug?: string;
    config?: unknown;
    [key: string]: unknown;
};

type TreeNodeOption = {
    key: string;
    label: string;
    data: NodeSummary;
    children: TreeNodeOption[];
    selectable?: boolean;
};

type PathSequence = [string, string][];

type RelationshipGraphPair = readonly [string, string];

const { $gettext } = useGettext();

const getNodesForGraphId =
    inject<(graphId: string) => Promise<NodeSummary[]>>("getNodesForGraphId")!;

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;

const emit = defineEmits<{
    (event: "update:pathSequence", value: PathSequence): void;
    (event: "compatibleRelationshipNodesChanged", value: boolean): void;
}>();

const props = withDefaults(
    defineProps<{
        graphSlugs: string[];
        pathSequence?: PathSequence;
        relationshipBetweenGraphs?: string[];
        shouldPrependGraphName?: boolean;
        restrictToResourceInstanceDatatypes?: boolean;
    }>(),
    {
        shouldPrependGraphName: false,
        restrictToResourceInstanceDatatypes: false,
    },
);

const isLoading = ref(false);
const configurationError = ref<Error | null>(null);

const nodeOptions = ref<TreeNodeOption[]>([]);
const expandedKeys = ref<Record<string, boolean>>({});
const selectedKeys = ref<Record<string, boolean>>({});

const latestNodeLoadRequestId = ref(0);

const lastEmittedPathSequenceKey = ref<string | null>(null);
const lastEmittedSelectedTreeKey = ref<string | null>(null);

const graphSelectionKey = computed(() => {
    const graphSlugsKey = (props.graphSlugs ?? []).join("|");
    const relationshipGraphSlugsKey = (
        props.relationshipBetweenGraphs ?? []
    ).join("|");
    const datatypeRestrictionKey = props.restrictToResourceInstanceDatatypes
        ? "restricted"
        : "all";
    return `${graphSlugsKey}::${relationshipGraphSlugsKey}::${datatypeRestrictionKey}`;
});

const selectableNodeCount = computed(() => {
    return countSelectableNodes(nodeOptions.value);
});

watch(
    () => graphSelectionKey.value,
    async () => {
        const nextGraphSlugs = props.graphSlugs;

        if (!nextGraphSlugs || nextGraphSlugs.length === 0) {
            nodeOptions.value = [];
            expandedKeys.value = {};
            selectedKeys.value = {};
            lastEmittedPathSequenceKey.value = null;
            lastEmittedSelectedTreeKey.value = null;
            return;
        }

        await loadNodesForGraphSlugs(nextGraphSlugs);
        seedSelectionFromPathSequence();
    },
    { immediate: true },
);

watch(
    () => props.pathSequence,
    () => {
        seedSelectionFromPathSequence();
    },
    { deep: true, immediate: true },
);

watch(
    () => selectableNodeCount.value,
    (nextCount: number) => {
        emit("compatibleRelationshipNodesChanged", nextCount > 0);
    },
    { immediate: true },
);

function countSelectableNodes(treeNodes: TreeNodeOption[]): number {
    let totalSelectableCount = 0;

    function traverse(treeNodeList: TreeNodeOption[]): void {
        for (const treeNode of treeNodeList) {
            if (treeNode.selectable !== false) {
                totalSelectableCount += 1;
            }

            if (treeNode.children.length > 0) {
                traverse(treeNode.children);
            }
        }
    }

    traverse(treeNodes);
    return totalSelectableCount;
}

function deriveRelationshipGraphPairFromSlugs(
    relationshipGraphSlugList?: string[],
): RelationshipGraphPair | undefined {
    if (relationshipGraphSlugList && relationshipGraphSlugList.length > 0) {
        if (relationshipGraphSlugList.length === 1) {
            const onlyGraphSlug = relationshipGraphSlugList[0];
            if (!onlyGraphSlug) {
                return undefined;
            }
            return [onlyGraphSlug, onlyGraphSlug];
        }

        const firstGraphSlug = relationshipGraphSlugList[0];
        const secondGraphSlug = relationshipGraphSlugList[1];

        if (!firstGraphSlug || !secondGraphSlug) {
            return undefined;
        }

        return [firstGraphSlug, secondGraphSlug];
    }

    if (props.graphSlugs && props.graphSlugs.length >= 2) {
        const firstGraphSlug = props.graphSlugs[0];
        const secondGraphSlug = props.graphSlugs[1];

        if (!firstGraphSlug || !secondGraphSlug) {
            return undefined;
        }

        return [firstGraphSlug, secondGraphSlug];
    }

    return undefined;
}

function isResourceInstanceDatatype(datatype: string): boolean {
    return (
        datatype === "resource-instance" ||
        datatype === "resource-instance-list"
    );
}

function doesNodeBridgeRelationshipGraphPair(
    nodeSummary: NodeSummary,
    relationshipGraphPair: RelationshipGraphPair,
): boolean {
    const nodeGraphSlug = nodeSummary.graph_slug;

    if (!nodeGraphSlug) {
        return false;
    }

    const configuredGraphs =
        (nodeSummary.config as { graphs?: { graphid: string }[] } | undefined)
            ?.graphs ?? [];

    if (configuredGraphs.length === 0) {
        return false;
    }

    const [firstGraphSlug, secondGraphSlug] = relationshipGraphPair;

    if (nodeGraphSlug !== firstGraphSlug && nodeGraphSlug !== secondGraphSlug) {
        return false;
    }

    const configuredTargetGraphSlugs = new Set<string>();

    for (const configuredGraph of configuredGraphs) {
        const matchingGraphSummary = graphs.value.find(
            (graphSummary) => graphSummary.graphid === configuredGraph.graphid,
        );

        if (!matchingGraphSummary) {
            continue;
        }

        configuredTargetGraphSlugs.add(matchingGraphSummary.slug);
    }

    if (nodeGraphSlug === firstGraphSlug) {
        return configuredTargetGraphSlugs.has(secondGraphSlug);
    }

    if (nodeGraphSlug === secondGraphSlug) {
        return configuredTargetGraphSlugs.has(firstGraphSlug);
    }

    return false;
}

function isNodeSelectable(
    nodeSummary: NodeSummary,
    relationshipGraphPair: RelationshipGraphPair | undefined,
): boolean {
    if (nodeSummary.datatype === "semantic") {
        return false;
    }

    if (
        props.restrictToResourceInstanceDatatypes &&
        !isResourceInstanceDatatype(nodeSummary.datatype)
    ) {
        return false;
    }

    if (!relationshipGraphPair) {
        return true;
    }

    return doesNodeBridgeRelationshipGraphPair(
        nodeSummary,
        relationshipGraphPair,
    );
}

function markWrapperAliasParentsUnselectable(
    treeNodes: TreeNodeOption[],
): void {
    function traverse(treeNodeList: TreeNodeOption[]): void {
        for (const treeNode of treeNodeList) {
            if (treeNode.children.length > 0) {
                const parentAlias = treeNode.data.alias;

                const hasChildWithSameAlias = treeNode.children.some(
                    (childNode) => {
                        return childNode.data.alias === parentAlias;
                    },
                );

                if (hasChildWithSameAlias) {
                    treeNode.selectable = false;
                }
            }

            if (treeNode.children.length > 0) {
                traverse(treeNode.children);
            }
        }
    }

    traverse(treeNodes);
}

function buildTreeFromFlatNodes(
    nodeSummaries: NodeSummary[],
    relationshipGraphPair: RelationshipGraphPair | undefined,
): TreeNodeOption[] {
    const treeNodesByLookupKey: Record<string, TreeNodeOption> = {};
    const rootTreeNodes: TreeNodeOption[] = [];

    for (const nodeSummary of nodeSummaries) {
        let label = nodeSummary.card_x_node_x_widget_label;
        if (!label) {
            label = nodeSummary.name;
        }
        if (!label) {
            label = nodeSummary.alias;
        }

        const graphSlug = nodeSummary.graph_slug ?? "";
        const treeNodeKey = `${graphSlug}:${nodeSummary.id}`;

        treeNodesByLookupKey[treeNodeKey] = {
            key: treeNodeKey,
            label,
            data: nodeSummary,
            children: [],
            selectable: isNodeSelectable(nodeSummary, relationshipGraphPair),
        };
    }

    for (const nodeSummary of nodeSummaries) {
        const graphSlug = nodeSummary.graph_slug ?? "";
        const treeNodeKey = `${graphSlug}:${nodeSummary.id}`;

        const treeNode = treeNodesByLookupKey[treeNodeKey];
        const semanticParentId = nodeSummary.semantic_parent_id;

        if (semanticParentId) {
            const parentTreeNodeKey = `${graphSlug}:${semanticParentId}`;
            const parentTreeNode = treeNodesByLookupKey[parentTreeNodeKey];

            if (parentTreeNode) {
                parentTreeNode.children.push(treeNode);
                continue;
            }
        }

        rootTreeNodes.push(treeNode);
    }

    markWrapperAliasParentsUnselectable(rootTreeNodes);
    sortTreeNodes(rootTreeNodes);

    if (!relationshipGraphPair) {
        return rootTreeNodes;
    }

    return pruneTreeToSelectableNodes(rootTreeNodes);
}

function sortTreeNodes(treeNodeList: TreeNodeOption[]): void {
    treeNodeList.sort((firstNode, secondNode) => {
        const firstSortorder = firstNode.data.sortorder ?? 0;
        const secondSortorder = secondNode.data.sortorder ?? 0;

        const sortorderComparison = firstSortorder - secondSortorder;

        if (sortorderComparison !== 0) {
            return sortorderComparison;
        }

        return firstNode.label.localeCompare(secondNode.label);
    });

    for (const treeNode of treeNodeList) {
        if (treeNode.children.length > 0) {
            sortTreeNodes(treeNode.children);
        }
    }
}

function pruneTreeToSelectableNodes(
    treeNodeList: TreeNodeOption[],
): TreeNodeOption[] {
    const prunedTreeNodes: TreeNodeOption[] = [];

    for (const treeNode of treeNodeList) {
        const prunedChildren = pruneTreeToSelectableNodes(treeNode.children);

        const nodeIsSelectable = treeNode.selectable !== false;
        const shouldIncludeNode = nodeIsSelectable || prunedChildren.length > 0;

        if (shouldIncludeNode) {
            prunedTreeNodes.push({
                key: treeNode.key,
                label: treeNode.label,
                data: treeNode.data,
                children: prunedChildren,
                selectable: treeNode.selectable,
            });
        }
    }

    return prunedTreeNodes;
}

function findNodeByKey(
    treeNodes: TreeNodeOption[],
    key: string,
): TreeNodeOption | null {
    for (const treeNode of treeNodes) {
        if (treeNode.key === key) {
            return treeNode;
        }

        if (treeNode.children.length > 0) {
            const matchingChild = findNodeByKey(treeNode.children, key);
            if (matchingChild) {
                return matchingChild;
            }
        }
    }

    return null;
}

function findDeepestNodeByGraphSlugAndAlias(
    treeNodes: TreeNodeOption[],
    graphSlug: string,
    alias: string,
): TreeNodeOption | null {
    let bestMatch: TreeNodeOption | null = null;
    let bestDepth = -1;

    function traverse(treeNodeList: TreeNodeOption[], depth: number): void {
        for (const treeNode of treeNodeList) {
            if (
                treeNode.data.graph_slug === graphSlug &&
                treeNode.data.alias === alias
            ) {
                const isBetterDepth = depth > bestDepth;
                const isBetterSelectability =
                    depth === bestDepth &&
                    bestMatch?.selectable === false &&
                    treeNode.selectable !== false;

                if (isBetterDepth || isBetterSelectability) {
                    bestDepth = depth;
                    bestMatch = treeNode;
                }
            }

            if (treeNode.children.length > 0) {
                traverse(treeNode.children, depth + 1);
            }
        }
    }

    traverse(treeNodes, 0);
    return bestMatch;
}

function expandAll(treeNodes: TreeNodeOption[]): void {
    const expanded: Record<string, boolean> = {};

    function traverse(treeNodeList: TreeNodeOption[]): void {
        for (const treeNode of treeNodeList) {
            expanded[treeNode.key] = true;
            if (treeNode.children.length > 0) {
                traverse(treeNode.children);
            }
        }
    }

    traverse(treeNodes);
    expandedKeys.value = expanded;
}

function uniqueGraphSlugsPreservingOrder(graphSlugsList: string[]): string[] {
    const seenGraphSlugs = new Set<string>();
    const uniqueGraphSlugs: string[] = [];

    for (const graphSlug of graphSlugsList ?? []) {
        if (!graphSlug) {
            continue;
        }

        if (seenGraphSlugs.has(graphSlug)) {
            continue;
        }

        seenGraphSlugs.add(graphSlug);
        uniqueGraphSlugs.push(graphSlug);
    }

    return uniqueGraphSlugs;
}

function getTruthySelectedKeys(
    updatedValue: Record<string, boolean>,
): string[] {
    return Object.keys(updatedValue).filter((key) =>
        Boolean(updatedValue[key]),
    );
}

function findNodePathByKey(
    treeNodes: TreeNodeOption[],
    key: string,
    currentPath: TreeNodeOption[] = [],
): TreeNodeOption[] | null {
    for (const treeNode of treeNodes) {
        const nextPath = [...currentPath, treeNode];

        if (treeNode.key === key) {
            return nextPath;
        }

        if (treeNode.children.length > 0) {
            const matchingPath = findNodePathByKey(
                treeNode.children,
                key,
                nextPath,
            );
            if (matchingPath) {
                return matchingPath;
            }
        }
    }

    return null;
}

function pickDeepestSelectableNodeKeyFromSelectedKeys(
    updatedValue: Record<string, boolean>,
    treeNodes: TreeNodeOption[],
): string | null {
    const truthySelectedKeys = getTruthySelectedKeys(updatedValue);

    let deepestSelectableKey: string | null = null;
    let deepestSelectableDepth = -1;

    for (const candidateKey of truthySelectedKeys) {
        const candidatePath = findNodePathByKey(treeNodes, candidateKey);
        if (!candidatePath || candidatePath.length === 0) {
            continue;
        }

        const candidateNode = candidatePath[candidatePath.length - 1];

        if (candidateNode.selectable === false) {
            continue;
        }

        if (candidatePath.length > deepestSelectableDepth) {
            deepestSelectableDepth = candidatePath.length;
            deepestSelectableKey = candidateKey;
        }
    }

    return deepestSelectableKey;
}

async function loadNodesForGraphSlugs(graphSlugsList: string[]): Promise<void> {
    const nodeLoadRequestId = ++latestNodeLoadRequestId.value;

    try {
        isLoading.value = true;
        configurationError.value = null;

        selectedKeys.value = {};
        nodeOptions.value = [];
        expandedKeys.value = {};
        lastEmittedPathSequenceKey.value = null;
        lastEmittedSelectedTreeKey.value = null;

        const graphSlugsToUse = uniqueGraphSlugsPreservingOrder(
            graphSlugsList ?? [],
        );
        const relationshipGraphPair = deriveRelationshipGraphPairFromSlugs(
            props.relationshipBetweenGraphs,
        );

        const perGraphTreePromises = graphSlugsToUse.map(async (graphSlug) => {
            const matchingGraph = graphs.value.find(
                (graphSummary) => graphSummary.slug === graphSlug,
            );
            if (!matchingGraph) {
                return [];
            }

            const flatNodes = await getNodesForGraphId(matchingGraph.graphid);

            const flatNodesWithGraphSlug: NodeSummary[] = flatNodes.map(
                (nodeSummary) => ({
                    ...nodeSummary,
                    graph_slug: nodeSummary.graph_slug || matchingGraph.slug,
                }),
            );

            return buildTreeFromFlatNodes(
                flatNodesWithGraphSlug,
                relationshipGraphPair,
            );
        });

        const perGraphTrees = await Promise.all(perGraphTreePromises);

        if (nodeLoadRequestId !== latestNodeLoadRequestId.value) {
            return;
        }

        const mergedRootNodes = perGraphTrees.flat();

        nodeOptions.value = mergedRootNodes;
        expandAll(mergedRootNodes);
    } catch (caughtError) {
        if (nodeLoadRequestId !== latestNodeLoadRequestId.value) {
            return;
        }

        configurationError.value = caughtError as Error;
        nodeOptions.value = [];
        expandedKeys.value = {};
        selectedKeys.value = {};
        lastEmittedPathSequenceKey.value = null;
        lastEmittedSelectedTreeKey.value = null;
    } finally {
        if (nodeLoadRequestId === latestNodeLoadRequestId.value) {
            isLoading.value = false;
        }
    }
}

function makePathSequenceKey(
    pathSequenceValue: PathSequence | undefined,
): string {
    const firstSegment = pathSequenceValue?.[0];
    if (!firstSegment) {
        return "";
    }

    const graphSlug = firstSegment[0] ?? "";
    const nodeAlias = firstSegment[1] ?? "";
    return `${graphSlug}::${nodeAlias}`;
}

function seedSelectionFromPathSequence(): void {
    const initialSegment = props.pathSequence?.[0];
    const nextPathSequenceKey = makePathSequenceKey(props.pathSequence);

    if (!initialSegment || nodeOptions.value.length === 0) {
        selectedKeys.value = {};
        return;
    }

    if (
        lastEmittedPathSequenceKey.value &&
        lastEmittedSelectedTreeKey.value &&
        nextPathSequenceKey === lastEmittedPathSequenceKey.value
    ) {
        const matchingPreviouslySelectedNode = findNodeByKey(
            nodeOptions.value,
            lastEmittedSelectedTreeKey.value,
        );

        if (
            matchingPreviouslySelectedNode &&
            matchingPreviouslySelectedNode.selectable !== false
        ) {
            selectedKeys.value = { [lastEmittedSelectedTreeKey.value]: true };
            return;
        }
    }

    const [graphSlug, nodeAlias] = initialSegment;
    const matchingNode = findDeepestNodeByGraphSlugAndAlias(
        nodeOptions.value,
        graphSlug,
        nodeAlias,
    );

    if (!matchingNode || matchingNode.selectable === false) {
        selectedKeys.value = {};
        return;
    }

    selectedKeys.value = { [matchingNode.key]: true };
}

function onUpdateModelValue(
    updatedValue: Record<string, boolean> | null,
): void {
    const normalizedUpdatedValue = updatedValue ?? {};
    const truthySelectedKeys = getTruthySelectedKeys(normalizedUpdatedValue);

    if (truthySelectedKeys.length === 0) {
        selectedKeys.value = {};
        emit("update:pathSequence", []);
        lastEmittedPathSequenceKey.value = null;
        lastEmittedSelectedTreeKey.value = null;
        return;
    }

    const chosenKey = pickDeepestSelectableNodeKeyFromSelectedKeys(
        normalizedUpdatedValue,
        nodeOptions.value,
    );

    if (!chosenKey) {
        selectedKeys.value = {};
        emit("update:pathSequence", []);
        lastEmittedPathSequenceKey.value = null;
        lastEmittedSelectedTreeKey.value = null;
        return;
    }

    const matchingNode = findNodeByKey(nodeOptions.value, chosenKey);

    if (
        !matchingNode ||
        matchingNode.selectable === false ||
        !matchingNode.data.graph_slug
    ) {
        selectedKeys.value = {};
        emit("update:pathSequence", []);
        lastEmittedPathSequenceKey.value = null;
        lastEmittedSelectedTreeKey.value = null;
        return;
    }

    selectedKeys.value = { [chosenKey]: true };

    const emittedPathSequence: PathSequence = [
        [matchingNode.data.graph_slug, matchingNode.data.alias],
    ];

    lastEmittedPathSequenceKey.value = makePathSequenceKey(emittedPathSequence);
    lastEmittedSelectedTreeKey.value = chosenKey;

    emit("update:pathSequence", emittedPathSequence);
}

function getGraphLabelPrefixForNode(
    nodeSummary: NodeSummary | undefined,
): string {
    if (!nodeSummary?.graph_slug) {
        return "";
    }

    const matchingGraphSummary = graphs.value.find(
        (graphSummary) => graphSummary.slug === nodeSummary.graph_slug,
    );

    const graphLabel = matchingGraphSummary?.name ?? "";
    if (!graphLabel) {
        return "";
    }

    return `${graphLabel}: `;
}

function getSelectedNodeSummaryFromValueSlot(
    valueSlotValue: unknown,
): NodeSummary | undefined {
    const selectedNodeArray = valueSlotValue as
        | Array<{ data?: NodeSummary; label?: string }>
        | undefined;
    const firstSelectedNode = selectedNodeArray?.[0];
    return firstSelectedNode?.data;
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
        <TreeSelect
            :key="graphSelectionKey"
            style="font-size: 1.2rem"
            selection-mode="single"
            :model-value="selectedKeys"
            :disabled="selectableNodeCount === 0"
            filter
            :filter-placeholder="$gettext('Search nodes...')"
            :loading="isLoading"
            :placeholder="$gettext('Select node...')"
            :expanded-keys="expandedKeys"
            :options="nodeOptions"
            @update:model-value="onUpdateModelValue"
        >
            <template #value="valueSlotProps">
                <span
                    v-if="
                        valueSlotProps.value && valueSlotProps.value.length > 0
                    "
                >
                    <template v-if="props.shouldPrependGraphName">
                        {{
                            getGraphLabelPrefixForNode(
                                getSelectedNodeSummaryFromValueSlot(
                                    valueSlotProps.value,
                                ),
                            )
                        }}
                    </template>
                    {{ valueSlotProps.value[0].label }}
                </span>
                <span v-else>
                    {{ valueSlotProps.placeholder }}
                </span>
            </template>
        </TreeSelect>
    </div>
</template>

<style scoped>
.path-builder {
    display: flex;
    gap: 0.5rem;
}
</style>
