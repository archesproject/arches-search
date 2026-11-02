import { describe, expect, it } from "vitest";

import {
    ClauseSubjectTypeToken,
    GraphScopeToken,
    LogicToken,
    QUERY_BUILDER_ITEM_LOCKED_CLAUSE,
    QUERY_BUILDER_ITEM_LOCKED_GROUP,
    QUERY_BUILDER_ITEM_ROW,
} from "@/arches_search/AdvancedSearch/types.ts";
import {
    addGroup,
    addRelatedGroup,
    addRow,
    buildPrunedPayload,
    createQueryBuilderRoot,
    queryBuilderRootFromPayload,
    setRelatedRelationship,
    setRelatedTarget,
} from "@/arches_search/AdvancedSearch/utils/query-builder.ts";

import type {
    GroupPayload,
    LiteralClause,
    QueryBuilderGroup,
    QueryBuilderLookups,
    RelationshipBlock,
} from "@/arches_search/AdvancedSearch/types.ts";

const SAMPLE = "sample";
const PERSON = "person";

const NODE_DATATYPES: Record<string, string> = {
    "sample:material": "reference",
    "sample:weight": "number",
    "person:name": "string",
};

const OPERATOR_ARITIES: Record<string, number> = {
    REFERENCES_ANY: 1,
    EQUALS: 1,
    LIKE: 1,
};

const LOOKUPS: QueryBuilderLookups = {
    getNodeDatatype: (graphSlug, nodeAlias) =>
        NODE_DATATYPES[`${graphSlug}:${nodeAlias}`],
    getOperatorArity: (_datatype, operator) => OPERATOR_ARITIES[operator],
    getOperandComponent: () => undefined,
};

function nodeClause(
    graphSlug: string,
    nodeAlias: string,
    operator: string | null,
    values: unknown[],
    quantifier: LiteralClause["quantifier"] = "ANY",
): LiteralClause {
    return {
        type: "LITERAL",
        quantifier,
        subject: {
            type: ClauseSubjectTypeToken.NODE,
            graph_slug: graphSlug,
            node_alias: nodeAlias,
            search_models: [],
        },
        operator,
        operands: values.map((value) => ({ type: "LITERAL", value })),
    };
}

function group(
    graphSlug: string,
    logic: LogicToken,
    clauses: LiteralClause[] = [],
    groups: GroupPayload[] = [],
    relationship: RelationshipBlock | null = null,
): GroupPayload {
    return {
        graph_slug: graphSlug,
        scope: GraphScopeToken.RESOURCE,
        logic,
        clauses,
        groups,
        aggregations: [],
        relationship,
    };
}

function relationship(
    nodeAlias: string,
    traversalQuantifier: RelationshipBlock["traversal_quantifier"] = "ANY",
): RelationshipBlock {
    return {
        path: {
            type: ClauseSubjectTypeToken.NODE,
            graph_slug: SAMPLE,
            node_alias: nodeAlias,
        },
        is_inverse: false,
        traversal_quantifier: traversalQuantifier,
    };
}

function lastItemId(container: QueryBuilderGroup): string {
    const lastItem = container.items.at(-1);
    if (!lastItem) {
        throw new Error("Expected the group to hold an item.");
    }
    return lastItem.id;
}

const MATERIAL_IS_GLASS = nodeClause(SAMPLE, "material", "REFERENCES_ANY", [
    ["glass"],
]);
const WEIGHT_IS_TEN = nodeClause(SAMPLE, "weight", "EQUALS", [10]);
const NAME_LIKE_FORBES = nodeClause(PERSON, "name", "LIKE", ["Forbes"]);

const BUILDER_SHAPED_PAYLOAD: GroupPayload = {
    ...group(
        SAMPLE,
        LogicToken.AND,
        [MATERIAL_IS_GLASS],
        [
            {
                ...group(
                    SAMPLE,
                    LogicToken.OR,
                    [nodeClause(SAMPLE, "weight", "EQUALS", [10], "NONE")],
                    [],
                ),
                label: "Weights",
            },
            group(
                SAMPLE,
                LogicToken.AND,
                [],
                [group(PERSON, LogicToken.OR, [NAME_LIKE_FORBES])],
                relationship("creator", "NONE"),
            ),
        ],
    ),
    label: "Root label",
};

