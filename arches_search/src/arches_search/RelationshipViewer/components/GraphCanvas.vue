<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from "vue";
import * as d3 from "d3";
import type {
    SimNode,
    SimLink,
    GraphNode,
    GraphEdge,
} from "@/arches_search/RelationshipViewer/types.ts";

const PALETTE = [
    "#4e79a7",
    "#f28e2b",
    "#e15759",
    "#76b7b2",
    "#59a14f",
    "#edc948",
    "#b07aa1",
    "#ff9da7",
    "#9c755f",
    "#bab0ac",
];
const BASE_RADIUS = 10;
const MAX_RADIUS = 32;

const props = defineProps<{
    nodes: GraphNode[];
    edges: GraphEdge[];
    hiddenSlugs: Set<string | null>;
    enabledRelTypeIds: Set<string>;
    highlightedPath: string[]; // ordered list of node IDs on the found path
    selectedNodeId: string | null;
    pathfindMode: boolean;
    pathfindSourceId: string | null;
    highlightedSlugs: Set<string | null>;
}>();

const emit = defineEmits<{
    (e: "node-click", nodeId: string): void;
    (e: "node-dblclick", nodeId: string): void;
    (e: "canvas-click"): void;
    (e: "pathfind-node-select", nodeId: string): void;
}>();

const svgEl = ref<SVGSVGElement | null>(null);
const colorMap = new Map<string | null, string>();
let paletteIdx = 0;

function graphColor(node: GraphNode): string {
    if (node.graph_color) return node.graph_color;
    const key = node.graph_slug;
    if (!colorMap.has(key)) {
        colorMap.set(key, PALETTE[paletteIdx % PALETTE.length]);
        paletteIdx++;
    }
    return colorMap.get(key)!;
}

function nodeRadius(node: GraphNode): number {
    return Math.min(
        BASE_RADIUS + Math.sqrt(node.related_count) * 2.5,
        MAX_RADIUS,
    );
}

type D3Selection = ReturnType<typeof d3.select>;
type D3Simulation = ReturnType<typeof d3.forceSimulation>;

interface D3DragEvent {
    active: number;
    x: number;
    y: number;
}

interface D3ZoomEvent {
    transform: { toString(): string };
}

// ------- D3 mutable state (not Vue reactive) --------
let simulation: D3Simulation | null = null;
let svgSel: D3Selection | null = null;
let zoomGroup: D3Selection | null = null;
let linkSel: D3Selection | null = null;
let nodeSel: D3Selection | null = null;
let labelSel: D3Selection | null = null;
let subtitleSel: D3Selection | null = null;
let simNodes: SimNode[] = [];
let simLinks: SimLink[] = [];

function buildSimData() {
    // Preserve existing positions and pin status for nodes already in the sim
    const prevById = new Map(simNodes.map((n) => [n.id, n]));
    // Active rel-type filter: if the set is non-empty, it represents an explicit allow-list
    const relTypeActive = (id: string) =>
        props.enabledRelTypeIds.size === 0 || props.enabledRelTypeIds.has(id);

    simNodes = props.nodes.map((n) => {
        const prev = prevById.get(n.id);
        return Object.assign(
            {
                x: prev?.x ?? Math.random() * 600,
                y: prev?.y ?? Math.random() * 400,
                fx: prev?.fx ?? null,
                fy: prev?.fy ?? null,
                vx: 0,
                vy: 0,
            },
            n,
        ) as SimNode;
    });

    const nodeIds = new Set(simNodes.map((n) => n.id));

    simLinks = props.edges
        .filter((e) => {
            return (
                nodeIds.has(e.source) &&
                nodeIds.has(e.target) &&
                relTypeActive(e.relationship_type_id)
            );
        })
        .map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            relationship_type_id: e.relationship_type_id,
            relationship_type_label: e.relationship_type_label,
            tile_id: e.tile_id,
        })) as SimLink[];
}

function typeClass(node: SimNode): string {
    // Only apply when a highlight is active and no path is shown (path takes priority)
    if (props.highlightedSlugs.size === 0 || props.highlightedPath.length > 0)
        return "";
    return props.highlightedSlugs.has(node.graph_slug) ? "type-on" : "type-off";
}

function hiddenClass(node: SimNode): string {
    return props.hiddenSlugs.has(node.graph_slug) ? "slug-hidden" : "";
}

