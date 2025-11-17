import {
    type GroupPayload,
    type RelationshipPath,
    type LiteralOperand,
    type SubjectPath,
    LogicToken,
    GraphScopeToken,
} from "@/arches_search/AdvancedSearch/types.ts";

type ClausePayload = GroupPayload["clauses"][number];
type RelationshipState = NonNullable<GroupPayload["relationship"]>;

const CLAUSE_TYPE_LITERAL = "LITERAL";
const QUANTIFIER_ANY = "ANY";
const OPERATOR_HAS_ANY_VALUE = "HAS_ANY_VALUE";
const RELATIONSHIP_TRAVERSAL_ANY = "ANY";

function filterLiteralClauses(
    clauses: ReadonlyArray<ClausePayload>,
): ClausePayload[] {
    return clauses.filter(function keepLiteralClauses(clause) {
        return clause.type === CLAUSE_TYPE_LITERAL;
    });
}

function stripRelatedClausesFromGroup(
    groupPayload: GroupPayload,
): GroupPayload {
    return {
        ...groupPayload,
        clauses: filterLiteralClauses(groupPayload.clauses),
    };
}

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

export function setGraphSlug(
    groupPayload: GroupPayload,
    graphSlug: string,
): GroupPayload {
    return { ...groupPayload, graph_slug: graphSlug };
}

export function setGraphSlugAndResetIfChanged(
    groupPayload: GroupPayload,
    graphSlug: string,
): GroupPayload {
    const currentGraphSlug = groupPayload.graph_slug;
    const didGraphChange =
        Boolean(currentGraphSlug) && currentGraphSlug !== graphSlug;

    if (!didGraphChange) {
        return setGraphSlug(groupPayload, graphSlug);
    }

    const updatedWithSlug = setGraphSlug(groupPayload, graphSlug);

    return {
        ...updatedWithSlug,
        clauses: [],
        groups: [],
        relationship: null,
    };
}

export function setScope(
    groupPayload: GroupPayload,
    scopeToken: GroupPayload["scope"],
): GroupPayload {
    return { ...groupPayload, scope: scopeToken };
}

export function toggleLogic(groupPayload: GroupPayload): GroupPayload {
    let nextLogic = LogicToken.AND;
    if (groupPayload.logic === LogicToken.AND) {
        nextLogic = LogicToken.OR;
    } else {
        nextLogic = LogicToken.AND;
    }
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

export function replaceChildGroupAtIndexAndReconcile(
    groupPayload: GroupPayload,
    childIndex: number,
    replacementGroup: GroupPayload,
): GroupPayload {
    const previousChildGroup = groupPayload.groups[childIndex];
    const previousChildGraphSlug = previousChildGroup
        ? previousChildGroup.graph_slug
        : "";
    const nextChildGraphSlug = replacementGroup.graph_slug;

    const didChildGraphChange =
        Boolean(previousChildGraphSlug) &&
        Boolean(nextChildGraphSlug) &&
        previousChildGraphSlug !== nextChildGraphSlug;

    const updatedWithChild = replaceChildGroupAtIndex(
        groupPayload,
        childIndex,
        replacementGroup,
    );

    if (!didChildGraphChange) {
        return updatedWithChild;
    }

    let nextRelationship = updatedWithChild.relationship;
    if (childIndex === 0 && nextRelationship !== null) {
        nextRelationship = null;
    }

    const updatedParent: GroupPayload = {
        ...updatedWithChild,
        relationship: nextRelationship,
        clauses: filterLiteralClauses(updatedWithChild.clauses),
    };

    return updatedParent;
}

export function removeChildGroupAtIndex(
    groupPayload: GroupPayload,
    childIndex: number,
): GroupPayload {
    const nextGroups = groupPayload.groups.slice();
    nextGroups.splice(childIndex, 1);
    return { ...groupPayload, groups: nextGroups };
}

export function removeChildGroupAtIndexAndReconcile(
    groupPayload: GroupPayload,
    childIndex: number,
): GroupPayload {
    const groupWithoutChild = removeChildGroupAtIndex(groupPayload, childIndex);

    const hasAnyGroups = groupWithoutChild.groups.length > 0;
    const hasRelationship = groupWithoutChild.relationship !== null;

    if (!hasAnyGroups && hasRelationship) {
        const clearedRelationshipGroup: GroupPayload = {
            ...groupWithoutChild,
            relationship: null,
        };
        return stripRelatedClausesFromGroup(clearedRelationshipGroup);
    }

    return groupWithoutChild;
}

export function addEmptyLiteralClauseToGroup(
    groupPayload: GroupPayload,
): GroupPayload {
    const emptyClause: ClausePayload = {
        type: CLAUSE_TYPE_LITERAL,
        quantifier: QUANTIFIER_ANY,
        subject: [] as SubjectPath,
        operator: OPERATOR_HAS_ANY_VALUE,
        operands: [] as LiteralOperand[],
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

export function setClauseAtIndex(
    groupPayload: GroupPayload,
    clauseIndex: number,
    replacementClause: ClausePayload,
): GroupPayload {
    const nextClauses = groupPayload.clauses.slice();
    nextClauses.splice(clauseIndex, 1, replacementClause);
    return { ...groupPayload, clauses: nextClauses };
}

export function addRelationshipIfMissing(
    groupPayload: GroupPayload,
): GroupPayload {
    if (groupPayload.relationship !== null) {
        return groupPayload;
    }

    const emptyRelationship: RelationshipState = {
        path: [] as RelationshipPath,
        is_inverse: false,
        traversal_quantifiers: [RELATIONSHIP_TRAVERSAL_ANY],
    };

    return { ...groupPayload, relationship: emptyRelationship };
}

export function clearRelationshipIfPresent(
    groupPayload: GroupPayload,
): GroupPayload {
    if (groupPayload.relationship === null) {
        return groupPayload;
    }
    return { ...groupPayload, relationship: null };
}

export function setRelationshipAndReconcileClauses(
    groupPayload: GroupPayload,
    nextRelationship: GroupPayload["relationship"],
): GroupPayload {
    const previousRelationship = groupPayload.relationship;

    if (nextRelationship === null) {
        const withoutRelationship: GroupPayload = {
            ...groupPayload,
            relationship: null,
        };
        return stripRelatedClausesFromGroup(withoutRelationship);
    }

    let didFlipDirection = false;
    if (previousRelationship !== null) {
        const previousIsInverse = Boolean(previousRelationship.is_inverse);
        const nextIsInverse = Boolean(nextRelationship.is_inverse);
        didFlipDirection = previousIsInverse !== nextIsInverse;
    }

    let updatedGroup: GroupPayload = {
        ...groupPayload,
        relationship: nextRelationship,
    };

    if (didFlipDirection) {
        updatedGroup = stripRelatedClausesFromGroup(updatedGroup);
    }

    return updatedGroup;
}

export function computeIsAnd(groupPayload: GroupPayload): boolean {
    return groupPayload.logic === LogicToken.AND;
}