describe("loading and saving", () => {
    it("round-trips a query the builder made", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);

        expect(buildPrunedPayload(root, LOOKUPS)).toEqual(
            BUILDER_SHAPED_PAYLOAD,
        );
    });

    it("keeps what it cannot edit and writes it back unchanged", () => {
        const resourceFieldClause = {
            type: "LITERAL",
            quantifier: "ANY",
            subject: { type: "RESOURCE_FIELD", field: "principaluser" },
            operator: "IS_CURRENT_USER",
            operands: [],
        } as unknown as LiteralClause;
        const pathOperandClause = {
            ...WEIGHT_IS_TEN,
            operands: [
                {
                    type: "PATH",
                    value: [{ graph_slug: SAMPLE, node_alias: "weight" }],
                },
            ],
        } as unknown as LiteralClause;
        const tileScopeGroup: GroupPayload = {
            ...group(SAMPLE, LogicToken.AND, [MATERIAL_IS_GLASS]),
            scope: GraphScopeToken.TILE,
        };
        const relationshipWithAnchorClause = group(
            SAMPLE,
            LogicToken.AND,
            [WEIGHT_IS_TEN],
            [group(PERSON, LogicToken.AND, [NAME_LIKE_FORBES])],
            relationship("creator"),
        );
        const relationshipWithLabelledTarget = group(
            SAMPLE,
            LogicToken.AND,
            [],
            [
                {
                    ...group(PERSON, LogicToken.AND, [NAME_LIKE_FORBES]),
                    label: "Makers",
                },
            ],
            relationship("creator"),
        );
        const payload = group(
            SAMPLE,
            LogicToken.AND,
            [MATERIAL_IS_GLASS, resourceFieldClause, pathOperandClause],
            [
                tileScopeGroup,
                relationshipWithAnchorClause,
                relationshipWithLabelledTarget,
            ],
        );

        const root = queryBuilderRootFromPayload(payload);

        expect(root.items.map((item) => item.itemType)).toEqual([
            QUERY_BUILDER_ITEM_ROW,
            QUERY_BUILDER_ITEM_LOCKED_CLAUSE,
            QUERY_BUILDER_ITEM_LOCKED_CLAUSE,
            QUERY_BUILDER_ITEM_LOCKED_GROUP,
            QUERY_BUILDER_ITEM_LOCKED_GROUP,
            QUERY_BUILDER_ITEM_LOCKED_GROUP,
        ]);
        expect(buildPrunedPayload(root, LOOKUPS)).toEqual(payload);
    });

    it("nests a root it cannot edit inside an editable one", () => {
        const tileScopeRoot: GroupPayload = {
            ...group(SAMPLE, LogicToken.OR, [MATERIAL_IS_GLASS]),
            scope: GraphScopeToken.TILE,
        };

        expect(
            buildPrunedPayload(
                queryBuilderRootFromPayload(tileScopeRoot),
                LOOKUPS,
            ),
        ).toEqual(group(SAMPLE, LogicToken.AND, [], [tileScopeRoot]));
    });
});

describe("buildPrunedPayload", () => {
    it("drops unfinished rows and groups left empty", () => {
        let root = queryBuilderRootFromPayload(
            group(SAMPLE, LogicToken.AND, [MATERIAL_IS_GLASS]),
        );
        root = addRow(root, root.id);
        root = addGroup(root, root.id);
        root = addRow(root, lastItemId(root));

        expect(buildPrunedPayload(root, LOOKUPS)).toEqual(
            group(SAMPLE, LogicToken.AND, [MATERIAL_IS_GLASS]),
        );
    });

    it("keeps a related group with a link even with no rows of its own", () => {
        const emptyRoot = createQueryBuilderRoot(SAMPLE);
        const withRelated = addRelatedGroup(emptyRoot, emptyRoot.id);
        const relatedGroupId = lastItemId(withRelated);
        const linked = setRelatedRelationship(
            setRelatedTarget(withRelated, relatedGroupId, PERSON),
            relatedGroupId,
            relationship("creator"),
        );

        expect(buildPrunedPayload(linked, LOOKUPS)).toEqual(
            group(
                SAMPLE,
                LogicToken.AND,
                [],
                [
                    group(
                        SAMPLE,
                        LogicToken.AND,
                        [],
                        [group(PERSON, LogicToken.AND)],
                        relationship("creator"),
                    ),
                ],
            ),
        );
    });
});
