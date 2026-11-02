import {
    RESULTS_SORT_CREATED_TIME,
    RESULTS_SORT_NAME,
    RESULTS_SORT_NODE_PREFIX,
    RESULTS_SORT_RELEVANCE,
} from "@/arches_search/SimpleSearch/types.ts";

import type {
    ResultsSortDirection,
    ResultsSortField,
    SortSpec,
} from "@/arches_search/SimpleSearch/types.ts";

const DEFAULT_SORT_DIRECTION: ResultsSortDirection = "asc";

// A node is sorted on within one resource model, so a node sort needs it.
export function sortSpecForField(
    field: ResultsSortField | null,
    direction: ResultsSortDirection,
    graphSlug: string | null,
): SortSpec[] {
    switch (field) {
        case RESULTS_SORT_NAME:
            return [{ type: "primary_name", direction }];
        case RESULTS_SORT_CREATED_TIME:
            return [{ type: "created_time", direction }];
        case RESULTS_SORT_RELEVANCE:
        case null:
            return [];
        default: {
            if (!graphSlug || !field.startsWith(RESULTS_SORT_NODE_PREFIX)) {
                return [];
            }
            return [
                {
                    type: "NODE",
                    graph_slug: graphSlug,
                    node_alias: field.slice(RESULTS_SORT_NODE_PREFIX.length),
                    direction,
                },
            ];
        }
    }
}

// What the sort controls show for a sort; one they cannot show reads as
// relevance, while the sort itself is kept as it is.
export function sortFieldForSpecs(specs: SortSpec[]): ResultsSortField {
    const [firstSpec] = specs;
    if (firstSpec?.type === "primary_name") {
        return RESULTS_SORT_NAME;
    }
    if (firstSpec?.type === "created_time") {
        return RESULTS_SORT_CREATED_TIME;
    }
    if (firstSpec?.type === "NODE") {
        return `${RESULTS_SORT_NODE_PREFIX}${firstSpec.node_alias}`;
    }
    return RESULTS_SORT_RELEVANCE;
}

export function sortDirectionForSpecs(specs: SortSpec[]): ResultsSortDirection {
    return specs[0]?.direction ?? DEFAULT_SORT_DIRECTION;
}
