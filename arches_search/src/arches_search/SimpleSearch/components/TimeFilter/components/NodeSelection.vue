<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Chip from "primevue/chip";
import TreeSelect from "primevue/treeselect";

import type {
    TimeFilterNodeSummary,
    TimeFilterTreeNode,
} from "@/arches_search/SimpleSearch/components/TimeFilter/types.ts";

const UPDATE_EVENT = "update:modelValue" as const;
const DATE_DATATYPES = ["date", "edtf"] as const;

const props = defineProps<{
    graphLabel: string | null;
    loading: boolean;
    modelValue: string[];
    nodes: TimeFilterNodeSummary[];
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_EVENT, value: string[]): void;
}>();

const { $gettext, interpolate } = useGettext();
const NODE_SELECT_ID = "simple-search-time-filter-node-selection" as const;

const transientSelectedKeys = ref<Record<string, boolean>>({});

const nodeOptions = computed<TimeFilterTreeNode[]>(() =>
    buildTree(props.nodes),
);

const hasSelectableNodes = computed<boolean>(() => {
    return hasSelectableNode(nodeOptions.value);
});

const expandedKeys = computed<Record<string, boolean>>(() => {
    const allExpandedKeys: Record<string, boolean> = {};
    const nodesToVisit = [...nodeOptions.value];

    while (nodesToVisit.length > 0) {
        const currentNode = nodesToVisit.pop()!;
        allExpandedKeys[currentNode.key] = true;
        nodesToVisit.push(...currentNode.children);
    }

    return allExpandedKeys;
});

const nodeLabelByAlias = computed<Record<string, string>>(() => {
    return Object.fromEntries(
        props.nodes.map((node) => [node.alias, getNodeDisplayLabel(node)]),
    );
});

const selectedKeys = computed<Record<string, boolean>>({
    get(): Record<string, boolean> {
        return transientSelectedKeys.value;
    },
    set(newSelectionKeys: unknown): void {
        transientSelectedKeys.value = Object(newSelectionKeys) as Record<
            string,
            boolean
        >;

        const selectedKey =
            Object.keys(transientSelectedKeys.value).find((key) => {
                return transientSelectedKeys.value[key] === true;
            }) ?? null;

        const matchingNode = selectedKey
            ? findNode(nodeOptions.value, (node) => node.key === selectedKey)
            : null;

        if (matchingNode && matchingNode.selectable !== false) {
            const nextAlias = matchingNode.data.alias;

            if (!props.modelValue.includes(nextAlias)) {
                emit(UPDATE_EVENT, [...props.modelValue, nextAlias]);
            }
        }

        void nextTick(() => {
            transientSelectedKeys.value = {};
        });
    },
});

function hasSelectableNode(nodes: TimeFilterTreeNode[]): boolean {
    return nodes.some((node) => {
        return node.selectable !== false || hasSelectableNode(node.children);
    });
}

function findNode(
    nodes: TimeFilterTreeNode[],
    predicate: (node: TimeFilterTreeNode) => boolean,
): TimeFilterTreeNode | null {
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

function isNodeSelectable(node: TimeFilterNodeSummary): boolean {
    return (DATE_DATATYPES as readonly string[]).includes(node.datatype);
}

function getNodeDisplayLabel(node: TimeFilterNodeSummary): string {
    return node.card_x_node_x_widget_label || node.name || node.alias;
}

function buildTree(
    nodeSummaries: TimeFilterNodeSummary[],
): TimeFilterTreeNode[] {
    const nodeKeyToPathNode: Record<string, TimeFilterTreeNode> = {};
    const roots: TimeFilterTreeNode[] = [];

    for (const nodeSummary of nodeSummaries) {
        nodeKeyToPathNode[nodeSummary.id] = {
            key: nodeSummary.id,
            label: getNodeDisplayLabel(nodeSummary),
            data: nodeSummary,
            children: [],
            selectable: isNodeSelectable(nodeSummary),
        };
    }

    for (const nodeSummary of nodeSummaries) {
        const treeNode = nodeKeyToPathNode[nodeSummary.id]!;

        if (nodeSummary.semantic_parent_id) {
            const parentNode =
                nodeKeyToPathNode[nodeSummary.semantic_parent_id];
            (parentNode?.children ?? roots).push(treeNode);
        } else {
            roots.push(treeNode);
        }
    }

    // Card-group wrapper nodes share the same alias as their first child.
    for (const node of Object.values(nodeKeyToPathNode)) {
        if (
            node.children.some((child) => {
                return child.data.alias === node.data.alias;
            })
        ) {
            node.selectable = false;
        }
    }

    function compareNodes(
        leftNode: TimeFilterTreeNode,
        rightNode: TimeFilterTreeNode,
    ): number {
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

    function pruneUnselectable(
        nodes: TimeFilterTreeNode[],
    ): TimeFilterTreeNode[] {
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

function getNodeLabel(alias: string): string {
    return nodeLabelByAlias.value[alias] ?? alias;
}

function removeNode(alias: string): void {
    emit(
        UPDATE_EVENT,
        props.modelValue.filter((value) => value !== alias),
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
                v-model="selectedKeys"
                :input-id="NODE_SELECT_ID"
                selection-mode="single"
                style="font-size: 1.2rem"
                :disabled="!hasSelectableNodes"
                filter
                :filter-placeholder="$gettext('Search nodes...')"
                :loading="props.loading"
                :placeholder="$gettext('Select node...')"
                :expanded-keys="expandedKeys"
                :options="nodeOptions"
                class="node-selection__select"
            >
                <template #value="valueSlotProps">
                    <span
                        v-if="
                            valueSlotProps.value &&
                            valueSlotProps.value.length > 0
                        "
                    >
                        {{ valueSlotProps.value[0].label }}
                    </span>
                    <span v-else>{{ valueSlotProps.placeholder }}</span>
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
                :label="getNodeLabel(alias)"
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
