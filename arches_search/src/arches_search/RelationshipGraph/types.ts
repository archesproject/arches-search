export type RelationshipDirection = "outgoing" | "incoming";

export interface ResourceModel {
    id: string;
    name: string;
    color: string | null;
    icon: string | null;
}

// One row of the summary: every relationship of one type, in one direction,
// between the resource and resources of one model.
export interface RelationshipSummaryRow {
    id: string;
    direction: RelationshipDirection;
    relationship_type_id: string;
    // Worded from the resource's side, so incoming rows carry the inverse label
    relationship_type_label: string;
    related_model: ResourceModel;
    count: number;
}

export interface RelationshipSummary {
    resource_id: string;
    resource_model: ResourceModel | null;
    rows: RelationshipSummaryRow[];
}

// A resource picked in the search results to look at the relationships of
export interface SelectedResource {
    id: string;
    title: string;
}

// The summary rows of one resource that the graph should draw
export interface RowSelection {
    resource_id: string;
    row_ids: string[];
}

export interface GraphNode {
    id: string;
    name: string;
    model: ResourceModel;
    is_seed: boolean;
    related_count: number;
    on_path: boolean;
}

export interface GraphEdge {
    id: string;
    source: string;
    target: string;
    relationship_type_id: string;
    relationship_type_label: string;
    // The relationship as worded from the target's side; empty if not recorded
    inverse_relationship_type_id: string;
    inverse_relationship_type_label: string;
    notes: string;
    on_path: boolean;
}

export interface RelationshipGraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
    // Whether more resources were left out than the node limit allows
    truncated: boolean;
    node_limit: number;
}

// A relationship between the two resources being compared, worded from the
// first one's side
export interface PathRelationship {
    id: string;
    direction: RelationshipDirection;
    relationship_type_id: string;
    relationship_type_label: string;
}

export interface RelationshipPath {
    from_resource_id: string;
    to_resource_id: string;
    direct_relationships: PathRelationship[];
    // Null when no chain of at most max_hops relationships was found
    hops: number | null;
    // The relationships of the shortest chain, in order from the first resource
    relationship_ids: string[];
    max_hops: number;
    // The search gave up on its size rather than on the distance
    limit_reached: boolean;
}
