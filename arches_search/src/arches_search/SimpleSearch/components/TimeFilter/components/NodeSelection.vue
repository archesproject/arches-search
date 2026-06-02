<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Chip from "primevue/chip";
import TreeSelect from "primevue/treeselect";

import type {
    TimeFilterNodeSummary,
    TimeFilterTreeNode,
} from "@/arches_search/SimpleSearch/components/TimeFilter/types.ts";

type CheckboxState = Record<
    string,
    { checked: boolean; partialChecked: boolean }
>;

const DATE_DATATYPES = ["date", "edtf"] as const;
const NODE_SELECT_ID = "simple-search-time-filter-node-selection";

const props = defineProps<{
    graphLabel: string | null;
    loading: boolean;
    modelValue: string[];
    nodes: TimeFilterNodeSummary[];
}>();

const emit = defineEmits<{
    (event: "update:modelValue", value: string[]): void;
}>();

const { $gettext, interpolate } = useGettext();

const nodeOptions = computed<TimeFilterTreeNode[]>(() =>
    buildTree(props.nodes),
);

const hasSelectableNodes = computed<boolean>(
    () => nodeOptions.value.length > 0,
);

const expandedKeys = computed<Record<string, boolean>>(() => {
    const keys: Record<string, boolean> = {};
    const queue = [...nodeOptions.value];
    while (queue.length > 0) {
        const node = queue.pop()!;
        keys[node.key] = true;
        queue.push(...node.children);
    }
    return keys;
});

const nodeByKey = computed<Map<string, TimeFilterTreeNode>>(() => {
    const map = new Map<string, TimeFilterTreeNode>();
    function collect(nodes: TimeFilterTreeNode[]): void {
        for (const node of nodes) {
            map.set(node.key, node);
            collect(node.children);
        }
    }
    collect(nodeOptions.value);
    return map;
});

const nodePathByAlias = computed<Record<string, string>>(() => {
    const nodeById = new Map(props.nodes.map((node) => [node.id, node]));

    function buildPath(node: TimeFilterNodeSummary): string {
        const labels: string[] = [];
        let current: TimeFilterNodeSummary | undefined = node;
        while (current) {
            labels.unshift(getDisplayLabel(current));
            if (!current.semantic_parent_id) break;
            current = nodeById.get(current.semantic_parent_id);
        }
        return labels.join(" > ");
    }

    return Object.fromEntries(
        props.nodes
            .filter((node) => node.alias)
            .map((node) => [node.alias, buildPath(node)]),
    );
});

const selectedKeys = computed<CheckboxState>(() => {
    const selectedAliasSet = new Set(props.modelValue);

    function processNode(node: TimeFilterTreeNode): {
        state: CheckboxState;
        selected: number;
        total: number;
    } {
        if (node.children.length === 0) {
            const isChecked = selectedAliasSet.has(node.data.alias);
            const state: CheckboxState = {};
            if (isChecked) {
                state[node.key] = { checked: true, partialChecked: false };
            }
            return { state, selected: isChecked ? 1 : 0, total: 1 };
        }

        let selected = 0;
        let total = 0;
        const childState: CheckboxState = {};
        for (const child of node.children) {
            const childStats = processNode(child);
            selected += childStats.selected;
            total += childStats.total;
            Object.assign(childState, childStats.state);
        }

        const parentState: CheckboxState = {};
        if (selected === total && total > 0) {
            parentState[node.key] = { checked: true, partialChecked: false };
        } else if (selected > 0) {
            parentState[node.key] = { checked: false, partialChecked: true };
        }

        return { state: { ...childState, ...parentState }, selected, total };
    }

    const result: CheckboxState = {};

    for (const root of nodeOptions.value) {
        Object.assign(result, processNode(root).state);
    }

    return result;
});

function onKeysChanged(newKeys: CheckboxState): void {
    const aliases: string[] = [];
    for (const [key, node] of nodeByKey.value) {
        if (
            node.selectable !== false &&
            node.data.alias &&
            newKeys[key]?.checked
        ) {
            aliases.push(node.data.alias);
        }
    }
    emit("update:modelValue", aliases);
}

function isNodeSelectable(node: TimeFilterNodeSummary): boolean {
    return (DATE_DATATYPES as readonly string[]).includes(node.datatype);
}

function getDisplayLabel(node: TimeFilterNodeSummary): string {
    return node.card_x_node_x_widget_label || node.name || node.alias;
}

function compareNodes(
    nodeA: TimeFilterTreeNode,
    nodeB: TimeFilterTreeNode,
): number {
    const sortDiff = (nodeA.data.sortorder ?? 0) - (nodeB.data.sortorder ?? 0);
    if (sortDiff !== 0) return sortDiff;
    return nodeA.label.localeCompare(nodeB.label);
}

