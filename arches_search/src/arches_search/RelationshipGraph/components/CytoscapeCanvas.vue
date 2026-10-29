<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import cytoscape from "cytoscape";
import Button from "openvue/button";

import { useGraphColors } from "@/arches_search/RelationshipGraph/composables/useGraphColors.ts";
import {
    toEdgeElement,
    toNodeElement,
} from "@/arches_search/RelationshipGraph/utils/graph-elements.ts";
import {
    buildGraphStylesheet,
    readGraphTheme,
} from "@/arches_search/RelationshipGraph/utils/graph-style.ts";
import { registerCytoscapeLayouts } from "@/arches_search/RelationshipGraph/utils/register-cytoscape-layouts.ts";
import { syncGraphElements } from "@/arches_search/RelationshipGraph/utils/sync-graph-elements.ts";

import type { Core, LayoutOptions, Layouts } from "cytoscape";
import type {
    GraphEdge,
    GraphNode,
} from "@/arches_search/RelationshipGraph/types.ts";

const MIN_ZOOM = 0.1;
const MAX_ZOOM = 3;
const WHEEL_SENSITIVITY = 0.3;
const FIT_PADDING = 30;
const RECENTER_DURATION_MS = 300;
const LAYOUT_EDGE_LENGTH = 120;
const LAYOUT_NODE_SPACING = 16;
const LAYOUT_MAX_SIMULATION_MS = 2500;

const { nodes, edges } = defineProps<{
    nodes: GraphNode[];
    edges: GraphEdge[];
}>();

const { $gettext } = useGettext();
const { colorFor } = useGraphColors();

const containerElement = ref<HTMLDivElement | null>(null);

// Cytoscape owns these, and Vue must not wrap them in proxies
let cy: Core | null = null;
let activeLayout: Layouts | null = null;
let resizeObserver: ResizeObserver | null = null;
let hasLaidOut = false;

watch(() => [nodes, edges], applyGraph);

onMounted(() => {
    if (!containerElement.value) return;

    registerCytoscapeLayouts();
    cy = cytoscape({
        container: containerElement.value,
        style: buildGraphStylesheet(readGraphTheme(containerElement.value)),
        minZoom: MIN_ZOOM,
        maxZoom: MAX_ZOOM,
        wheelSensitivity: WHEEL_SENSITIVITY,
    });

    resizeObserver = new ResizeObserver(() => cy?.resize());
    resizeObserver.observe(containerElement.value);

    applyGraph();
});

onBeforeUnmount(() => {
    resizeObserver?.disconnect();
    activeLayout?.stop();
    cy?.destroy();
    cy = null;
    activeLayout = null;
    resizeObserver = null;
});

function applyGraph(): void {
    if (!cy) return;

    const isPathShown =
        nodes.some((node) => node.on_path) ||
        edges.some((edge) => edge.on_path);
    const { addedNodeIds } = syncGraphElements(
        cy,
        nodes.map((node) =>
            toNodeElement(node, colorFor(node.model), isPathShown),
        ),
        edges.map((edge) => toEdgeElement(edge, isPathShown)),
    );
    if (addedNodeIds.length > 0) {
        runLayout(addedNodeIds);
    }
}

// Lays out only what is new: the nodes already on the canvas stay put while
// the new ones settle around them, so adding a relationship never rearranges
// the graph the user is looking at.
function runLayout(addedNodeIds: string[]): void {
    if (!cy) return;

    activeLayout?.stop();

    const addedIds = new Set(addedNodeIds);
    cy.nodes()
        .filter((node) => !addedIds.has(node.id()))
        .lock();

    // The first layout frames the whole graph. Later ones leave the view alone
    // unless a new node would be out of sight, so adding a relationship does
    // not move the graph under the user for no reason. Until a layout has
    // finished and framed it, a layout that replaces another still does so.
    const shouldFit = !hasLaidOut;

    // Not a literal: the layout options of an extension are not typed
    const layoutOptions = {
        name: "cola",
        animate: true,
        randomize: false,
        fit: false,
        edgeLength: LAYOUT_EDGE_LENGTH,
        nodeSpacing: LAYOUT_NODE_SPACING,
        avoidOverlap: true,
        handleDisconnected: true,
        maxSimulationTime: LAYOUT_MAX_SIMULATION_MS,
    };
    const layout = cy.layout(layoutOptions as LayoutOptions);
    layout.one("layoutstop", () => {
        // A layout that was stopped to make way for a newer one must not
        // unlock what the newer one has locked
        if (layout !== activeLayout) return;
        cy?.nodes().unlock();
        if (shouldFit) {
            cy?.fit(undefined, FIT_PADDING);
            hasLaidOut = true;
        } else if (isOutOfView(addedIds)) {
            fitToGraph();
        }
    });
    activeLayout = layout;
    layout.run();
}

function isOutOfView(nodeIds: Set<string>): boolean {
    if (!cy) return false;

    const view = cy.extent();
    return cy
        .nodes()
        .toArray()
        .some((node) => {
            if (!nodeIds.has(node.id())) return false;
            const box = node.boundingBox();
            return (
                box.x1 < view.x1 ||
                box.y1 < view.y1 ||
                box.x2 > view.x2 ||
                box.y2 > view.y2
            );
        });
}

function fitToGraph(): void {
    cy?.animate({
        fit: { eles: cy.elements(), padding: FIT_PADDING },
        duration: RECENTER_DURATION_MS,
    });
}
</script>

<template>
    <div class="cytoscape-canvas">
        <div
            ref="containerElement"
            class="canvas"
            role="img"
            :aria-label="$gettext('Relationship graph')"
        />
        <Button
            class="recenter"
            severity="secondary"
            size="small"
            icon="pi pi-arrows-alt"
            :aria-label="$gettext('Fit the graph to the panel')"
            :title="$gettext('Fit the graph to the panel')"
            @click="fitToGraph"
        />
    </div>
</template>

<style scoped>
.cytoscape-canvas {
    position: relative;
    inline-size: 100%;
    block-size: 100%;
    background-color: var(--arches-search-page-bg);
}

.cytoscape-canvas .canvas {
    inline-size: 100%;
    block-size: 100%;
}

.cytoscape-canvas .recenter {
    position: absolute;
    inset-block-start: 0.8rem;
    inset-inline-end: 0.8rem;
}
</style>
