<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";

import GraphCanvas from "@/arches_search/RelationshipViewer/components/GraphCanvas.vue";
import GraphLegend from "@/arches_search/RelationshipViewer/components/GraphLegend.vue";
import NodeDetailsPanel from "@/arches_search/RelationshipViewer/components/NodeDetailsPanel.vue";
import { fetchRelationshipGraph } from "@/arches_search/RelationshipViewer/api.ts";
import type {
    GraphData,
    GraphNode,
    GraphTypeGroup,
    RelationshipType,
} from "@/arches_search/RelationshipViewer/types.ts";

const PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
];

const props = defineProps<{
    resourceIds: string[];
}>();

const { $gettext } = useGettext();
const toast = useToast();

// -- Graph data --
const graphData = ref<GraphData>({ nodes: [], edges: [], relationship_types: [] });
const loading = ref(false);

// -- Controls state --
const depth = ref<1 | 2>(1);
const enabledRelTypeIds = ref<Set<string>>(new Set());
const hiddenSlugs = ref<Set<string | null>>(new Set());
const highlightedSlugs = ref<Set<string | null>>(new Set());
const showRelTypeMenu = ref(false);

// -- Interaction state --
const selectedNodeId = ref<string | null>(null);
const pathfindMode = ref(false);
const pathfindSourceId = ref<string | null>(null);
const highlightedPath = ref<string[]>([]);

const canvasRef = ref<InstanceType<typeof GraphCanvas> | null>(null);

// -- Color map (stable across re-renders) --
const colorMap = new Map<string | null, string>();
let paletteIdx = 0;

function resolveColor(node: GraphNode): string {
    if (node.graph_color) return node.graph_color;
    const key = node.graph_slug;
    if (!colorMap.has(key)) {
        colorMap.set(key, PALETTE[paletteIdx % PALETTE.length]);
        paletteIdx++;
    }
    return colorMap.get(key)!;
}

const legendGroups = computed<GraphTypeGroup[]>(() => {
    const bySlug = new Map<string | null, GraphTypeGroup>();
    for (const node of graphData.value.nodes) {
        if (!bySlug.has(node.graph_slug)) {
            bySlug.set(node.graph_slug, {
                slug: node.graph_slug,
                name: node.graph_name,
                color: resolveColor(node),
                count: 0,
                hidden: hiddenSlugs.value.has(node.graph_slug),
                highlighted: highlightedSlugs.value.has(node.graph_slug),
            });
        }
        bySlug.get(node.graph_slug)!.count++;
    }
    return Array.from(bySlug.values()).sort((a, b) => b.count - a.count);
});

const selectedNode = computed<GraphNode | null>(
    () => graphData.value.nodes.find((n) => n.id === selectedNodeId.value) ?? null,
);

// -- Data loading --
async function loadGraph(extraIds: string[] = []) {
    const ids = [...new Set([...props.resourceIds, ...extraIds])];
    if (!ids.length) {
        graphData.value = { nodes: [], edges: [], relationship_types: [] };
        return;
    }
    loading.value = true;
    try {
        graphData.value = await fetchRelationshipGraph({
            resourceIds: ids,
            depth: depth.value,
            relationshipTypes:
                enabledRelTypeIds.value.size > 0
                    ? Array.from(enabledRelTypeIds.value)
                    : [],
        });
    } catch (err) {
        toast.add({
            severity: "error",
            life: 5000,
            summary: $gettext("Failed to load relationship graph"),
            detail: err instanceof Error ? err.message : undefined,
        });
    } finally {
        loading.value = false;
    }
}

watch(() => props.resourceIds, () => loadGraph(), { immediate: true });
watch(depth, () => loadGraph());

// -- Legend --
function onToggleSlug(slug: string | null) {
    const next = new Set(hiddenSlugs.value);
    if (next.has(slug)) {
        next.delete(slug);
    } else {
        next.add(slug);
    }
    hiddenSlugs.value = next;
}

function onIsolateSlug(slug: string | null) {
    const all = new Set(legendGroups.value.map((g) => g.slug));
    all.delete(slug);
    hiddenSlugs.value = all;
}

function onHighlightSlug(slug: string | null) {
    const next = new Set(highlightedSlugs.value);
    if (next.has(slug)) {
        next.delete(slug);
    } else {
        next.add(slug);
    }
    highlightedSlugs.value = next;
}

// -- Rel-type filter --
function toggleRelType(id: string) {
    const next = new Set(enabledRelTypeIds.value);
    if (next.has(id)) {
        next.delete(id);
    } else {
        next.add(id);
    }
    enabledRelTypeIds.value = next;
}

function isRelTypeEnabled(id: string): boolean {
    return enabledRelTypeIds.value.size === 0 || enabledRelTypeIds.value.has(id);
}

// -- Node interaction --
function onNodeClick(nodeId: string) {
    selectedNodeId.value = nodeId === selectedNodeId.value ? null : nodeId;
}

function onCanvasClick() {
    selectedNodeId.value = null;
}

