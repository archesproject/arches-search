<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import cytoscape from "cytoscape";
import Button from "openvue/button";

import EdgeDetailsPopup from "@/arches_search/RelationshipGraph/components/EdgeDetailsPopup.vue";
import GraphPopup from "@/arches_search/RelationshipGraph/components/GraphPopup.vue";
import NodeDetailsPopup from "@/arches_search/RelationshipGraph/components/NodeDetailsPopup.vue";
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

interface SelectedElement {
    kind: "node" | "edge";
    id: string;
}

// Where the selected element is on the canvas, and how far a popup about it
// has to keep to stay off it
interface PopupAnchor {
    x: number;
    y: number;
    clearance: number;
}

const MIN_ZOOM = 0.1;
const MAX_ZOOM = 3;
const WHEEL_SENSITIVITY = 0.3;
const FIT_PADDING = 30;
const RECENTER_DURATION_MS = 300;
const LAYOUT_EDGE_LENGTH = 120;
const LAYOUT_NODE_SPACING = 16;
const LAYOUT_MAX_SIMULATION_MS = 2500;
const POPUP_GAP = 8;

const { nodes, edges } = defineProps<{
    nodes: GraphNode[];
    edges: GraphEdge[];
}>();

const { $gettext } = useGettext();
const { colorFor } = useGraphColors();

const containerElement = ref<HTMLDivElement | null>(null);
const selectedElement = ref<SelectedElement | null>(null);
const popupAnchor = ref<PopupAnchor | null>(null);
const stageSize = ref({ width: 0, height: 0 });

const selectedNode = computed<GraphNode | null>(() =>
    selectedElement.value?.kind === "node"
        ? nodes.find((node) => node.id === selectedElement.value?.id) ?? null
        : null,
);

const selectedEdge = computed<GraphEdge | null>(() =>
    selectedElement.value?.kind === "edge"
        ? edges.find((edge) => edge.id === selectedElement.value?.id) ?? null
        : null,
);

const popupLabel = computed<string>(() =>
    selectedElement.value?.kind === "edge"
        ? $gettext("Relationship details")
        : $gettext("Resource details"),
);

function nameOf(resourceId: string): string {
    return nodes.find((node) => node.id === resourceId)?.name ?? "";
}

// Cytoscape owns these, and Vue must not wrap them in proxies
let cy: Core | null = null;
let activeLayout: Layouts | null = null;
let resizeObserver: ResizeObserver | null = null;
let hasLaidOut = false;
let anchorFrame: number | null = null;

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

    cy.on("tap", "node", (event) => selectElement("node", event.target.id()));
    cy.on("tap", "edge", (event) => selectElement("edge", event.target.id()));
    cy.on("tap", (event) => {
        if (event.target === cy) closePopup();
    });
    // Fires for every change to what is on screen: panning, zooming, a node
    // being dragged, a layout moving things
    cy.on("render", scheduleAnchorUpdate);
    document.addEventListener("keydown", onKeydown);

    resizeObserver = new ResizeObserver(() => {
        cy?.resize();
        measureStage();
    });
    resizeObserver.observe(containerElement.value);
    measureStage();

    applyGraph();
});

onBeforeUnmount(() => {
    if (anchorFrame !== null) cancelAnimationFrame(anchorFrame);
    document.removeEventListener("keydown", onKeydown);
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
    // What was selected may be gone
    updateAnchor();
}

function measureStage(): void {
    if (!containerElement.value) return;
    stageSize.value = {
        width: containerElement.value.clientWidth,
        height: containerElement.value.clientHeight,
    };
}

function selectElement(kind: SelectedElement["kind"], id: string): void {
    if (!cy) return;

    cy.elements().unselect();
    cy.getElementById(id).select();
    selectedElement.value = { kind, id };
    updateAnchor();
}

function closePopup(): void {
    selectedElement.value = null;
    popupAnchor.value = null;
    cy?.elements().unselect();
}

function onKeydown(event: KeyboardEvent): void {
    if (event.key === "Escape" && selectedElement.value) closePopup();
}

function scheduleAnchorUpdate(): void {
    if (!selectedElement.value || anchorFrame !== null) return;

    anchorFrame = requestAnimationFrame(() => {
        anchorFrame = null;
        updateAnchor();
    });
}

function updateAnchor(): void {
    if (!cy || !selectedElement.value) return;

    const element = cy.getElementById(selectedElement.value.id);
    if (element.empty()) {
        closePopup();
        return;
    }

    let anchor: PopupAnchor;
    if (selectedElement.value.kind === "node") {
        const position = element.renderedPosition();
        anchor = {
            x: position.x,
            y: position.y,
            clearance: element.renderedWidth() / 2 + POPUP_GAP,
        };
    } else {
        const midpoint = element.renderedMidpoint();
        anchor = { x: midpoint.x, y: midpoint.y, clearance: POPUP_GAP };
    }

    // A frame in which nothing moved should not redraw the popup
    const current = popupAnchor.value;
    if (
        !current ||
        current.x !== anchor.x ||
        current.y !== anchor.y ||
        current.clearance !== anchor.clearance
    ) {
        popupAnchor.value = anchor;
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
        <GraphPopup
            v-if="selectedElement && popupAnchor"
            :anchor-x="popupAnchor.x"
            :anchor-y="popupAnchor.y"
            :clearance="popupAnchor.clearance"
            :stage-width="stageSize.width"
            :stage-height="stageSize.height"
            :label="popupLabel"
            @close="closePopup"
        >
            <NodeDetailsPopup
                v-if="selectedNode"
                :resource-id="selectedNode.id"
                :name="selectedNode.name"
                :model-name="selectedNode.model.name"
                :model-color="colorFor(selectedNode.model)"
                :related-count="selectedNode.related_count"
            />
            <EdgeDetailsPopup
                v-else-if="selectedEdge"
                :source-name="nameOf(selectedEdge.source)"
                :target-name="nameOf(selectedEdge.target)"
                :relationship-type-label="selectedEdge.relationship_type_label"
                :inverse-label="selectedEdge.inverse_relationship_type_label"
                :notes="selectedEdge.notes"
            />
        </GraphPopup>
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
