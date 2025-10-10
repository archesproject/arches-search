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
        graph_slug: graphSlug ?? null,
        query: {
            logic: "AND",
            clauses: [],
            groups: [],
        },
        aggregations: [],
    };
}

export function addEmptyGroup(targetGroup: GroupPayload): void {
    targetGroup.groups.push({
        logic: "AND",
        clauses: [],
        groups: [],
    });
}

export function updateGroupLogic(
    targetGroup: GroupPayload,
    newLogic: LogicOperator,
) {
    targetGroup.logic = newLogic;
}

export function removeGroup(
    parentGroup: GroupPayload,
    groupToRemove: GroupPayload,
): void {
    const indexOfTarget = parentGroup.groups.indexOf(groupToRemove);

    if (indexOfTarget >= 0) {
        parentGroup.groups.splice(indexOfTarget, 1);
    }
}

export function addEmptyClause(targetGroup: GroupPayload): void {
    targetGroup.clauses.push({
        node_alias: null,
        search_table: null,
        datatype: null,
        operator: null,
        params: [],
    });
}

export function updateClause(
    clauseToUpdate: Clause,
    updatedProperties: Partial<Clause>,
): void {
    Object.assign(clauseToUpdate, updatedProperties);
}

export function removeClause(
    parentGroup: GroupPayload,
    clauseToRemove: Clause,
): void {
    const indexOfTarget = parentGroup.clauses.indexOf(clauseToRemove);

    if (indexOfTarget >= 0) {
        parentGroup.clauses.splice(indexOfTarget, 1);
    }
}
