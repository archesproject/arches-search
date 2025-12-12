<script setup lang="ts">
import { ref, inject, watch } from "vue";
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
};

type PathSequence = [string, string][];

type RelationshipGraphPair = readonly [string, string];

const { $gettext } = useGettext();

const getNodesForGraphId =
    inject<(graphId: string) => Promise<NodeSummary[]>>("getNodesForGraphId")!;

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;

const emits = defineEmits<{
    (event: "update:pathSequence", value: PathSequence): void;
    (event: "compatibleRelationshipNodesChanged", value: boolean): void;
}>();

const {
    graphSlugs,
    pathSequence,
    relationshipBetweenGraphs,
    shouldPrependGraphName,
} = defineProps<{
    graphSlugs: string[];
    pathSequence?: PathSequence;
    relationshipBetweenGraphs?: string[];
    shouldPrependGraphName?: boolean;
}>();

const isLoading = ref(false);
const configurationError = ref<Error | null>(null);

const nodeOptions = ref<TreeNodeOption[]>([]);
const expandedKeys = ref<Record<string, boolean>>({});
const selectedKeys = ref<Record<string, boolean>>({});

watch(
    () => graphSlugs,
    async (nextGraphSlugs) => {
        if (!nextGraphSlugs || nextGraphSlugs.length === 0) {
            nodeOptions.value = [];
            expandedKeys.value = {};
            selectedKeys.value = {};
            return;
        }

        await loadNodesForGraphSlugs(nextGraphSlugs);
        seedSelectionFromPathSequence();
    },
    { deep: true, immediate: true },
);

watch(
    () => pathSequence,
    () => {
        seedSelectionFromPathSequence();
    },
    { deep: true, immediate: true },
);

watch(
    () => nodeOptions.value.length,
    (nextLength: number) => {
        emits("compatibleRelationshipNodesChanged", nextLength > 0);
    },
    { immediate: true },
);

