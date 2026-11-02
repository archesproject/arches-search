<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import cytoscape from "cytoscape";

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
import type { GraphTheme } from "@/arches_search/RelationshipGraph/utils/graph-style.ts";

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

defineExpose({ fitToGraph });

const { $gettext } = useGettext();
const { colorFor } = useGraphColors();

const containerElement = ref<HTMLDivElement | null>(null);
// The node or edge whose details are on show; their ids cannot clash, as one
// is a resource's and the other a relationship's
const selectedId = ref<string | null>(null);
const popupAnchor = ref<PopupAnchor | null>(null);
const stageSize = ref({ width: 0, height: 0 });

const selectedNode = computed<GraphNode | null>(
    () => nodes.find((node) => node.id === selectedId.value) ?? null,
);

const selectedEdge = computed<GraphEdge | null>(
    () => edges.find((edge) => edge.id === selectedId.value) ?? null,
);

const popupLabel = computed<string>(() =>
    selectedEdge.value
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
let themeObserver: MutationObserver | null = null;
let theme: GraphTheme | null = null;

watch(() => [nodes, edges], applyGraph);

onMounted(() => {
    if (!containerElement.value) return;

    registerCytoscapeLayouts();
    theme = readGraphTheme(containerElement.value);
    cy = cytoscape({
        container: containerElement.value,
        style: buildGraphStylesheet(theme),
        minZoom: MIN_ZOOM,
        maxZoom: MAX_ZOOM,
        wheelSensitivity: WHEEL_SENSITIVITY,
    });

    cy.on("tap", "node, edge", (event) => selectElement(event.target.id()));
    cy.on("tap", (event) => {
        if (event.target === cy) closePopup();
    });
    // Fires for every change to what is on screen: panning, zooming, a node
    // being dragged, a layout moving things
    cy.on("render", scheduleAnchorUpdate);
    document.addEventListener("keydown", onKeydown);

    // The canvas cannot follow the page's CSS, so a switch between the light
    // and dark theme, which is a class on the page, has to be passed on to it
    themeObserver = new MutationObserver(applyTheme);
    themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["class"],
    });

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
    themeObserver?.disconnect();
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

function applyTheme(): void {
    if (!cy || !containerElement.value) return;

    // The page's class changes for other reasons than the theme too
    const nextTheme = readGraphTheme(containerElement.value);
    const isUnchanged = (Object.keys(nextTheme) as (keyof GraphTheme)[]).every(
        (key) => nextTheme[key] === theme?.[key],
    );
    if (isUnchanged) return;

    theme = nextTheme;
    cy.style(buildGraphStylesheet(theme));
}

// Whether the user has asked for less movement, which the graph settling into
// place and sliding to fit is plenty of
function prefersReducedMotion(): boolean {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function measureStage(): void {
    if (!containerElement.value) return;
    stageSize.value = {
        width: containerElement.value.clientWidth,
        height: containerElement.value.clientHeight,
    };
}

function selectElement(id: string): void {
    if (!cy) return;

    cy.elements().unselect();
    cy.getElementById(id).select();
    selectedId.value = id;
    updateAnchor();
}

function closePopup(): void {
    selectedId.value = null;
    popupAnchor.value = null;
    cy?.elements().unselect();
}

function onKeydown(event: KeyboardEvent): void {
    if (event.key === "Escape" && selectedId.value) closePopup();
}

function scheduleAnchorUpdate(): void {
    if (!selectedId.value || anchorFrame !== null) return;

    anchorFrame = requestAnimationFrame(() => {
        anchorFrame = null;
        updateAnchor();
    });
}

function updateAnchor(): void {
    if (!cy || !selectedId.value) return;

    const element = cy.getElementById(selectedId.value);
    if (element.empty()) {
        closePopup();
        return;
    }

    let anchor: PopupAnchor;
    if (element.group() === "nodes") {
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
        animate: !prefersReducedMotion(),
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
        duration: prefersReducedMotion() ? 0 : RECENTER_DURATION_MS,
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
        <GraphPopup
            v-if="selectedId && popupAnchor"
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
</style>
