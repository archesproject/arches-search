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

export function updateGraphSlug(
    existingQueryPayload: QueryPayload,
    nextGraphSlug: string | null,
): QueryPayload {
    return {
        ...existingQueryPayload,
        graph_slug: nextGraphSlug,
    };
}

function createEmptyGroup(): GroupPayload {
    return {
        logic: "AND",
        clauses: [],
        groups: [],
    };
}

export function addEmptyGroup(targetGroup: GroupPayload): void {
    const newGroup = createEmptyGroup();
    targetGroup.groups.push(newGroup);
}

export function toggleGroupLogic(targetGroup: GroupPayload): void {
    targetGroup.logic = targetGroup.logic === "AND" ? "OR" : "AND";
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

function createEmptyClause(): Clause {
    return {
        node_alias: null,
        search_table: null,
        datatype: null,
        operator: null,
        params: [],
    };
}

export function addEmptyClause(targetGroup: GroupPayload): void {
    targetGroup.clauses.push(createEmptyClause());
}

export function setClauseNodeAlias(
    targetClause: Clause,
    nextAlias: string | null,
): void {
    targetClause.node_alias = nextAlias;
}

export function setClauseDatatype(
    targetClause: Clause,
    nextDatatype: string | null,
): void {
    targetClause.datatype = nextDatatype;
}

export function setClauseOperator(
    targetClause: Clause,
    nextOperator: string | null,
): void {
    targetClause.operator = nextOperator;
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
