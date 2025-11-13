import {
    type GroupPayload,
    type RelationshipPath,
    type LiteralOperand,
    type SubjectPath,
    LogicToken,
    GraphScopeToken,
} from "@/arches_search/AdvancedSearch/types.ts";

/* Factory: empty group (now lives here) */
export function makeEmptyGroupPayload(): GroupPayload {
    return {
        graph_slug: "",
        scope: GraphScopeToken.RESOURCE,
        logic: LogicToken.AND,
        clauses: [],
        groups: [],
        aggregations: [],
        relationship: null,
    };
}

/* UI updaters */
export function setGraphSlug(
    groupPayload: GroupPayload,
    graphSlug: string,
): GroupPayload {
    return { ...groupPayload, graph_slug: graphSlug };
}

export function setScope(
    groupPayload: GroupPayload,
    scopeToken: GroupPayload["scope"],
): GroupPayload {
    return { ...groupPayload, scope: scopeToken };
}

export function toggleLogic(groupPayload: GroupPayload): GroupPayload {
    const nextLogic =
        groupPayload.logic === LogicToken.AND ? LogicToken.OR : LogicToken.AND;
    return { ...groupPayload, logic: nextLogic };
}

export function addChildGroupLikeParent(
    groupPayload: GroupPayload,
): GroupPayload {
    const childGroup: GroupPayload = {
        graph_slug: groupPayload.graph_slug,
        scope: groupPayload.scope,
        logic: groupPayload.logic,
        clauses: [],
        groups: [],
        aggregations: [],
        relationship: null,
    };
    return { ...groupPayload, groups: [...groupPayload.groups, childGroup] };
}

export function replaceChildGroupAtIndex(
    groupPayload: GroupPayload,
    childIndex: number,
    replacementGroup: GroupPayload,
): GroupPayload {
    const nextGroups = groupPayload.groups.slice();
    nextGroups.splice(childIndex, 1, replacementGroup);
    return { ...groupPayload, groups: nextGroups };
}

export function removeChildGroupAtIndex(
    groupPayload: GroupPayload,
    childIndex: number,
): GroupPayload {
    const nextGroups = groupPayload.groups.slice();
    nextGroups.splice(childIndex, 1);
    return { ...groupPayload, groups: nextGroups };
}

export function addEmptyLiteralClauseToGroup(
    groupPayload: GroupPayload,
): GroupPayload {
    const emptyClause = {
        type: "LITERAL" as const,
        quantifier: "ANY" as const,
        subject: [] as SubjectPath,
        operator: "HAS_ANY_VALUE",
        operands: [] as ReadonlyArray<LiteralOperand>,
    };
    return { ...groupPayload, clauses: [...groupPayload.clauses, emptyClause] };
}

export function removeClauseAtIndex(
    groupPayload: GroupPayload,
    clauseIndex: number,
): GroupPayload {
    const nextClauses = groupPayload.clauses.slice();
    nextClauses.splice(clauseIndex, 1);
    return { ...groupPayload, clauses: nextClauses };
}

export function addRelationshipIfMissing(
    groupPayload: GroupPayload,
): GroupPayload {
    if (groupPayload.relationship !== null) return groupPayload;
    const emptyRelationship = {
        path: [] as RelationshipPath,
        is_inverse: false,
        traversal_quantifiers: ["ANY"] as const,
    };
    return { ...groupPayload, relationship: emptyRelationship };
}

export function clearRelationshipIfPresent(
    groupPayload: GroupPayload,
): GroupPayload {
    if (groupPayload.relationship === null) return groupPayload;
    return { ...groupPayload, relationship: null };
}

export function computeIsAnd(groupPayload: GroupPayload): boolean {
    return groupPayload.logic === LogicToken.AND;
}

export function createStableKeys(
    itemCount: number,
    createId: () => string,
): string[] {
    return Array.from({ length: itemCount }, () => createId());
}

export function reconcileStableKeys(
    existingKeys: string[],
    nextCount: number,
    createId: () => string,
): string[] {
    if (nextCount > existingKeys.length) {
        const additional = Array.from(
            { length: nextCount - existingKeys.length },
            () => createId(),
        );
        return [...existingKeys, ...additional];
    }
    if (nextCount < existingKeys.length) {
        return existingKeys.slice(0, nextCount);
    }
    return existingKeys;
}
