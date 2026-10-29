import type { ElementDefinition } from "cytoscape";

import type {
    GraphEdge,
    GraphNode,
} from "@/arches_search/RelationshipGraph/types.ts";

const MIN_NODE_SIZE = 26;
const MAX_NODE_SIZE = 40;
const SIZE_PER_RELATED_COUNT_ROOT = 2;

export const SEED_CLASS = "seed";

// Grows with the square root of how connected a resource is, within a narrow
// range: enough to tell a hub from a leaf, not enough to swallow its
// neighbors
export function nodeSize(relatedCount: number): number {
    return Math.min(
        MIN_NODE_SIZE + Math.sqrt(relatedCount) * SIZE_PER_RELATED_COUNT_ROOT,
        MAX_NODE_SIZE,
    );
}

export function toNodeElement(
    node: GraphNode,
    color: string,
): ElementDefinition {
    return {
        group: "nodes",
        data: {
            id: node.id,
            label: node.name,
            color,
            size: nodeSize(node.related_count),
        },
        classes: node.is_seed ? SEED_CLASS : "",
    };
}

export function toEdgeElement(edge: GraphEdge): ElementDefinition {
    return {
        group: "edges",
        data: {
            id: edge.id,
            source: edge.source,
            target: edge.target,
            label: edge.relationship_type_label,
        },
    };
}
