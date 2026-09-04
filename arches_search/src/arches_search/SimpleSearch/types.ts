import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

export interface ResourceType {
    id: string | null; // graph id; null = "all types"
    // The search API addresses resource models by slug, not id.
    slug: string;
    label: string;
    icon: string;
}

// Serializable snapshot of every piece of state that defines a search.
// Anything that should round-trip through "save / load search" must live
// here — and therefore on `useSearchFilters`.
export interface SearchDefinition {
    terms: SerializedTerm[];
    queries: Record<string, GroupPayload>;
    graphSlugs: string[];
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

export const ACTIVE_FILTER_KIND_TERM = "term";
export const ACTIVE_FILTER_KIND_RESOURCE_TYPE = "resource-type";
export const ACTIVE_FILTER_KIND_TIME = "time";
export const ACTIVE_FILTER_KIND_MAP = "map";
export const ACTIVE_FILTER_KIND_ATTRIBUTE = "attribute";

export type ActiveFilterKind =
    | typeof ACTIVE_FILTER_KIND_TERM
    | typeof TERM_KIND_CONTROLLED_TERM
    | typeof TERM_KIND_RECORD
    | typeof ACTIVE_FILTER_KIND_RESOURCE_TYPE
    | typeof ACTIVE_FILTER_KIND_TIME
    | typeof ACTIVE_FILTER_KIND_MAP
    | typeof ACTIVE_FILTER_KIND_ATTRIBUTE;

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
    | { type: "created_time"; direction: SortDirection }
    | { type: "RESOURCE_FIELD"; field: string; direction: SortDirection }
    | {
          type: "NODE";
          graph_slug: string;
          node_alias: string;
          direction: SortDirection;
      };

export type ResourceFieldKind =
    | "USER"
    | "CHOICE"
    | "BOOLEAN"
    | "DATE"
    | "ID"
    | "TEXT";

export interface ResourceFieldChoice {
    value: string;
    label: string;
}

export interface ResourceFieldMetadata {
    field: string;
    label: string;
    kind: ResourceFieldKind;
    operators: string[];
    is_groupable: boolean;
    is_user_relation: boolean;
    choices?: ResourceFieldChoice[];
}

export interface ResourceFieldFilter {
    field: string;
    operator: string;
    value?: unknown;
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
