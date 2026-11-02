import type { Core, ElementDefinition, Position } from "cytoscape";

import { SEED_CLASS } from "@/arches_search/RelationshipGraph/utils/graph-elements.ts";

// Roughly the edge length the layout aims for, so a new node starts about
// where the layout would put it
const NEIGHBOR_DISTANCE = 120;
const NEIGHBOR_DISTANCE_VARIATION = 0.5;
const SCATTER_RADIUS = 200;
// A new node tries this many spots and takes the one with the most room
const CANDIDATE_COUNT = 12;

export interface SyncResult {
    addedNodeIds: string[];
}

function isSeed(definition: ElementDefinition): boolean {
    return String(definition.classes ?? "")
        .split(" ")
        .includes(SEED_CLASS);
}

function addNeighbor(
    neighbors: Map<string, string[]>,
    id: string,
    neighbor: string,
): void {
    const known = neighbors.get(id);
    if (known) {
        known.push(neighbor);
    } else {
        neighbors.set(id, [neighbor]);
    }
}

// Cytoscape restyles an element it is written to, whether or not anything
// changed, so only what differs is written
function refreshElement(
    existing: ReturnType<Core["getElementById"]>,
    definition: ElementDefinition,
): void {
    const changedData = Object.fromEntries(
        Object.entries(definition.data).filter(
            ([key, value]) => existing.data(key) !== value,
        ),
    );
    if (Object.keys(changedData).length > 0) existing.data(changedData);

    const wantedClasses = String(definition.classes ?? "")
        .split(" ")
        .filter(Boolean)
        .sort()
        .join(" ");
    if ([...existing.classes()].sort().join(" ") !== wantedClasses) {
        existing.classes(wantedClasses);
    }
}

// Every element built here is given an id
function idOf(definition: ElementDefinition): string {
    return definition.data.id as string;
}

function randomOffset(
    distance: number,
    random: () => number,
): { x: number; y: number } {
    const angle = random() * 2 * Math.PI;
    return { x: Math.cos(angle) * distance, y: Math.sin(angle) * distance };
}

// Of a few random spots around the anchor (or, with none, around the center),
// the one furthest from every node already placed. The nodes already on the
// canvas stay put while the layout settles the new ones, so a new node that
// starts on top of one of them would stay there.
function chooseStartPosition(
    anchor: Position | undefined,
    center: Position,
    placed: Map<string, Position>,
    random: () => number,
): Position {
    let bestPosition = center;
    let bestClearance = -1;
    for (let attempt = 0; attempt < CANDIDATE_COUNT; attempt++) {
        const origin = anchor ?? center;
        const distance = anchor
            ? NEIGHBOR_DISTANCE * (1 - NEIGHBOR_DISTANCE_VARIATION + random())
            : SCATTER_RADIUS * random();
        const offset = randomOffset(distance, random);
        const candidate = { x: origin.x + offset.x, y: origin.y + offset.y };

        let clearance = Infinity;
        for (const other of placed.values()) {
            clearance = Math.min(
                clearance,
                Math.hypot(candidate.x - other.x, candidate.y - other.y),
            );
        }
        if (clearance > bestClearance) {
            bestPosition = candidate;
            bestClearance = clearance;
        }
    }
    return bestPosition;
}

function centerOf(positions: Iterable<Position>): Position {
    let count = 0;
    let sumX = 0;
    let sumY = 0;
    for (const position of positions) {
        count += 1;
        sumX += position.x;
        sumY += position.y;
    }
    return count ? { x: sumX / count, y: sumY / count } : { x: 0, y: 0 };
}

// Brings the elements of a Cytoscape instance in line with the given ones,
// without disturbing the ones that stay: they keep their positions, and a new
// node starts next to a node it connects to, so a layout run afterwards only
// has to settle things rather than untangle them.
export function syncGraphElements(
    cy: Core,
    nodes: ElementDefinition[],
    edges: ElementDefinition[],
    random: () => number = Math.random,
): SyncResult {
    const nodeIds = new Set(nodes.map(idOf));
    // An edge to a node that is not drawn would make Cytoscape throw
    const drawableEdges = edges.filter(
        (edge) =>
            nodeIds.has(edge.data.source as string) &&
            nodeIds.has(edge.data.target as string),
    );
    const wantedIds = new Set([...nodeIds, ...drawableEdges.map(idOf)]);

    const addedNodeIds: string[] = [];

    cy.batch(() => {
        cy.elements()
            .filter((element) => !wantedIds.has(element.id()))
            .remove();

        const positions = new Map<string, Position>();
        cy.nodes().forEach((node) => {
            positions.set(node.id(), node.position());
        });

        const neighbors = new Map<string, string[]>();
        for (const edge of drawableEdges) {
            const source = edge.data.source as string;
            const target = edge.data.target as string;
            addNeighbor(neighbors, source, target);
            addNeighbor(neighbors, target, source);
        }

        const center = centerOf(positions.values());
        // Seeds first, so the resources around them can start beside them
        const newNodes = nodes
            .filter((node) => cy.getElementById(idOf(node)).empty())
            .sort(
                (first, second) =>
                    Number(isSeed(second)) - Number(isSeed(first)),
            );

        const placedNodes: ElementDefinition[] = [];
        for (const node of newNodes) {
            const id = idOf(node);
            const anchorId = (neighbors.get(id) ?? []).find((neighborId) =>
                positions.has(neighborId),
            );
            const position = chooseStartPosition(
                anchorId ? positions.get(anchorId) : undefined,
                center,
                positions,
                random,
            );
            positions.set(id, position);
            placedNodes.push({ ...node, position });
            addedNodeIds.push(id);
        }

        for (const definition of [...nodes, ...drawableEdges]) {
            const existing = cy.getElementById(idOf(definition));
            if (existing.nonempty()) refreshElement(existing, definition);
        }

        cy.add([
            ...placedNodes,
            ...drawableEdges.filter((edge) =>
                cy.getElementById(idOf(edge)).empty(),
            ),
        ]);
    });

    return { addedNodeIds };
}