function nodeClass(node: SimNode): string {
    const classes: string[] = ["graph-node"];
    if (node.id === props.selectedNodeId) classes.push("selected");
    if (node.is_seed) classes.push("seed");
    if (props.highlightedPath.length > 0) {
        if (props.highlightedPath.includes(node.id)) {
            classes.push("on-path");
        } else {
            classes.push("off-path");
        }
    }
    if (props.pathfindMode) {
        if (node.id === props.pathfindSourceId) classes.push("pathfind-source");
        classes.push("pathfind-target");
    }
    const tc = typeClass(node);
    if (tc) classes.push(tc);
    const hc = hiddenClass(node);
    if (hc) classes.push(hc);
    return classes.join(" ");
}

function linkClass(link: SimLink): string {
    const sourceId =
        typeof link.source === "string" ? link.source : link.source.id;
    const targetId =
        typeof link.target === "string" ? link.target : link.target.id;
    if (props.highlightedPath.length > 0) {
        const si = props.highlightedPath.indexOf(sourceId);
        const ti = props.highlightedPath.indexOf(targetId);
        if (si !== -1 && ti !== -1 && Math.abs(si - ti) === 1) {
            return "graph-link on-path";
        }
        return "graph-link off-path";
    }
    const sourceNode =
        typeof link.source === "object"
            ? link.source
            : simNodes.find((n) => n.id === sourceId);
    const targetNode =
        typeof link.target === "object"
            ? link.target
            : simNodes.find((n) => n.id === targetId);
    if (
        (sourceNode && props.hiddenSlugs.has(sourceNode.graph_slug)) ||
        (targetNode && props.hiddenSlugs.has(targetNode.graph_slug))
    ) {
        return "graph-link slug-hidden";
    }
    return "graph-link";
}

function initD3() {
    if (!svgEl.value) return;
    svgSel = d3.select(svgEl.value);
    svgSel.selectAll("*").remove();

    // Arrow marker definition
    const defs = svgSel.append("defs");
    defs.append("marker")
        .attr("id", "arrow")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 22)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "#aaa");

    defs.append("marker")
        .attr("id", "arrow-path")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 22)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "#e15759");

    // Root group for pan/zoom
    zoomGroup = svgSel.append("g").attr("class", "zoom-root");

    const linkGroup = zoomGroup.append("g").attr("class", "links");
    const nodeGroup = zoomGroup.append("g").attr("class", "nodes");
    const labelGroup = zoomGroup.append("g").attr("class", "labels");
    const subtitleGroup = zoomGroup.append("g").attr("class", "subtitles");

    buildSimData();

    // Set up zoom
    const zoom = d3
        .zoom()
        .scaleExtent([0.1, 8])
        .on("zoom", (event: D3ZoomEvent) => {
            zoomGroup!.attr("transform", event.transform.toString());
        });
    svgSel.call(zoom);

    // Background click clears selection
    svgSel.on("click", (event: MouseEvent) => {
        if (event.target === svgEl.value) emit("canvas-click");
    });

    rebindData(linkGroup, nodeGroup, labelGroup, subtitleGroup);

    const { width, height } = svgEl.value.getBoundingClientRect();
    simulation = d3
        .forceSimulation(simNodes)
        .force(
            "link",
            d3
                .forceLink(simLinks)
                .id((d: SimNode) => d.id)
                .distance(120),
        )
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force(
            "collide",
            d3.forceCollide().radius((d: SimNode) => nodeRadius(d) + 8),
        )
        .on("tick", ticked);
}

function firstAttrSubtitle(node: SimNode): string {
    const first = node.attributes[0]?.values[0];
    if (!first) return "";
    return first.length > 24 ? first.slice(0, 22) + "…" : first;
}

