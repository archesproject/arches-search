<script setup lang="ts">
import { ref, inject, computed, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import TreeSelect from "primevue/treeselect";
import Select from "primevue/select";

const { $gettext } = useGettext();

type GraphSummary = {
    graphid: string;
    slug: string;
    name: string;
    label?: string;
    [key: string]: unknown;
};

type NodeSummary = {
    id: string;
    alias: string;
    name: string;
    datatype: string;
    sortorder: number;
    card_x_node_x_widget_label: string;
    semantic_parent_id: string | null;
    [key: string]: unknown;
};

type TreeNodeOption = {
    key: string;
    label: string;
    data: NodeSummary;
    children: TreeNodeOption[];
};

type PathSequence = readonly (readonly [string, string])[];

const getNodesForGraphId =
    inject<(graphId: string) => Promise<NodeSummary[]>>("getNodesForGraphId")!;

const emits = defineEmits<{
    (event: "update:pathSequence", value: [string, string][]): void;
}>();

const { anchorGraph, pathSequence, showAnchorGraphDropdown } = defineProps<{
    anchorGraph: GraphSummary;
    pathSequence?: PathSequence;
    showAnchorGraphDropdown?: boolean;
}>();

const isLoading = ref(false);
const configurationError = ref<Error | null>(null);

const nodeOptions = ref<TreeNodeOption[]>([]);
const expandedKeys = ref<Record<string, boolean>>({});
const selectedKeys = ref<Record<string, boolean>>({});

const anchorGraphDisplayOption = computed(() => ({
    ...anchorGraph,
    label: anchorGraph.label ?? anchorGraph.name,
}));

const shouldShowAnchorGraphDropdown = computed(() => {
    return Boolean(showAnchorGraphDropdown);
});

watch(
    () => anchorGraph.graphid,
    async (graphId) => {
        if (!graphId) {
            nodeOptions.value = [];
            expandedKeys.value = {};
            selectedKeys.value = {};
            return;
        }

        await loadNodes(graphId);
        seedSelectionFromPathSequence();
    },
    { immediate: true },
);

watch(
    () => pathSequence,
    () => {
        seedSelectionFromPathSequence();
    },
    { deep: true, immediate: true },
);

function buildTreeFromFlatNodes(
    nodeSummaries: NodeSummary[],
): TreeNodeOption[] {
    const treeNodesById: Record<string, TreeNodeOption> = {};
    const rootTreeNodes: TreeNodeOption[] = [];

    for (const nodeSummary of nodeSummaries) {
        const label =
            nodeSummary.card_x_node_x_widget_label ||
            nodeSummary.name ||
            nodeSummary.alias;

        treeNodesById[nodeSummary.id] = {
            key: nodeSummary.id,
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

    function sortTreeNodes(treeNodeList: TreeNodeOption[]) {
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

    sortTreeNodes(rootTreeNodes);

    return rootTreeNodes;
}

function findNodeByAlias(
    treeNodes: TreeNodeOption[],
    alias: string,
): TreeNodeOption | null {
    for (const treeNode of treeNodes) {
        if (treeNode.data.alias === alias) {
            return treeNode;
        }

        if (treeNode.children.length > 0) {
            const matchingChild = findNodeByAlias(treeNode.children, alias);
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

function expandAll(treeNodes: TreeNodeOption[]) {
    const expanded: Record<string, boolean> = {};

    function traverse(treeNodeList: TreeNodeOption[]) {
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

async function loadNodes(graphId: string) {
    try {
        isLoading.value = true;
        configurationError.value = null;

        selectedKeys.value = {};
        nodeOptions.value = [];
        expandedKeys.value = {};

        const flatNodes = await getNodesForGraphId(graphId);
        const treeNodes = buildTreeFromFlatNodes(flatNodes);

        nodeOptions.value = treeNodes;
        expandAll(treeNodes);
    } catch (error) {
        configurationError.value = error as Error;
        nodeOptions.value = [];
        expandedKeys.value = {};
        selectedKeys.value = {};
    } finally {
        isLoading.value = false;
    }
}

function seedSelectionFromPathSequence() {
    const initialSegment = pathSequence?.[0];

    if (!initialSegment || nodeOptions.value.length === 0) {
        selectedKeys.value = {};
        return;
    }

    const [graphSlug, nodeAlias] = initialSegment;

    if (graphSlug !== anchorGraph.slug) {
        selectedKeys.value = {};
        return;
    }

    const matchingNode = findNodeByAlias(nodeOptions.value, nodeAlias);

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
    if (!matchingNode) {
        emits("update:pathSequence", []);
        return;
    }

    emits("update:pathSequence", [[anchorGraph.slug, matchingNode.data.alias]]);
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
        <Select
            v-if="shouldShowAnchorGraphDropdown"
            :model-value="anchorGraphDisplayOption"
            :options="[anchorGraphDisplayOption]"
            option-label="label"
            disabled
        />

        <TreeSelect
            style="font-size: 1.2rem"
            selection-mode="single"
            :model-value="selectedKeys"
            :expanded-keys="expandedKeys"
            :disabled="nodeOptions.length === 0"
            filter
            :filter-placeholder="$gettext('Search nodes...')"
            :loading="isLoading"
            :placeholder="$gettext('Select node...')"
            :options="nodeOptions"
            @update:model-value="onUpdateModelValue"
        />
    </div>
</template>

<style scoped>
.path-builder {
    display: flex;
    gap: 0.5rem;
}
</style>
