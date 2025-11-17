export type LogicOperator = "AND" | "OR";

export type Clause = {
    subject?: Array<[string, string]>;
    operands?: { [key: string]: unknown }[];
    operator?: string | null;
};

export type GroupPayload = {
    graph_slug: string | undefined;
    logic: LogicOperator;
    clauses: Clause[];
    groups: GroupPayload[];
    aggregations: Aggregation[];
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

export function initializeQueryTree(graphSlug?: string | null): GroupPayload {
    return {
        graph_slug: graphSlug ?? undefined,
        logic: "AND",
        clauses: [],
        groups: [],
        aggregations: [],
    };
}

export function addEmptyGroup(targetGroup: GroupPayload): void {
    targetGroup.groups.push({
        graph_slug: targetGroup.graph_slug,
        logic: "AND",
        clauses: [],
        groups: [],
        aggregations: [],
    });
}

export function updateGroupGraphSlug(
    targetGroup: GroupPayload,
    newGraphSlug: string | undefined,
) {
    targetGroup.graph_slug = newGraphSlug;
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
        subject: [],
        operands: [],
        operator: null,
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
