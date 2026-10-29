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