function deriveRelationshipGraphPairFromSlugs(
    relationshipGraphSlugList?: string[],
): RelationshipGraphPair | undefined {
    if (!relationshipGraphSlugList || relationshipGraphSlugList.length === 0) {
        return undefined;
    }

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

function isResourceInstanceDatatype(datatype: string): boolean {
    if (datatype === "resource-instance") {
        return true;
    }

    if (datatype === "resource-instance-list") {
        return true;
    }

    return false;
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
    if (!relationshipGraphPair) {
        return true;
    }

    if (!isResourceInstanceDatatype(nodeSummary.datatype)) {
        return false;
    }

    return doesNodeBridgeRelationshipGraphPair(
        nodeSummary,
        relationshipGraphPair,
    );
}

function buildTreeFromFlatNodes(
    nodeSummaries: NodeSummary[],
    relationshipGraphPair: RelationshipGraphPair | undefined,
): TreeNodeOption[] {
    const treeNodesById: Record<string, TreeNodeOption> = {};
    const rootTreeNodes: TreeNodeOption[] = [];

    for (const nodeSummary of nodeSummaries) {
        let label = nodeSummary.card_x_node_x_widget_label;
        if (!label) {
            label = nodeSummary.name;
        }
        if (!label) {
            label = nodeSummary.alias;
        }

        let treeNodeKey = nodeSummary.id;
        if (nodeSummary.graph_slug) {
            treeNodeKey = `${nodeSummary.graph_slug}:${nodeSummary.id}`;
        }

        treeNodesById[nodeSummary.id] = {
            key: treeNodeKey,
            label,
            data: nodeSummary,
            children: [],
        };
    }

    for (const nodeSummary of nodeSummaries) {
        const treeNode = treeNodesById[nodeSummary.id];
        const semanticParentId = nodeSummary.semantic_parent_id;

        if (semanticParentId && treeNodesById[semanticParentId]) {
            const parentTreeNode = treeNodesById[semanticParentId];
            parentTreeNode.children.push(treeNode);
        } else {
            rootTreeNodes.push(treeNode);
        }
    }

    sortTreeNodes(rootTreeNodes);

    const filteredRootTreeNodes = pruneTreeToSelectableNodes(
        rootTreeNodes,
        relationshipGraphPair,
    );

    return filteredRootTreeNodes;
}

function sortTreeNodes(treeNodeList: TreeNodeOption[]): void {
    treeNodeList.sort((firstNode, secondNode) => {
        const sortorderComparison =
            firstNode.data.sortorder - secondNode.data.sortorder;

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
    relationshipGraphPair: RelationshipGraphPair | undefined,
): TreeNodeOption[] {
    const prunedTreeNodes: TreeNodeOption[] = [];

    for (const treeNode of treeNodeList) {
        const prunedChildren = pruneTreeToSelectableNodes(
            treeNode.children,
            relationshipGraphPair,
        );

        const nodeIsSelectable = isNodeSelectable(
            treeNode.data,
            relationshipGraphPair,
        );

        const shouldIncludeNode = nodeIsSelectable || prunedChildren.length > 0;

        if (shouldIncludeNode) {
            const prunedTreeNode: TreeNodeOption = {
                key: treeNode.key,
                label: treeNode.label,
                data: treeNode.data,
                children: prunedChildren,
            };
            prunedTreeNodes.push(prunedTreeNode);
        }
    }

    return prunedTreeNodes;
}

function findNodeByGraphSlugAndAlias(
    treeNodes: TreeNodeOption[],
    graphSlug: string,
    alias: string,
): TreeNodeOption | null {
    for (const treeNode of treeNodes) {
        if (
            treeNode.data.graph_slug === graphSlug &&
            treeNode.data.alias === alias
        ) {
            return treeNode;
        }

        if (treeNode.children.length > 0) {
            const matchingChild = findNodeByGraphSlugAndAlias(
                treeNode.children,
                graphSlug,
                alias,
            );
            if (matchingChild) {
                return matchingChild;
            }
        }
    }

    return null;
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

async function loadNodesForGraphSlugs(graphSlugsList: string[]): Promise<void> {
    try {
        isLoading.value = true;
        configurationError.value = null;

        selectedKeys.value = {};
        nodeOptions.value = [];
        expandedKeys.value = {};

        const graphSlugsToUse = graphSlugsList ?? [];

        if (graphSlugsToUse.length === 0) {
            nodeOptions.value = [];
            expandedKeys.value = {};
            selectedKeys.value = {};
            return;
        }

        const uniqueGraphSlugSet = new Set<string>(graphSlugsToUse);
        const uniqueGraphSlugsToUse = Array.from(uniqueGraphSlugSet);

        const relationshipGraphPair = deriveRelationshipGraphPairFromSlugs(
            relationshipBetweenGraphs,
        );

        const treeNodesPerGraphPromises = uniqueGraphSlugsToUse.map(
            async (graphSlug) => {
                const matchingGraph = graphs.value.find((graphSummary) => {
                    return graphSummary.slug === graphSlug;
                });

                if (!matchingGraph) {
                    return [] as TreeNodeOption[];
                }

                const flatNodes = await getNodesForGraphId(
                    matchingGraph.graphid,
                );

                const flatNodesWithGraphSlug: NodeSummary[] = flatNodes.map(
                    (nodeSummary) => {
                        let nodeGraphSlug = nodeSummary.graph_slug;
                        if (!nodeGraphSlug) {
                            nodeGraphSlug = matchingGraph.slug;
                        }

                        return {
                            ...nodeSummary,
                            graph_slug: nodeGraphSlug,
                        };
                    },
                );

                return buildTreeFromFlatNodes(
                    flatNodesWithGraphSlug,
                    relationshipGraphPair,
                );
            },
        );

        const treeNodesPerGraph = await Promise.all(treeNodesPerGraphPromises);
        const mergedTreeNodes: TreeNodeOption[] = [];

        for (const treeNodesForGraph of treeNodesPerGraph) {
            for (const treeNode of treeNodesForGraph) {
                mergedTreeNodes.push(treeNode);
            }
        }

        nodeOptions.value = mergedTreeNodes;
        expandAll(mergedTreeNodes);
    } catch (error) {
        configurationError.value = error as Error;
        nodeOptions.value = [];
        expandedKeys.value = {};
        selectedKeys.value = {};
    } finally {
        isLoading.value = false;
    }
}

function seedSelectionFromPathSequence(): void {
    const initialSegment = pathSequence?.[0];

    if (!initialSegment || nodeOptions.value.length === 0) {
        selectedKeys.value = {};
        return;
    }

    const [graphSlug, nodeAlias] = initialSegment;

    const matchingNode = findNodeByGraphSlugAndAlias(
        nodeOptions.value,
        graphSlug,
        nodeAlias,
    );

    if (!matchingNode) {
        selectedKeys.value = {};
        return;
    }

    selectedKeys.value = { [matchingNode.key]: true };
}

function onUpdateModelValue(
    updatedValue: Record<string, boolean> | null,
): void {
    if (!updatedValue || Object.keys(updatedValue).length === 0) {
        selectedKeys.value = {};
        emits("update:pathSequence", []);
        return;
    }

    const chosenKey = Object.keys(updatedValue)[0];

    selectedKeys.value = { [chosenKey]: true };

    const matchingNode = findNodeByKey(nodeOptions.value, chosenKey);
    if (!matchingNode || !matchingNode.data.graph_slug) {
        emits("update:pathSequence", []);
        return;
    }

    const nextPathSequence: PathSequence = [
        [matchingNode.data.graph_slug, matchingNode.data.alias],
    ];

    emits("update:pathSequence", nextPathSequence);
}

function getGraphLabelPrefixForNode(
    nodeSummary: NodeSummary | undefined,
): string {
    if (!nodeSummary) {
        return "";
    }

    const nodeGraphSlug = nodeSummary.graph_slug;
    if (!nodeGraphSlug) {
        return "";
    }

    const matchingGraphSummary = graphs.value.find((graphSummary) => {
        return graphSummary.slug === nodeGraphSlug;
    });

    if (!matchingGraphSummary) {
        return "";
    }

    const graphLabel = matchingGraphSummary.name ?? "";

    if (!graphLabel) {
        return "";
    }

    return `${graphLabel}: `;
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
            style="font-size: 1.2rem"
            selection-mode="single"
            :model-value="selectedKeys"
            :disabled="nodeOptions.length === 0"
            filter
            :filter-placeholder="$gettext('Search nodes...')"
            :loading="isLoading"
            :placeholder="$gettext('Select node...')"
            :options="nodeOptions"
            @update:model-value="onUpdateModelValue"
        >
            <template #value="valueSlotProps">
                <span
                    v-if="
                        valueSlotProps.value && valueSlotProps.value.length > 0
                    "
                >
                    <template v-if="shouldPrependGraphName">
                        {{
                            getGraphLabelPrefixForNode(
                                valueSlotProps.value[0].data as NodeSummary,
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