// -- Path finding --
function togglePathfindMode() {
    pathfindMode.value = !pathfindMode.value;
    pathfindSourceId.value = null;
    highlightedPath.value = [];
}

function onPathfindNodeSelect(nodeId: string) {
    if (!pathfindSourceId.value) {
        pathfindSourceId.value = nodeId;
        return;
    }
    if (nodeId === pathfindSourceId.value) {
        pathfindSourceId.value = null;
        return;
    }
    highlightedPath.value = findShortestPath(
        pathfindSourceId.value,
        nodeId,
        graphData.value.edges,
    );
    if (!highlightedPath.value.length) {
        toast.add({
            severity: "info",
            life: 3000,
            summary: $gettext("No path found between these nodes in the loaded graph."),
        });
    }
    pathfindMode.value = false;
    pathfindSourceId.value = null;
}

function clearPath() {
    highlightedPath.value = [];
    pathfindSourceId.value = null;
    pathfindMode.value = false;
}

function onExpandNode(nodeId: string) {
    void loadGraph([nodeId]);
}

function findShortestPath(
    sourceId: string,
    targetId: string,
    edges: GraphData["edges"],
): string[] {
    const adj = new Map<string, string[]>();
    for (const edge of edges) {
        if (!adj.has(edge.source)) adj.set(edge.source, []);
        if (!adj.has(edge.target)) adj.set(edge.target, []);
        adj.get(edge.source)!.push(edge.target);
        adj.get(edge.target)!.push(edge.source);
    }
    const queue: string[][] = [[sourceId]];
    const visited = new Set<string>([sourceId]);
    while (queue.length) {
        const path = queue.shift()!;
        const node = path[path.length - 1];
        if (node === targetId) return path;
        for (const neighbor of adj.get(node) ?? []) {
            if (!visited.has(neighbor)) {
                visited.add(neighbor);
                queue.push([...path, neighbor]);
            }
        }
    }
    return [];
}
</script>

<template>
    <div class="relationship-viewer">
        <!-- Compact toolbar strip -->
        <div class="rv-toolbar">
            <div class="rv-toolbar-left">
                <span class="rv-title">Relationships</span>
                <button
                    :class="{ active: depth === 1 }"
                    class="depth-btn"
                    @click="depth = 1"
                >
                    1 hop
                </button>
                <button
                    :class="{ active: depth === 2 }"
                    class="depth-btn"
                    @click="depth = 2"
                >
                    2 hops
                </button>
            </div>
            <div class="rv-toolbar-right">
                <span class="rv-stat">
                    {{ graphData.nodes.length }}N · {{ graphData.edges.length }}E
                </span>
                <Button
                    v-if="graphData.relationship_types.length"
                    icon="pi pi-sliders-h"
                    size="small"
                    text
                    rounded
                    :class="{ active: enabledRelTypeIds.size > 0 }"
                    :title="$gettext('Filter relationship types')"
                    @click="showRelTypeMenu = !showRelTypeMenu"
                />
                <Button
                    icon="pi pi-directions"
                    size="small"
                    text
                    rounded
                    :class="{ active: pathfindMode }"
                    :title="
                        pathfindMode
                            ? $gettext('Cancel path find')
                            : $gettext('Find shortest path')
                    "
                    @click="togglePathfindMode"
                />
                <Button
                    icon="pi pi-arrows-alt"
                    size="small"
                    text
                    rounded
                    :title="$gettext('Re-center graph')"
                    @click="canvasRef?.recenter()"
                />
                <Button
                    icon="pi pi-refresh"
                    size="small"
                    text
                    rounded
                    :loading="loading"
                    :title="$gettext('Reload graph')"
                    @click="loadGraph()"
                />
            </div>
        </div>

        <!-- Rel-type filter dropdown (inline, toggled) -->
        <div
            v-if="showRelTypeMenu && graphData.relationship_types.length"
            class="rel-type-menu"
        >
            <div class="rel-type-menu-title">
                Relationship Types
                <button
                    class="all-btn"
                    @click="enabledRelTypeIds = new Set()"
                >
                    All
                </button>
            </div>
            <label
                v-for="rt in (graphData.relationship_types as RelationshipType[])"
                :key="rt.id"
                class="rel-type-row"
            >
                <input
                    type="checkbox"
                    :checked="isRelTypeEnabled(rt.id)"
                    @change="toggleRelType(rt.id)"
                />
                <span class="rt-label">{{ rt.label }}</span>
                <span class="rt-count">{{ rt.count }}</span>
            </label>
        </div>

        <!-- Canvas area -->
        <div class="canvas-area">
            <div
                v-if="loading"
                class="canvas-state"
            >
                <i class="pi pi-spin pi-spinner" />
                <span>{{ $gettext("Loading…") }}</span>
            </div>

            <div
                v-else-if="!graphData.nodes.length"
                class="canvas-state"
            >
                <i class="pi pi-sitemap" />
                <p>
                    {{
                        props.resourceIds.length
                            ? $gettext("No relationships found for the current results.")
                            : $gettext("Run a search to visualize relationships.")
                    }}
                </p>
            </div>

            <GraphCanvas
                v-else
                ref="canvasRef"
                :nodes="graphData.nodes"
                :edges="graphData.edges"
                :hidden-slugs="hiddenSlugs"
                :enabled-rel-type-ids="enabledRelTypeIds"
                :highlighted-path="highlightedPath"
                :selected-node-id="selectedNodeId"
                :pathfind-mode="pathfindMode"
                :pathfind-source-id="pathfindSourceId"
                :highlighted-slugs="highlightedSlugs"
                @node-click="onNodeClick"
                @canvas-click="onCanvasClick"
                @pathfind-node-select="onPathfindNodeSelect"
            />

            <!-- Legend overlay -->
            <div
                v-if="legendGroups.length && !loading"
                class="legend-overlay"
            >
                <GraphLegend
                    :groups="legendGroups"
                    @toggle="onToggleSlug"
                    @highlight="onHighlightSlug"
                />
            </div>

            <!-- Path highlight banner -->
            <div
                v-if="highlightedPath.length"
                class="path-banner"
            >
                <i class="pi pi-directions" />
                {{ highlightedPath.length }} nodes
                <button @click="clearPath">✕</button>
            </div>

            <!-- Pathfind mode hint -->
            <div
                v-if="pathfindMode"
                class="pathfind-banner"
            >
                <i class="pi pi-directions" />
                {{
                    pathfindSourceId
                        ? $gettext("Now click the destination node.")
                        : $gettext("Click a start node.")
                }}
            </div>
        </div>

        <!-- Node details panel (slide in from bottom) -->
        <div
            v-if="selectedNode"
            class="node-details-overlay"
        >
            <NodeDetailsPanel
                :node="selectedNode"
                @close="selectedNodeId = null"
                @expand-node="onExpandNode"
            />
        </div>
    </div>
