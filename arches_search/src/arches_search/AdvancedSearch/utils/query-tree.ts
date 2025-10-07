export type LogicOperator = "AND" | "OR";

export type Clause = {
    node_alias: string | null;
    search_table: string | null;
    datatype: string | null;
    operator: string | null;
    params: unknown[];
};

export type GroupPayload = {
    logic: LogicOperator;
    clauses: Clause[];
    groups: GroupPayload[];
};

export type AggregationMetric = {
    alias: string;
    fn: string;
    field: string;
    distinct?: boolean;
};

export type Aggregation = {
    name: string;
    where?: Record<string, unknown>;
    group_by?: string[];
    metrics?: AggregationMetric[];
    order_by?: string[];
    limit?: number;
};

export type QueryPayload = {
    graph_slug: string | null | undefined;
    query: GroupPayload;
    aggregations: Aggregation[];
};

export function initializeQueryTree(graphSlug?: string | null): QueryPayload {
    return {
        graph_slug: graphSlug,
        query: {
            logic: "AND",
            clauses: [],
            groups: [],
        },
        aggregations: [],
    };
}

export function updateGraphSlug(
    existingQueryPayload: QueryPayload,
    nextGraphSlug: string | null,
): QueryPayload {
    return {
        ...existingQueryPayload,
        graph_slug: nextGraphSlug,
    };
}
