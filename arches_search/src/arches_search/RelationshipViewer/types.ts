import type * as d3 from "d3";

export interface GraphNodeAttribute {
    alias: string;
    values: string[];
}

export interface GraphNode {
    id: string;
    name: string;
    graph_id: string | null;
    graph_slug: string | null;
    graph_name: string | null;
    graph_color: string | null;
    graph_icon: string | null;
    is_seed: boolean;
    related_count: number;
    attributes: GraphNodeAttribute[];
}

export interface GraphEdge {
    id: string;
    source: string;
    target: string;
    relationship_type_id: string;
    relationship_type_label: string;
    tile_id: string | null;
}

export interface RelationshipType {
    id: string;
    label: string;
    count: number;
}

export interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
    relationship_types: RelationshipType[];
}

// D3 simulation extensions — D3 mutates these onto the node/link objects
export interface SimNode extends d3.SimulationNodeDatum, GraphNode {
    x: number;
    y: number;
    fx: number | null;
    fy: number | null;
}

export interface SimLink extends d3.SimulationLinkDatum<SimNode> {
    id: string;
    source: SimNode | string;
    target: SimNode | string;
    relationship_type_id: string;
    relationship_type_label: string;
    tile_id: string | null;
}

export interface GraphTypeGroup {
    slug: string | null;
    name: string | null;
    color: string;
    count: number;
    hidden: boolean;
    highlighted: boolean;
}