</template>

<style scoped>
.relationship-viewer {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    font-size: var(--p-arches-search-font-size, 13px);
}

.rv-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 10px;
    border-bottom: 1px solid var(--p-content-border-color, #e0e0e0);
    flex-shrink: 0;
    gap: 6px;
    background: var(--p-content-background, #fff);
}

.rv-toolbar-left {
    display: flex;
    align-items: center;
    gap: 6px;
}

.rv-toolbar-right {
    display: flex;
    align-items: center;
    gap: 2px;
}

.rv-title {
    font-weight: 600;
    color: var(--p-primary-color, #25476a);
    font-size: 12px;
    white-space: nowrap;
}

.rv-stat {
    font-size: 11px;
    color: #888;
    white-space: nowrap;
    padding-right: 4px;
}

.depth-btn {
    padding: 2px 8px;
    border: 1px solid #ccc;
    border-radius: 12px;
    background: #fff;
    cursor: pointer;
    font-size: 11px;
    transition: background 0.15s, color 0.15s;
    color: #444;
}

.depth-btn.active {
    background: var(--p-primary-color, #25476a);
    color: #fff;
    border-color: var(--p-primary-color, #25476a);
}

.rv-toolbar :deep(.p-button) {
    color: #555;
}

.rv-toolbar :deep(.p-button.active) {
    color: var(--p-primary-color, #25476a);
    background: var(--p-highlight-background, #e8f0fa);
}

.rel-type-menu {
    padding: 8px 12px;
    border-bottom: 1px solid var(--p-content-border-color, #e0e0e0);
    background: var(--p-content-background, #fff);
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
    max-height: 200px;
    overflow-y: auto;
}

.rel-type-menu-title {
    font-weight: 600;
    font-size: 11px;
    color: #25476a;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;
}

.all-btn {
    font-size: 10px;
    border: 1px solid #ccc;
    border-radius: 10px;
    padding: 1px 7px;
    cursor: pointer;
    background: #f5f5f5;
    color: #555;
}

.rel-type-row {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    font-size: 12px;
}

.rt-label {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.rt-count {
    font-size: 10px;
    color: #666;
    font-weight: 600;
}

.canvas-area {
    flex: 1;
    position: relative;
    overflow: hidden;
}

.canvas-state {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: #999;
    font-size: 13px;
    background: #f5f7fa;
}

.canvas-state .pi-spinner {
    font-size: 1.8rem;
    color: #25476a;
}

.canvas-state .pi-sitemap {
    font-size: 2rem;
    color: #ccc;
}

.legend-overlay {
    position: absolute;
    bottom: 12px;
    left: 10px;
    z-index: 10;
}

.path-banner {
    position: absolute;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(225, 87, 89, 0.92);
    color: #fff;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
    z-index: 10;
}

.path-banner button {
    background: none;
    border: none;
    color: #fff;
    cursor: pointer;
    font-size: 12px;
    line-height: 1;
}

.pathfind-banner {
    position: absolute;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(37, 71, 106, 0.9);
    color: #fff;
    padding: 5px 14px;
    border-radius: 16px;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    z-index: 10;
    white-space: nowrap;
}

.node-details-overlay {
    flex-shrink: 0;
    max-height: 40%;
    overflow-y: auto;
    border-top: 1px solid var(--p-content-border-color, #e0e0e0);
}
</style>