function rebindData(
    linkGroup: D3Selection,
    nodeGroup: D3Selection,
    labelGroup: D3Selection,
    subtitleGroup: D3Selection,
) {
    linkSel = linkGroup
        .selectAll("line")
        .data(simLinks, (d: SimLink) => d.id)
        .join("line")
        .attr("class", (d: SimLink) => linkClass(d))
        .attr("marker-end", (d: SimLink) => {
            const sourceId =
                typeof d.source === "string" ? d.source : d.source.id;
            const targetId =
                typeof d.target === "string" ? d.target : d.target.id;
            if (
                props.highlightedPath.includes(sourceId) &&
                props.highlightedPath.includes(targetId)
            ) {
                return "url(#arrow-path)";
            }
            return "url(#arrow)";
        });

    nodeSel = nodeGroup
        .selectAll("g.graph-node")
        .data(simNodes, (d: SimNode) => d.id)
        .join("g")
        .attr("class", (d: SimNode) => nodeClass(d))
        .call(
            d3
                .drag()
                .on("start", (event: D3DragEvent, d: SimNode) => {
                    if (!event.active) simulation?.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                })
                .on("drag", (event: D3DragEvent, d: SimNode) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on("end", (event: D3DragEvent) => {
                    if (!event.active) simulation?.alphaTarget(0);
                    // Leave fx/fy set — node stays pinned until double-clicked
                }),
        );

    nodeSel
        .selectAll("circle")
        .data((d: SimNode) => [d])
        .join("circle")
        .attr("r", (d: SimNode) => nodeRadius(d))
        .attr("fill", (d: SimNode) => graphColor(d))
        .attr("stroke", "#fff")
        .attr("stroke-width", 2);

    nodeSel.on("click", (_event: MouseEvent, d: SimNode) => {
        _event.stopPropagation();
        if (props.pathfindMode) {
            emit("pathfind-node-select", d.id);
        } else {
            emit("node-click", d.id);
        }
    });

    nodeSel.on("dblclick", (_event: MouseEvent, d: SimNode) => {
        _event.stopPropagation();
        // Toggle pin
        if (d.fx !== null) {
            d.fx = null;
            d.fy = null;
        } else {
            d.fx = d.x;
            d.fy = d.y;
        }
        emit("node-dblclick", d.id);
        simulation?.alpha(0.1).restart();
        refreshNodeClasses();
    });

    labelSel = labelGroup
        .selectAll("text")
        .data(simNodes, (d: SimNode) => d.id)
        .join("text")
        .attr("class", (d: SimNode) =>
            ["node-label", typeClass(d), hiddenClass(d)]
                .filter(Boolean)
                .join(" "),
        )
        .attr("text-anchor", "middle")
        .attr("dy", (d: SimNode) => nodeRadius(d) + 13)
        .text((d: SimNode) =>
            d.name.length > 28 ? d.name.slice(0, 26) + "…" : d.name,
        );

    subtitleSel = subtitleGroup
        .selectAll("text")
        .data(simNodes, (d: SimNode) => d.id)
        .join("text")
        .attr("class", (d: SimNode) =>
            ["node-subtitle", typeClass(d), hiddenClass(d)]
                .filter(Boolean)
                .join(" "),
        )
        .attr("text-anchor", "middle")
        .attr("dy", (d: SimNode) => nodeRadius(d) + 25)
        .text((d: SimNode) => firstAttrSubtitle(d));
}

function ticked() {
    linkSel
        ?.attr("x1", (d: SimLink) => (d.source as SimNode).x)
        .attr("y1", (d: SimLink) => (d.source as SimNode).y)
        .attr("x2", (d: SimLink) => (d.target as SimNode).x)
        .attr("y2", (d: SimLink) => (d.target as SimNode).y);

    nodeSel?.attr("transform", (d: SimNode) => `translate(${d.x},${d.y})`);
    labelSel?.attr("transform", (d: SimNode) => `translate(${d.x},${d.y})`);
    subtitleSel?.attr("transform", (d: SimNode) => `translate(${d.x},${d.y})`);
}

function refreshNodeClasses() {
    nodeSel?.attr("class", (d: SimNode) => nodeClass(d));
    labelSel?.attr("class", (d: SimNode) =>
        ["node-label", typeClass(d), hiddenClass(d)].filter(Boolean).join(" "),
    );
    subtitleSel?.attr("class", (d: SimNode) =>
        ["node-subtitle", typeClass(d), hiddenClass(d)]
            .filter(Boolean)
            .join(" "),
    );
    linkSel
        ?.attr("class", (d: SimLink) => linkClass(d))
        .attr("marker-end", (d: SimLink) => {
            const sourceId =
                typeof d.source === "string" ? d.source : d.source.id;
            const targetId =
                typeof d.target === "string" ? d.target : d.target.id;
            if (
                props.highlightedPath.includes(sourceId) &&
                props.highlightedPath.includes(targetId)
            ) {
                return "url(#arrow-path)";
            }
            return "url(#arrow)";
        });
}

function restartSimulation() {
    if (!zoomGroup) return;
    buildSimData();
    const linkGroup = zoomGroup.select("g.links");
    const nodeGroup = zoomGroup.select("g.nodes");
    const labelGroup = zoomGroup.select("g.labels");
    const subtitleGroup = zoomGroup.select("g.subtitles");

    rebindData(linkGroup, nodeGroup, labelGroup, subtitleGroup);

    simulation?.nodes(simNodes);
    simulation?.force("link")?.links(simLinks);
    simulation?.alpha(0.5).restart();
}

// Expose a method to re-center the view
function recenter() {
    if (!svgEl.value || !svgSel) return;
    const { width, height } = svgEl.value.getBoundingClientRect();
    svgSel
        .transition()
        .duration(500)
        .call(
            d3.zoom().transform,
            d3.zoomIdentity
                .translate(width / 2, height / 2)
                .scale(0.8)
                .translate(-width / 2, -height / 2),
        );
}

defineExpose({ recenter });

// Restart sim when the graph data or rel-type filters change
watch(
    () => [props.nodes, props.edges, props.enabledRelTypeIds],
    () => restartSimulation(),
    { deep: true },
);

// Just restyle on highlight/selection/visibility changes (no sim restart needed)
watch(
    () => [
        props.selectedNodeId,
        props.highlightedPath,
        props.pathfindMode,
        props.pathfindSourceId,
        props.highlightedSlugs,
        props.hiddenSlugs,
    ],
    () => refreshNodeClasses(),
    { deep: true },
);

onMounted(() => initD3());

onBeforeUnmount(() => {
    simulation?.stop();
    simulation = null;
});
</script>

<template>
    <svg
        ref="svgEl"
        class="graph-canvas"
        @click="emit('canvas-click')"
    />
</template>

<style scoped>
.graph-canvas {
    width: 100%;
    height: 100%;
    background: #f5f7fa;
    cursor: default;
}
</style>

<style>
/* Global: D3 puts these elements outside Vue's scoped tree */
.graph-link {
    stroke: #ccc;
    stroke-width: 1.5;
    fill: none;
    transition:
        stroke 0.2s,
        opacity 0.2s;
}
.graph-link.on-path {
    stroke: #e15759;
    stroke-width: 2.5;
}
.graph-link.off-path {
    opacity: 0.15;
}

.graph-node circle {
    transition:
        opacity 0.2s,
        stroke-width 0.15s;
    cursor: pointer;
}
.graph-node.selected circle {
    stroke: #222;
    stroke-width: 3;
}
.graph-node.seed circle {
    stroke-dasharray: 4 2;
    stroke: #25476a;
    stroke-width: 2.5;
}
.graph-node.on-path circle {
    stroke: #e15759;
    stroke-width: 3;
}
.graph-node.off-path circle {
    opacity: 0.2;
}
.graph-node.pathfind-source circle {
    stroke: #59a14f;
    stroke-width: 3;
}
.graph-node.pathfind-target {
    cursor: crosshair;
}

.graph-link.slug-hidden {
    opacity: 0.1;
}

.graph-node.type-off circle {
    opacity: 0.12;
}
.graph-node.type-on circle {
    stroke-width: 3;
    stroke: rgba(0, 0, 0, 0.5);
}
.node-label.type-off,
.node-subtitle.type-off {
    opacity: 0.12;
}
.graph-node.slug-hidden circle {
    opacity: 0.12;
}
.node-label.slug-hidden,
.node-subtitle.slug-hidden {
    opacity: 0.12;
}

.node-label {
    font-size: 11px;
    fill: #17212b;
    font-weight: 600;
    stroke: rgba(245, 247, 250, 0.96);
    stroke-width: 3.5px;
    stroke-linejoin: round;
    paint-order: stroke;
    pointer-events: none;
    user-select: none;
}
.node-subtitle {
    font-size: 9.5px;
    fill: #3d4b59;
    stroke: rgba(245, 247, 250, 0.94);
    stroke-width: 3px;
    stroke-linejoin: round;
    paint-order: stroke;
    pointer-events: none;
    user-select: none;
}
</style>