function pruneUnselectable(nodes: TimeFilterTreeNode[]): TimeFilterTreeNode[] {
    return nodes
        .map((node) => ({
            ...node,
            children: pruneUnselectable(node.children),
        }))
        .filter(
            (node) => node.selectable !== false || node.children.length > 0,
        );
}

function buildTree(
    nodeSummaries: TimeFilterNodeSummary[],
): TimeFilterTreeNode[] {
    const nodeById: Record<string, TimeFilterTreeNode> = {};
    const roots: TimeFilterTreeNode[] = [];

    for (const summary of nodeSummaries) {
        nodeById[summary.id] = {
            key: summary.id,
            label: getDisplayLabel(summary),
            data: summary,
            children: [],
            selectable: isNodeSelectable(summary),
        };
    }

    for (const summary of nodeSummaries) {
        const node = nodeById[summary.id]!;
        if (
            summary.semantic_parent_id &&
            nodeById[summary.semantic_parent_id]
        ) {
            nodeById[summary.semantic_parent_id]!.children.push(node);
        } else {
            roots.push(node);
        }
    }

    // Card-group wrapper nodes share the same alias as their first child.
    for (const node of Object.values(nodeById)) {
        if (
            node.children.some((child) => child.data.alias === node.data.alias)
        ) {
            node.selectable = false;
        }
    }

    roots.sort(compareNodes);
    for (const node of Object.values(nodeById)) {
        node.children.sort(compareNodes);
    }

    return pruneUnselectable(roots);
}

function removeNode(alias: string): void {
    emit(
        "update:modelValue",
        props.modelValue.filter((selectedAlias) => selectedAlias !== alias),
    );
}
</script>

<template>
    <div class="node-selection">
        <div class="node-selection__attribute-row">
            <label
                class="node-selection__attribute-label"
                :for="NODE_SELECT_ID"
            >
                {{
                    interpolate($gettext("%{graphLabel} Time attribute:"), {
                        graphLabel: props.graphLabel ?? $gettext("Resource"),
                    })
                }}
            </label>

            <TreeSelect
                :model-value="selectedKeys"
                :input-id="NODE_SELECT_ID"
                selection-mode="checkbox"
                style="font-size: 1.2rem"
                :disabled="!hasSelectableNodes"
                filter
                :filter-placeholder="$gettext('Search nodes...')"
                :loading="props.loading"
                :placeholder="$gettext('Select node...')"
                :expanded-keys="expandedKeys"
                :options="nodeOptions"
                class="node-selection__select"
                @update:model-value="onKeysChanged"
            >
                <template #value="{ value: selectedNodes, placeholder }">
                    <span v-if="selectedNodes && selectedNodes.length > 0">
                        {{ selectedNodes[0].label }}
                    </span>
                    <span v-else>{{ placeholder }}</span>
                </template>
            </TreeSelect>
        </div>

        <div class="node-selection__chips">
            <Chip
                v-if="props.modelValue.length === 0"
                :label="$gettext('All date nodes')"
                class="node-selection__chip"
            />
            <Chip
                v-for="alias in props.modelValue"
                :key="alias"
                :label="nodePathByAlias[alias] ?? alias"
                removable
                remove-icon="pi pi-times"
                class="node-selection__chip"
                @remove="removeNode(alias)"
            />
        </div>
    </div>
</template>

<style scoped>
.node-selection {
    display: flex;
    flex-direction: column;
    gap: 0.9375rem;
}

.node-selection__attribute-row {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 0.875rem;
}

.node-selection__attribute-label {
    font-size: 1.25rem;
    font-weight: 600;
    line-height: 1.35;
    color: var(--p-text-color);
    white-space: nowrap;
}

.node-selection__select {
    flex: 0 1 auto;
    inline-size: min(100%, 22rem);
}

.node-selection__chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.625rem;
}

.node-selection__chip {
    border-radius: 0.4rem;
    min-block-size: 3rem;
    padding-block: 0.6875rem;
    padding-inline: 1.125rem;
    gap: 0.875rem;
    font-size: var(--time-filter-chip-size, 1.125rem);
}

.node-selection__chip :deep(.p-chip-remove-icon) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    inline-size: auto;
    block-size: auto;
    border-radius: 0;
    margin-inline-start: 0.75rem;
    font-size: var(--time-filter-chip-size, 1.125rem);
}

.node-selection__chip :deep(.p-chip-label) {
    font-size: var(--time-filter-chip-size, 1.125rem);
}
</style>
