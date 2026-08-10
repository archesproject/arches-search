import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

export interface ResourceType {
    id: string | null; // graph id; null = "all types"
    label: string;
    icon: string;
}

// Serializable snapshot of every piece of state that defines a search.
// Anything that should round-trip through "save / load search" must live
// here — and therefore on `useSearchFilters`. Bump `version` when the
// shape changes so old saved rows can be migrated.
export interface SearchDefinition {
    version: 1;
    terms: SerializedTerm[];
    queries: Record<string, GroupPayload>;
    graphId: string | null;
}

export const TERM_KIND_CONTROLLED_TERM = "controlled-term";
export const TERM_KIND_RECORD = "record";

export type TermKind =
    | typeof TERM_KIND_CONTROLLED_TERM
    | typeof TERM_KIND_RECORD;

export interface SerializedTerm {
    id: string;
    text: string;
    inverted: boolean;
    termKind?: TermKind;
    icon?: string;
    options?: Record<string, unknown>;
}

export interface TermSuggestion {
    id: number;
    datatype: string;
    text: string;
    addtional_info?: Record<string, unknown>;
    resourceinstanceid?: string;
    graph_icon?: string;
    graph_name?: string;
}

export type ActiveFilterKind =
    | "term"
    | typeof TERM_KIND_CONTROLLED_TERM
    | typeof TERM_KIND_RECORD
    | "resource-type"
    | "time"
    | "map"
    | "attribute";

export interface ActiveFilter {
    id: string;
    text: string;
    clear: () => void;
    inverted: boolean;
    kind: ActiveFilterKind;
    category: string;
    icon: string;
    onEdit?: () => void;
    options?: Record<string, unknown>;
}

export const RESULTS_SORT_RELEVANCE = "relevance";
export const RESULTS_SORT_A_TO_Z = "aToZ";
export const RESULTS_SORT_Z_TO_A = "zToA";
export const RESULTS_SORT_NEWEST = "newest";
export const RESULTS_SORT_OLDEST = "oldest";

export type ResultsSortValue =
    | typeof RESULTS_SORT_RELEVANCE
    | typeof RESULTS_SORT_A_TO_Z
    | typeof RESULTS_SORT_Z_TO_A
    | typeof RESULTS_SORT_NEWEST
    | typeof RESULTS_SORT_OLDEST;

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

export type SortSpec =
    | { type: "primary_name"; direction: SortDirection }
    | { type: "created_time"; direction: SortDirection };

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
