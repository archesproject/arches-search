import type { ElementDefinition } from "cytoscape";

import type {
    GraphEdge,
    GraphNode,
} from "@/arches_search/RelationshipGraph/types.ts";

const MIN_NODE_SIZE = 26;
const MAX_NODE_SIZE = 50;
const SIZE_PER_RELATED_COUNT_ROOT = 3;

export const SEED_CLASS = "seed";
export const ON_PATH_CLASS = "on-path";
export const FADED_CLASS = "faded";

function classesOf(
    isSeed: boolean,
    isOnPath: boolean,
    isFaded: boolean,
): string {
    return [
        isSeed ? SEED_CLASS : "",
        isOnPath ? ON_PATH_CLASS : "",
        isFaded ? FADED_CLASS : "",
    ]
        .filter(Boolean)
        .join(" ");
}

// Grows with the square root of how connected a resource is, within a narrow
// range: enough to tell a hub from a leaf, not enough to swallow its
// neighbors
export function nodeSize(relatedCount: number): number {
    return Math.min(
        MIN_NODE_SIZE + Math.sqrt(relatedCount) * SIZE_PER_RELATED_COUNT_ROOT,
        MAX_NODE_SIZE,
    );
}

// `isPathShown` is whether any path is on show, which fades what is off it
export function toNodeElement(
    node: GraphNode,
    color: string,
    isPathShown: boolean,
): ElementDefinition {
    return {
        group: "nodes",
        data: {
            id: node.id,
            label: node.name,
            color,
            size: nodeSize(node.related_count),
        },
        classes: classesOf(
            node.is_seed,
            node.on_path,
            isPathShown && !node.on_path,
        ),
    };
}

export function toEdgeElement(
    edge: GraphEdge,
    isPathShown: boolean,
): ElementDefinition {
    return {
        group: "edges",
        data: {
            id: edge.id,
            source: edge.source,
            target: edge.target,
            label: edge.relationship_type_label,
        },
        classes: classesOf(false, edge.on_path, isPathShown && !edge.on_path),
    };
}
