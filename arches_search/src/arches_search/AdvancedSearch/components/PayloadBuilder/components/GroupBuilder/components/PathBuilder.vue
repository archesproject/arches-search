<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import TreeSelect from "primevue/treeselect";

import type {
    GraphModel,
    PathSelection,
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
    config?: unknown;
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
const DATATYPE_RESOURCE_INSTANCE = "resource-instance";
const DATATYPE_RESOURCE_INSTANCE_LIST = "resource-instance-list";

const { $gettext } = useGettext();

const getNodesForGraphId =
    inject<(graphId: string) => Promise<NodeSummary[]>>("getNodesForGraphId")!;
const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;

const {
    graphSlugs,
    selectedNode,
    relationshipBetweenGraphs,
    shouldPrependGraphName,
    restrictToResourceInstanceDatatypes,
} = defineProps<{
    graphSlugs: string[];
    selectedNode?: PathSelection | null;
    relationshipBetweenGraphs?: string[];
    shouldPrependGraphName?: boolean;
    restrictToResourceInstanceDatatypes?: boolean;
}>();

const emit = defineEmits<{ "update:selectedNode": [PathSelection | null] }>();

let currentLoad = 0;

const isLoading = ref(false);
const configurationError = ref<Error | null>(null);
const nodeOptions = ref<PathNode[]>([]);

const graphSelectionKey = computed(() => {
    return `${graphSlugs.join("|")}::${relationshipBetweenGraphs?.join("|") ?? ""}::${restrictToResourceInstanceDatatypes}`;
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
        });
    },
});

watch(
    graphSelectionKey,
    async () => {
        if (graphSlugs.length === 0) {
            clearState();
            return;
        }

        await loadNodes();
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

function linksGraphPair(
    node: NodeSummary,
    graphPair: [string, string],
): boolean {
    const [firstGraphSlug, secondGraphSlug] = graphPair;

    if (
        node.graph_slug !== firstGraphSlug &&
        node.graph_slug !== secondGraphSlug
    ) {
        return false;
    }
    const configuredGraphs =
        (node.config as { graphs?: { graphid: string }[] })?.graphs ?? [];
    const targetSlug =
        node.graph_slug === firstGraphSlug ? secondGraphSlug : firstGraphSlug;

    return configuredGraphs.some((configured) => {
        return (
            graphs.value.find((graph) => {
                return graph.graphid === configured.graphid;
            })?.slug === targetSlug
        );
    });
}

function isNodeSelectable(
    node: NodeSummary,
    graphPair: [string, string] | undefined,
): boolean {
    if (node.datatype === DATATYPE_SEMANTIC) {
        return false;
    }

    const isRestrictedDatatype =
        node.datatype !== DATATYPE_RESOURCE_INSTANCE &&
        node.datatype !== DATATYPE_RESOURCE_INSTANCE_LIST;

    if (restrictToResourceInstanceDatatypes && isRestrictedDatatype) {
        return false;
    }
    if (!graphPair) {
        return true;
    }

    return linksGraphPair(node, graphPair);
}

function buildTree(
    nodeSummaries: NodeSummary[],
    graphPair: [string, string] | undefined,
): PathNode[] {
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
            selectable: isNodeSelectable(nodeSummary, graphPair),
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

    // Card-group wrapper nodes share the same alias as their first child — not user-selectable
    for (const node of Object.values(nodeKeyToPathNode)) {
        if (
            node.children.some((child) => {
                return child.data.alias === node.data.alias;
            })
        ) {
            node.selectable = false;
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

    if (!graphPair) {
        return roots;
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

async function loadNodes(): Promise<void> {
    currentLoad++;
    const thisLoad = currentLoad;
    isLoading.value = true;
    configurationError.value = null;
    clearState();

    try {
        const pairSlugs = relationshipBetweenGraphs ?? graphSlugs;
        let graphPair: [string, string] | undefined = undefined;

        if (pairSlugs.length >= 2) {
            graphPair = [pairSlugs[0], pairSlugs[1]];
        }

        const perGraphTrees = await Promise.all(
            graphSlugs.map(async (slug) => {
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

                return buildTree(nodesWithSlug, graphPair);
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

    const graphName = graphs.value.find((graph) => {
        return graph.slug === firstSelectedNode?.graph_slug;
    })?.name;

    if (!graphName) {
        return "";
    }

    return `${graphName}: `;
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
