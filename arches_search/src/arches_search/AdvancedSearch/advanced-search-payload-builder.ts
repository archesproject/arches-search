import { computed, reactive } from "vue";

/* ---------- Tokens (used for control flow; never raw strings) ---------- */
export enum GraphScopeToken {
    RESOURCE = "RESOURCE",
    TILE = "TILE",
}
export enum LogicToken {
    AND = "AND",
    OR = "OR",
}
export enum ClauseTypeToken {
    LITERAL = "LITERAL",
    RELATED = "RELATED",
}
export enum QuantifierToken {
    ANY = "ANY",
    ALL = "ALL",
    NONE = "NONE",
}
export enum OperandTypeToken {
    LITERAL = "LITERAL",
    PATH = "PATH",
}

/* ---------- Payload shapes (mirror your backend exactly) ---------- */
export type OperatorString = string;

export type SubjectPair = readonly [graphSlug: string, nodeAlias: string];
export type SubjectPath = ReadonlyArray<SubjectPair>;
export type RelationshipPath = ReadonlyArray<SubjectPair>;

export type LiteralOperand = {
    readonly type: OperandTypeToken.LITERAL;
    readonly value: string | number | boolean | null;
};

export type PathOperand = {
    readonly type: OperandTypeToken.PATH;
    readonly value: SubjectPath;
};

export type Operand = LiteralOperand | PathOperand;

export type LiteralClause = {
    readonly type: ClauseTypeToken.LITERAL;
    readonly quantifier: QuantifierToken;
    readonly subject: SubjectPath;
    readonly operator: OperatorString;
    readonly operands: ReadonlyArray<Operand>;
};

export type RelatedClause = {
    readonly type: ClauseTypeToken.RELATED;
    readonly quantifier: QuantifierToken;
    readonly subject: SubjectPath;
    readonly operator: OperatorString;
    readonly operands: ReadonlyArray<Operand>;
};

export type Clause = LiteralClause | RelatedClause;

export type RelationshipBlock = {
    readonly path: RelationshipPath;
    readonly is_inverse: boolean;
    readonly traversal_quantifiers: ReadonlyArray<QuantifierToken>;
};

export type GroupPayload = {
    readonly graph_slug: string;
    readonly scope: GraphScopeToken;
    readonly logic: LogicToken;
    readonly clauses: ReadonlyArray<Clause>;
    readonly groups: ReadonlyArray<GroupPayload>;
    readonly aggregations: ReadonlyArray<unknown>;
    readonly relationship: RelationshipBlock | null;
};

export type Payload = GroupPayload;

/* ---------- Small builders for clarity ---------- */
export function makeSubjectPath(...subjectPairs: SubjectPair[]): SubjectPath {
    return subjectPairs.map((subjectPair) => [...subjectPair] as SubjectPair);
}
export function makeRelationshipPath(
    ...relationshipPairs: SubjectPair[]
): RelationshipPath {
    return relationshipPairs.map(
        (relationshipPair) => [...relationshipPair] as SubjectPair,
    );
}
export function makeLiteralOperand(
    value: string | number | boolean | null,
): LiteralOperand {
    return { type: OperandTypeToken.LITERAL, value };
}
export function makePathOperand(path: SubjectPath): PathOperand {
    return { type: OperandTypeToken.PATH, value: path };
}
export function makeLiteralClause(args: {
    quantifier: QuantifierToken;
    subjectPath: SubjectPath;
    operator: OperatorString;
    operands: Operand[];
}): LiteralClause {
    return {
        type: ClauseTypeToken.LITERAL,
        quantifier: args.quantifier,
        subject: [...args.subjectPath],
        operator: args.operator,
        operands: [...args.operands],
    };
}
export function makeRelatedClause(args: {
    quantifier: QuantifierToken;
    subjectPath: SubjectPath;
    operator: OperatorString;
    operands: Operand[];
}): RelatedClause {
    return {
        type: ClauseTypeToken.RELATED,
        quantifier: args.quantifier,
        subject: [...args.subjectPath],
        operator: args.operator,
        operands: [...args.operands],
    };
}
export function makeRelationshipBlock(args: {
    relationshipPath: RelationshipPath;
    isInverse: boolean;
    traversalQuantifiers: QuantifierToken[];
}): RelationshipBlock {
    return {
        path: args.relationshipPath.map((pair) => [...pair] as SubjectPair),
        is_inverse: args.isInverse,
        traversal_quantifiers: [...args.traversalQuantifiers],
    };
}

/* ---------- Convenience empty builders (no business defaults) ---------- */
export function makeEmptyRelationshipBlock(): RelationshipBlock {
    return {
        path: [],
        is_inverse: false,
        traversal_quantifiers: [QuantifierToken.ANY],
    };
}

