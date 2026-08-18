<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import TreeSelect from "primevue/treeselect";

import type {
    GraphModel,
    PathSelection,
    RelatableGraphOption,
    RelatableNodeOption,
} from "@/arches_search/AdvancedSearch/types.ts";

type NodeSummary = {
    id: string;
    alias: string;
    name: string;
    datatype: string;
    sortorder: number;
    card_x_node_x_widget_label: string;
    semantic_parent_id: string | null;
    graph_slug?: string;
    graph_label?: string;
    is_inverse?: boolean;
    selectable?: boolean;
    [key: string]: unknown;
};

type PathNode = {
    key: string;
    label: string;
    data: NodeSummary;
    children: PathNode[];
    selectable?: boolean;
};

const DATATYPE_SEMANTIC = "semantic";

const {
    graphSlugs,
    selectedNode = null,
    shouldPrependGraphName,
    graphOptionsTree,
} = defineProps<{
    // No default: absence means "use graphOptionsTree instead" (see
    // graphSelectionKey and the watcher below) — the two are mutually exclusive
    // alternate data sources, so neither can be expressed as a static default.
    graphSlugs?: string[];
    selectedNode?: PathSelection | null;
    shouldPrependGraphName?: boolean;
    graphOptionsTree?: RelatableGraphOption[];
}>();

const emit = defineEmits<{ "update:selectedNode": [PathSelection | null] }>();

const getNodesForGraphId =
    inject<(graphId: string) => Promise<NodeSummary[]>>("getNodesForGraphId")!;
const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;

const { $gettext } = useGettext();

let currentLoad = 0;

const isLoading = ref(false);
const configurationError = ref<Error | null>(null);
const nodeOptions = ref<PathNode[]>([]);

const graphSelectionKey = computed(() => {
    if (graphOptionsTree) {
        return `options::${graphOptionsTree.map((graphOption) => graphOption.key).join("|")}`;
    }
    return (graphSlugs ?? []).join("|");
});

const hasSelectableNodes = computed(() => {
    return hasSelectableNode(nodeOptions.value);
});

const expandedKeys = computed(() => {
    const allExpandedKeys: Record<string, boolean> = {};
    const nodesToVisit = [...nodeOptions.value];
    while (nodesToVisit.length > 0) {
        const currentNode = nodesToVisit.pop()!;
        allExpandedKeys[currentNode.key] = true;
        nodesToVisit.push(...currentNode.children);
    }
    return allExpandedKeys;
});

const selectedKeys = computed({
    get(): Record<string, boolean> {
        if (!selectedNode?.graph_slug || !selectedNode.node_alias) {
            return {};
        }

        const matchingNode = findNode(nodeOptions.value, (node) => {
            return (
                node.data.graph_slug === selectedNode.graph_slug &&
                node.data.alias === selectedNode.node_alias &&
                (selectedNode.is_inverse === undefined ||
                    node.data.is_inverse === selectedNode.is_inverse) &&
                node.selectable !== false
            );
        });

        if (!matchingNode) {
            return {};
        }

        return { [matchingNode.key]: true };
    },
    set(newSelectionKeys: unknown) {
        const selectionMap = Object(newSelectionKeys) as Record<
            string,
            unknown
        >;
        const selectedKey =
            Object.keys(selectionMap).find((key) => {
                return selectionMap[key] === true;
            }) ?? null;

        let matchingNode: PathNode | null = null;
        if (selectedKey) {
            matchingNode = findNode(nodeOptions.value, (node) => {
                return node.key === selectedKey;
            });
        }
        if (!matchingNode || matchingNode.selectable === false) {
            emit("update:selectedNode", null);

            return;
        }

        emit("update:selectedNode", {
            graph_slug: matchingNode.data.graph_slug!,
            node_alias: matchingNode.data.alias,
            is_inverse: matchingNode.data.is_inverse,
        });
    },
});

watch(
    graphSelectionKey,
    async () => {
        if (graphOptionsTree) {
            nodeOptions.value = buildTree(
                flattenGraphOptionsTree(graphOptionsTree),
            );
            return;
        }

        const activeGraphSlugs = graphSlugs ?? [];
        if (activeGraphSlugs.length === 0) {
            clearState();
            return;
        }

        await loadNodes(activeGraphSlugs);
    },
    { immediate: true },
);

function hasSelectableNode(nodes: PathNode[]): boolean {
    return nodes.some((node) => {
        return node.selectable !== false || hasSelectableNode(node.children);
    });
}

function clearState(): void {
    nodeOptions.value = [];
}

function findNode(
    nodes: PathNode[],
    predicate: (node: PathNode) => boolean,
): PathNode | null {
    for (const node of nodes) {
        if (predicate(node)) {
            return node;
        }

        const found = findNode(node.children, predicate);
        if (found) {
            return found;
        }
    }
    return null;
}

function isNodeSelectable(node: NodeSummary): boolean {
    return node.datatype !== DATATYPE_SEMANTIC && node.selectable !== false;
}

