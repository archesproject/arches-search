export interface ResourceType {
    id: string | null; // graph id; null = "all types"
    label: string;
    icon: string;
}

export interface TermSuggestion {
    id: number;
    datatype: string;
    text: string;
    addtional_info?: Record<string, unknown>;
}

export interface ActiveFilter {
    id: string;
    text: string;
    clear: () => void;
    inverted: boolean;
    options?: Record<string, unknown>;
}

export interface SortOption {
    label: string;
    value: string;
}

export interface NodeFilterConfigResponse {
    graph_id: string;
    graph_slug: string;
    slug: string;
    nodes: NodeFilterConfigNode[];
}

export interface NodeFilterConfigNode {
    node_id: string;
    node_alias: string;
    nodegroup_id: string;
    label: string;
    datatype: string;
    config: Record<string, unknown> | null;
    sortorder: number;
}

export type SortDirection = "asc" | "desc";

export type SortSpec = { type: "primary_name"; direction: SortDirection };

export interface AttributeFilterOption {
    id: string;
    label: string;
    count?: number;
}

export interface AttributeFilterSection {
    id: string;
    label: string;
    options: AttributeFilterOption[];
}

export interface SavedSearch {
    savedsearchid: string;
    name: string;
    description: string;
    query_definition: Record<string, unknown>;
    created_at: string;
    creator: {
        id: number;
        username: string;
    };
}