export function makeEmptyLiteralClause(): LiteralClause {
    return makeLiteralClause({
        quantifier: QuantifierToken.ANY,
        subjectPath: [],
        operator: "HAS_ANY_VALUE",
        operands: [],
    });
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

/* ---------- Internal mutable type used for reactivity (no ids) ---------- */
type MutableGroup = {
    graph_slug: string;
    scope: GraphScopeToken;
    logic: LogicToken;
    clauses: Clause[];
    groups: MutableGroup[];
    aggregations: unknown[];
    relationship: RelationshipBlock | null;
};

/* ---------- Factory for a reactive group ---------- */
function createReactiveGroup(args: {
    graphSlug: string;
    scope: GraphScopeToken;
    logic: LogicToken;
    clauses?: Clause[];
    groups?: MutableGroup[];
    relationship?: RelationshipBlock | null;
    aggregations?: unknown[];
}): MutableGroup {
    return reactive<MutableGroup>({
        graph_slug: args.graphSlug,
        scope: args.scope,
        logic: args.logic,
        clauses: args.clauses ? [...args.clauses] : [],
        groups: args.groups ? [...args.groups] : [],
        aggregations: args.aggregations ? [...args.aggregations] : [],
        relationship: args.relationship ?? null,
    });
}

/* ---------- Pure converter from reactive tree -> plain payload ---------- */
function buildPayloadFromMutableGroup(groupNode: MutableGroup): Payload {
    return {
        graph_slug: groupNode.graph_slug,
        scope: groupNode.scope,
        logic: groupNode.logic,
        clauses: groupNode.clauses.map((clause) => ({ ...clause })),
        groups: groupNode.groups.map((childNode) =>
            buildPayloadFromMutableGroup(childNode),
        ),
        aggregations: [...groupNode.aggregations],
        relationship: groupNode.relationship
            ? {
                  path: groupNode.relationship.path.map(
                      (pair) => [...pair] as SubjectPair,
                  ),
                  is_inverse: groupNode.relationship.is_inverse,
                  traversal_quantifiers: [
                      ...groupNode.relationship.traversal_quantifiers,
                  ],
              }
            : null,
    };
}

/* ---------- Composable API ---------- */
export function useAdvancedSearchPayload(initialGraphSlug: string) {
    const rootGroup = createReactiveGroup({
        graphSlug: initialGraphSlug,
        scope: GraphScopeToken.RESOURCE,
        logic: LogicToken.AND,
    });

    const payload = computed<Payload>(() =>
        buildPayloadFromMutableGroup(rootGroup),
    );

    function setRootGraphSlug(graphSlug: string): void {
        rootGroup.graph_slug = graphSlug;
    }
    function setRootScope(scopeToken: GraphScopeToken): void {
        rootGroup.scope = scopeToken;
    }
    function setRootLogic(logicToken: LogicToken): void {
        rootGroup.logic = logicToken;
    }

    function addChildGroup(
        parentGroup: MutableGroup,
        childGroup: MutableGroup,
    ): void {
        parentGroup.groups = [...parentGroup.groups, childGroup];
    }
    function replaceChildGroup(
        parentGroup: MutableGroup,
        childIndex: number,
        replacementGroup: MutableGroup,
    ): void {
        const updatedGroups = parentGroup.groups.slice();
        updatedGroups.splice(childIndex, 1, replacementGroup);
        parentGroup.groups = updatedGroups;
    }
    function removeChildGroup(
        parentGroup: MutableGroup,
        childIndex: number,
    ): void {
        const updatedGroups = parentGroup.groups.slice();
        updatedGroups.splice(childIndex, 1);
        parentGroup.groups = updatedGroups;
    }

    function addClauseToGroup(targetGroup: MutableGroup, clause: Clause): void {
        targetGroup.clauses = [...targetGroup.clauses, clause];
    }
    function replaceClauseInGroup(
        targetGroup: MutableGroup,
        clauseIndex: number,
        replacementClause: Clause,
    ): void {
        const updatedClauses = targetGroup.clauses.slice();
        updatedClauses.splice(clauseIndex, 1, replacementClause);
        targetGroup.clauses = updatedClauses;
    }
    function removeClauseFromGroup(
        targetGroup: MutableGroup,
        clauseIndex: number,
    ): void {
        const updatedClauses = targetGroup.clauses.slice();
        updatedClauses.splice(clauseIndex, 1);
        targetGroup.clauses = updatedClauses;
    }

    function setGroupRelationship(
        targetGroup: MutableGroup,
        relationshipBlock: RelationshipBlock | null,
    ): void {
        targetGroup.relationship = relationshipBlock
            ? { ...relationshipBlock }
            : null;
    }

    function addAggregationToGroup(
        targetGroup: MutableGroup,
        aggregationDefinition: unknown,
    ): void {
        targetGroup.aggregations = [
            ...targetGroup.aggregations,
            aggregationDefinition,
        ];
    }

    function resetRootGroup(graphSlug: string): void {
        const fresh = createReactiveGroup({
            graphSlug,
            scope: GraphScopeToken.RESOURCE,
            logic: LogicToken.AND,
        });
        rootGroup.graph_slug = fresh.graph_slug;
        rootGroup.scope = fresh.scope;
        rootGroup.logic = fresh.logic;
        rootGroup.clauses = [];
        rootGroup.groups = [];
        rootGroup.aggregations = [];
        rootGroup.relationship = null;
    }

    function createChildGroup(args: {
        graphSlug: string;
        scope: GraphScopeToken;
        logic: LogicToken;
        clauses?: Clause[];
        relationship?: RelationshipBlock | null;
    }): MutableGroup {
        return createReactiveGroup({
            graphSlug: args.graphSlug,
            scope: args.scope,
            logic: args.logic,
            clauses: args.clauses ?? [],
            relationship: args.relationship ?? null,
        });
    }

    return {
        rootGroup,
        payload,
        setRootGraphSlug,
        setRootScope,
        setRootLogic,
        createChildGroup,
        addChildGroup,
        replaceChildGroup,
        removeChildGroup,
        addClauseToGroup,
        replaceClauseInGroup,
        removeClauseFromGroup,
        setGroupRelationship,
        addAggregationToGroup,
        resetRootGroup,
    };
}