function buildTree(nodeSummaries: NodeSummary[]): PathNode[] {
    const nodeKeyToPathNode: Record<string, PathNode> = {};
    const roots: PathNode[] = [];

    for (const nodeSummary of nodeSummaries) {
        const nodeKey = `${nodeSummary.graph_slug}:${nodeSummary.id}`;
        nodeKeyToPathNode[nodeKey] = {
            key: nodeKey,
            label:
                nodeSummary.card_x_node_x_widget_label ||
                nodeSummary.name ||
                nodeSummary.alias,
            data: nodeSummary,
            children: [],
            selectable: isNodeSelectable(nodeSummary),
        };
    }

    for (const nodeSummary of nodeSummaries) {
        const treeNode =
            nodeKeyToPathNode[`${nodeSummary.graph_slug}:${nodeSummary.id}`]!;

        if (nodeSummary.semantic_parent_id) {
            const parentNode =
                nodeKeyToPathNode[
                    `${nodeSummary.graph_slug}:${nodeSummary.semantic_parent_id}`
                ];
            (parentNode?.children ?? roots).push(treeNode);
        } else {
            roots.push(treeNode);
        }
    }

    function compareNodes(leftNode: PathNode, rightNode: PathNode): number {
        const sortOrderDifference =
            (leftNode.data.sortorder ?? 0) - (rightNode.data.sortorder ?? 0);

        if (sortOrderDifference !== 0) {
            return sortOrderDifference;
        }

        return leftNode.label.localeCompare(rightNode.label);
    }

    roots.sort(compareNodes);

    for (const node of Object.values(nodeKeyToPathNode)) {
        node.children.sort(compareNodes);
    }

    function pruneUnselectable(nodes: PathNode[]): PathNode[] {
        return nodes.flatMap((node) => {
            const prunedChildren = pruneUnselectable(node.children);
            if (node.selectable !== false || prunedChildren.length > 0) {
                return [{ ...node, children: prunedChildren }];
            }
            return [];
        });
    }

    return pruneUnselectable(roots);
}

function flattenGraphOptionsTree(
    graphOptions: RelatableGraphOption[],
): NodeSummary[] {
    const flatNodeSummaries: NodeSummary[] = [];

    function visit(
        relatableNode: RelatableNodeOption,
        graphSlug: string,
        graphLabel: string,
        parentKey: string,
    ): void {
        flatNodeSummaries.push({
            id: relatableNode.key,
            alias: relatableNode.data.alias,
            name: relatableNode.data.name,
            datatype: relatableNode.data.datatype,
            sortorder: flatNodeSummaries.length,
            card_x_node_x_widget_label: relatableNode.label,
            semantic_parent_id: parentKey,
            graph_slug: graphSlug,
            graph_label: graphLabel,
            is_inverse: relatableNode.data.is_inverse,
        });

        for (const childNode of relatableNode.children) {
            visit(childNode, graphSlug, graphLabel, relatableNode.key);
        }
    }

    for (const graphOption of graphOptions) {
        // Kept visible so a self-relationship's two identically-named branches stay distinguishable.
        flatNodeSummaries.push({
            id: graphOption.key,
            alias: "",
            name: graphOption.label,
            datatype: DATATYPE_SEMANTIC,
            sortorder: flatNodeSummaries.length,
            card_x_node_x_widget_label: graphOption.label,
            semantic_parent_id: null,
            graph_slug: graphOption.data.slug,
        });

        for (const rootNode of graphOption.children) {
            visit(
                rootNode,
                graphOption.data.slug,
                graphOption.label,
                graphOption.key,
            );
        }
    }

    return flatNodeSummaries;
}

async function loadNodes(activeGraphSlugs: string[]): Promise<void> {
    currentLoad++;
    const thisLoad = currentLoad;
    isLoading.value = true;
    configurationError.value = null;
    clearState();

    try {
        const perGraphTrees = await Promise.all(
            activeGraphSlugs.map(async (slug) => {
                const matchingGraph = graphs.value.find((graph) => {
                    return graph.slug === slug;
                });
                if (!matchingGraph) {
                    return [];
                }

                const flatNodes = await getNodesForGraphId(
                    matchingGraph.graphid,
                );
                const nodesWithSlug = flatNodes.map((node) => {
                    return {
                        ...node,
                        graph_slug: node.graph_slug || matchingGraph.slug,
                    };
                });

                return buildTree(nodesWithSlug);
            }),
        );

        if (thisLoad !== currentLoad) {
            return;
        }

        nodeOptions.value = perGraphTrees.flat();
    } catch (error) {
        if (thisLoad !== currentLoad) {
            return;
        }
        configurationError.value = error as Error;
        clearState();
    } finally {
        if (thisLoad === currentLoad) {
            isLoading.value = false;
        }
    }
}

function getGraphLabelPrefix(treeSelectValue: unknown): string {
    const firstSelectedNode = (
        treeSelectValue as Array<{ data?: NodeSummary }>
    )?.[0]?.data;

    const graphLabel =
        firstSelectedNode?.graph_label ??
        graphs.value.find((graph) => {
            return graph.slug === firstSelectedNode?.graph_slug;
        })?.name;

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
            :key="graphSelectionKey"
            v-model="selectedKeys"
            selection-mode="single"
            style="font-size: 1.2rem"
            :disabled="!hasSelectableNodes"
            filter
            :filter-placeholder="$gettext('Search nodes...')"
            :loading="isLoading"
            :placeholder="$gettext('Select node...')"
            :expanded-keys="expandedKeys"
            :options="nodeOptions"
        >
            <template #value="valueSlotProps">
                <span
                    v-if="
                        valueSlotProps.value && valueSlotProps.value.length > 0
                    "
                >
                    <template v-if="shouldPrependGraphName">
                        {{ getGraphLabelPrefix(valueSlotProps.value) }}
                    </template>

                    {{ valueSlotProps.value[0].label }}
                </span>
                <span v-else>{{ valueSlotProps.placeholder }}</span>
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
