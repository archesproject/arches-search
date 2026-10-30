import { describe, expect, it } from "vitest";

import {
    ClauseSubjectTypeToken,
    GraphScopeToken,
    LogicToken,
    QUERY_BUILDER_ITEM_GROUP,
    QUERY_BUILDER_ITEM_LOCKED_CLAUSE,
    QUERY_BUILDER_ITEM_LOCKED_GROUP,
    QUERY_BUILDER_ITEM_RELATED_GROUP,
    QUERY_BUILDER_ITEM_ROW,
} from "@/arches_search/AdvancedSearch/types.ts";
import {
    addGroup,
    addRelatedGroup,
    addRow,
    buildPrunedPayload,
    canGroupQueryBuilderItems,
    createQueryBuilderRoot,
    draftDiffersFromApplied,
    findQueryBuilderItem,
    getClauseDatatype,
    groupQueryBuilderItems,
    isClauseComplete,
    listQueryBuilderRows,
    queryBuilderRootFromPayload,
    queryBuilderRootToPayload,
    removeQueryBuilderItem,
    setGroupLabel,
    setRelatedRelationship,
    setRelatedTarget,
    setRowClause,
    toggleGroupLogic,
    toggleRelatedNot,
    toggleRowNot,
} from "@/arches_search/AdvancedSearch/utils/query-builder.ts";

import type {
    GroupPayload,
    LiteralClause,
    QueryBuilderGroup,
    QueryBuilderItem,
    QueryBuilderLookups,
    QueryBuilderRelatedGroup,
    QueryBuilderRow,
    RelationshipBlock,
} from "@/arches_search/AdvancedSearch/types.ts";

const SAMPLE = "sample";
const PERSON = "person";

const NODE_DATATYPES: Record<string, string> = {
    "sample:material": "reference",
    "sample:production_date": "date",
    "sample:location": "geojson-feature-collection",
    "sample:weight": "number",
    "person:name": "string",
};

const OPERATOR_ARITIES: Record<string, number> = {
    REFERENCES_ANY: 1,
    BETWEEN: 2,
    GEO_INTERSECTS: 1,
    EQUALS: 1,
    LIKE: 1,
    HAS_ANY_VALUE: 0,
};

const LOOKUPS: QueryBuilderLookups = {
    getNodeDatatype: (graphSlug, nodeAlias) =>
        NODE_DATATYPES[`${graphSlug}:${nodeAlias}`],
    getOperatorArity: (_datatype, operator) => OPERATOR_ARITIES[operator],
    getOperandComponent: () => undefined,
};

const DRAWN_AREA = {
    type: "FeatureCollection",
    features: [
        {
            type: "Feature",
            properties: {},
            geometry: { type: "Point", coordinates: [0, 0] },
        },
    ],
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

function searchModelsClause(
    searchModels: string[],
    operator: string,
    values: unknown[],
    graphSlug = SAMPLE,
): LiteralClause {
    return {
        type: "LITERAL",
        quantifier: "ANY",
        subject: {
            type: ClauseSubjectTypeToken.SEARCH_MODELS,
            graph_slug: graphSlug,
            node_alias: "",
            search_models: searchModels,
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

function rowsOf(container: { items: QueryBuilderItem[] }): QueryBuilderRow[] {
    return container.items.filter(
        (item): item is QueryBuilderRow =>
            item.itemType === QUERY_BUILDER_ITEM_ROW,
    );
}

function groupById(
    root: QueryBuilderGroup,
    groupId: string,
): QueryBuilderGroup | QueryBuilderRelatedGroup {
    const item = findQueryBuilderItem(root, groupId);
    if (
        !item ||
        (item.itemType !== QUERY_BUILDER_ITEM_GROUP &&
            item.itemType !== QUERY_BUILDER_ITEM_RELATED_GROUP)
    ) {
        throw new Error(`Expected a group with id ${groupId}.`);
    }
    return item;
}

describe("loading and saving", () => {
    it("round-trips a query the builder made", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);

        expect(queryBuilderRootToPayload(root)).toEqual(BUILDER_SHAPED_PAYLOAD);
    });

    it("reads a related group's ALL/ANY from the rows it holds", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);
        const relatedGroup = root.items.find(
            (item): item is QueryBuilderRelatedGroup =>
                item.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP,
        );

        if (!relatedGroup) {
            throw new Error("Expected a related group.");
        }
        expect(relatedGroup).toMatchObject({
            anchorGraphSlug: SAMPLE,
            targetGraphSlug: PERSON,
            logic: LogicToken.OR,
        });
        expect(rowsOf(relatedGroup)[0].clause).toEqual(NAME_LIKE_FORBES);
    });

    it("loads a text search inside a related group as an editable row", () => {
        const textSearch = searchModelsClause(
            ["TermSearch"],
            "LIKE",
            ["Germany"],
            PERSON,
        );
        const payload = group(
            SAMPLE,
            LogicToken.AND,
            [],
            [
                group(
                    SAMPLE,
                    LogicToken.AND,
                    [],
                    [group(PERSON, LogicToken.AND, [textSearch])],
                    relationship("creator"),
                ),
            ],
        );

        const root = queryBuilderRootFromPayload(payload);
        const relatedGroup = groupById(root, root.items[0].id);

        expect(rowsOf(relatedGroup)[0].clause).toEqual(textSearch);
        expect(queryBuilderRootToPayload(root)).toEqual(payload);
    });

    it("keeps what it cannot edit and writes it back unchanged", () => {
        const resourceFieldClause = {
            type: "LITERAL",
            quantifier: "ANY",
            subject: { type: "RESOURCE_FIELD", field: "principaluser" },
            operator: "IS_CURRENT_USER",
            operands: [],
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
        const payload = group(
            SAMPLE,
            LogicToken.AND,
            [MATERIAL_IS_GLASS, resourceFieldClause],
            [tileScopeGroup, relationshipWithAnchorClause],
        );

        const root = queryBuilderRootFromPayload(payload);

        expect(root.items.map((item) => item.itemType)).toEqual([
            QUERY_BUILDER_ITEM_ROW,
            QUERY_BUILDER_ITEM_LOCKED_CLAUSE,
            QUERY_BUILDER_ITEM_LOCKED_GROUP,
            QUERY_BUILDER_ITEM_LOCKED_GROUP,
        ]);
        expect(queryBuilderRootToPayload(root)).toEqual(payload);
    });

    it("nests a root it cannot edit inside an editable one", () => {
        const tileScopeRoot: GroupPayload = {
            ...group(SAMPLE, LogicToken.OR, [MATERIAL_IS_GLASS]),
            scope: GraphScopeToken.TILE,
        };

        expect(
            queryBuilderRootToPayload(
                queryBuilderRootFromPayload(tileScopeRoot),
            ),
        ).toEqual(group(SAMPLE, LogicToken.AND, [], [tileScopeRoot]));
    });
});

describe("adding", () => {
    it("adds an empty row on the group's model", () => {
        const root = createQueryBuilderRoot(SAMPLE);

        expect(rowsOf(addRow(root, root.id).root)[0].clause).toEqual(
            nodeClause(SAMPLE, "", null, []),
        );
    });

    it("starts a new subgroup with the opposite ALL/ANY", () => {
        const root = createQueryBuilderRoot(SAMPLE);
        const { root: withGroup, groupId } = addGroup(root, root.id);
        const { root: withNestedGroup, groupId: nestedGroupId } = addGroup(
            withGroup,
            groupId,
        );

        expect(groupById(withNestedGroup, groupId).logic).toBe(LogicToken.OR);
        expect(groupById(withNestedGroup, nestedGroupId).logic).toBe(
            LogicToken.AND,
        );
    });

    it("adds rows inside a related group on the related model", () => {
        const root = createQueryBuilderRoot(SAMPLE);
        const { root: withRelated, groupId } = addRelatedGroup(root, root.id);
        const withTarget = setRelatedTarget(withRelated, groupId, PERSON);
        const { root: withRow } = addRow(withTarget, groupId);

        const relatedGroup = groupById(withRow, groupId);
        expect(relatedGroup).toMatchObject({
            itemType: QUERY_BUILDER_ITEM_RELATED_GROUP,
            anchorGraphSlug: SAMPLE,
            targetGraphSlug: PERSON,
            logic: LogicToken.AND,
        });
        expect(rowsOf(relatedGroup)[0].clause.subject.graph_slug).toBe(PERSON);
    });
});

describe("editing", () => {
    it("flips a group's ALL/ANY without touching what it holds", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);
        const flipped = toggleGroupLogic(root, root.id);

        expect(flipped.logic).toBe(LogicToken.OR);
        expect(flipped.items).toEqual(root.items);
    });

    it("toggles NOT on a row between ANY and NONE", () => {
        let root = createQueryBuilderRoot(SAMPLE);
        const { root: withRow, rowId } = addRow(root, root.id);
        root = setRowClause(
            withRow,
            rowId,
            nodeClause(
                SAMPLE,
                "material",
                "REFERENCES_ANY",
                [["glass"]],
                "ALL",
            ),
        );

        const negated = toggleRowNot(root, rowId);
        expect(rowsOf(negated)[0].clause.quantifier).toBe("NONE");
        expect(rowsOf(toggleRowNot(negated, rowId))[0].clause.quantifier).toBe(
            "ANY",
        );
    });

    it("toggles NOT on a related group's traversal", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);
        const relatedGroupId = root.items[2].id;

        expect(
            groupById(toggleRelatedNot(root, relatedGroupId), relatedGroupId),
        ).toMatchObject({
            relationship: { traversal_quantifier: "ANY" },
        });
    });

    it("clears a related group's link and rows when its model changes", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);
        const relatedGroupId = root.items[2].id;
        const retargeted = groupById(
            setRelatedTarget(root, relatedGroupId, "group"),
            relatedGroupId,
        );

        expect(retargeted).toMatchObject({
            targetGraphSlug: "group",
            relationship: { path: { graph_slug: "", node_alias: "" } },
            items: [],
        });
    });

    it("sets a group's label and a related group's link", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);
        const relatedGroupId = root.items[2].id;
        const edited = setRelatedRelationship(
            setGroupLabel(root, root.id, "Renamed"),
            relatedGroupId,
            relationship("donor"),
        );

        expect(edited.label).toBe("Renamed");
        expect(groupById(edited, relatedGroupId)).toMatchObject({
            relationship: relationship("donor"),
        });
    });

    it("removes an item from wherever it is nested", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);
        const weightsGroup = groupById(root, root.items[1].id);
        const removed = removeQueryBuilderItem(root, weightsGroup.items[0].id);

        expect(groupById(removed, weightsGroup.id).items).toEqual([]);
    });
});

describe("grouping selected items", () => {
    function rootWithThreeRows(): QueryBuilderGroup {
        let root = createQueryBuilderRoot(SAMPLE);
        for (const clause of [
            MATERIAL_IS_GLASS,
            WEIGHT_IS_TEN,
            MATERIAL_IS_GLASS,
        ]) {
            const { root: withRow, rowId } = addRow(root, root.id);
            root = setRowClause(withRow, rowId, clause);
        }
        return root;
    }

    it("wraps siblings in a new group where the first of them was", () => {
        const root = rootWithThreeRows();
        const [firstRow, secondRow, thirdRow] = root.items;
        const result = groupQueryBuilderItems(root, [
            thirdRow.id,
            secondRow.id,
        ]);

        if (!result) {
            throw new Error("Expected the rows to be grouped.");
        }
        expect(result.root.items.map((item) => item.id)).toEqual([
            firstRow.id,
            result.groupId,
        ]);
        const newGroup = groupById(result.root, result.groupId);
        expect(newGroup.logic).toBe(LogicToken.OR);
        expect(newGroup.items).toEqual([secondRow, thirdRow]);
    });

    it("refuses items from different groups or fewer than two", () => {
        const root = rootWithThreeRows();
        const { root: withGroup, groupId } = addGroup(root, root.id);
        const { root: withNestedRow, rowId } = addRow(withGroup, groupId);

        expect(
            groupQueryBuilderItems(withNestedRow, [root.items[0].id, rowId]),
        ).toBeNull();
        expect(groupQueryBuilderItems(root, [root.items[0].id])).toBeNull();
    });

    it("says ahead of time whether the items can be grouped", () => {
        const root = rootWithThreeRows();
        const { root: withGroup, groupId } = addGroup(root, root.id);
        const { root: withNestedRow, rowId } = addRow(withGroup, groupId);

        expect(
            canGroupQueryBuilderItems(withNestedRow, [
                root.items[0].id,
                root.items[2].id,
            ]),
        ).toBe(true);
        expect(
            canGroupQueryBuilderItems(withNestedRow, [root.items[0].id, rowId]),
        ).toBe(false);
        expect(canGroupQueryBuilderItems(root, [root.items[0].id])).toBe(false);
    });
});

describe("listQueryBuilderRows", () => {
    it("lists every row in the order it appears, nested ones included", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);

        expect(
            listQueryBuilderRows(root).map((row) => row.clause.subject),
        ).toEqual([
            MATERIAL_IS_GLASS.subject,
            WEIGHT_IS_TEN.subject,
            NAME_LIKE_FORBES.subject,
        ]);
    });
});

describe("getClauseDatatype", () => {
    it("reads a node's datatype, or the datatype of the search models", () => {
        expect(
            getClauseDatatype(
                searchModelsClause(
                    ["DateSearch", "DateRangeSearch"],
                    "BETWEEN",
                    [],
                ),
                LOOKUPS,
            ),
        ).toBe("date");
        expect(
            getClauseDatatype(
                searchModelsClause(["GeometrySearch"], "GEO_WITHIN", []),
                LOOKUPS,
            ),
        ).toBe("geojson-feature-collection");
        expect(
            getClauseDatatype(
                searchModelsClause(["TermSearch"], "LIKE", []),
                LOOKUPS,
            ),
        ).toBe("string");
        expect(
            getClauseDatatype(
                nodeClause(SAMPLE, "production_date", "BETWEEN", []),
                LOOKUPS,
            ),
        ).toBe("date");
        expect(getClauseDatatype(MATERIAL_IS_GLASS, LOOKUPS)).toBe("reference");
        expect(
            getClauseDatatype(nodeClause(SAMPLE, "", null, []), LOOKUPS),
        ).toBeUndefined();
    });
});

describe("isClauseComplete", () => {
    it("needs a field, an operator and as many values as the operator takes", () => {
        expect(isClauseComplete(MATERIAL_IS_GLASS, LOOKUPS)).toBe(true);
        expect(
            isClauseComplete(nodeClause(SAMPLE, "", "EQUALS", [10]), LOOKUPS),
        ).toBe(false);
        expect(
            isClauseComplete(nodeClause(SAMPLE, "weight", null, []), LOOKUPS),
        ).toBe(false);
        expect(
            isClauseComplete(
                nodeClause(SAMPLE, "production_date", "BETWEEN", [
                    "1900-01-01",
                ]),
                LOOKUPS,
            ),
        ).toBe(false);
        expect(
            isClauseComplete(
                nodeClause(SAMPLE, "material", "REFERENCES_ANY", [[]]),
                LOOKUPS,
            ),
        ).toBe(false);
        expect(
            isClauseComplete(
                nodeClause(SAMPLE, "material", "HAS_ANY_VALUE", []),
                LOOKUPS,
            ),
        ).toBe(true);
    });

    it("needs a drawn area for a map row and both dates for a time row", () => {
        expect(
            isClauseComplete(
                searchModelsClause(["GeometrySearch"], "GEO_INTERSECTS", [
                    { type: "FeatureCollection", features: [] },
                ]),
                LOOKUPS,
            ),
        ).toBe(false);
        expect(
            isClauseComplete(
                searchModelsClause(["GeometrySearch"], "GEO_INTERSECTS", [
                    DRAWN_AREA,
                ]),
                LOOKUPS,
            ),
        ).toBe(true);
        expect(
            isClauseComplete(
                searchModelsClause(
                    ["DateSearch", "DateRangeSearch"],
                    "BETWEEN",
                    ["1900-01-01", "1950-12-31"],
                ),
                LOOKUPS,
            ),
        ).toBe(true);
    });
});

describe("buildPrunedPayload", () => {
    it("drops unfinished rows and groups left empty, ANY groups included", () => {
        let root = createQueryBuilderRoot(SAMPLE);
        const { root: withRow, rowId } = addRow(root, root.id);
        root = setRowClause(withRow, rowId, MATERIAL_IS_GLASS);
        root = addRow(root, root.id).root;
        const { root: withGroup, groupId } = addGroup(root, root.id);
        root = addRow(withGroup, groupId).root;

        expect(groupById(root, groupId).logic).toBe(LogicToken.OR);
        expect(buildPrunedPayload(root, LOOKUPS)).toEqual(
            group(SAMPLE, LogicToken.AND, [MATERIAL_IS_GLASS]),
        );
    });

    it("keeps a related group with a link even with no rows of its own", () => {
        const root = createQueryBuilderRoot(SAMPLE);
        const { root: withRelated, groupId } = addRelatedGroup(root, root.id);
        const linked = setRelatedRelationship(
            setRelatedTarget(withRelated, groupId, PERSON),
            groupId,
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

    it("drops a related group whose link is not chosen yet", () => {
        const root = createQueryBuilderRoot(SAMPLE);
        const { root: withRelated, groupId } = addRelatedGroup(root, root.id);

        expect(
            buildPrunedPayload(
                setRelatedTarget(withRelated, groupId, PERSON),
                LOOKUPS,
            ),
        ).toBeNull();
    });

    it("returns no query when nothing is left", () => {
        const root = createQueryBuilderRoot(SAMPLE);

        expect(
            buildPrunedPayload(addRow(root, root.id).root, LOOKUPS),
        ).toBeNull();
    });
});

describe("draftDiffersFromApplied", () => {
    it("ignores rows still being filled in", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);
        const withUnfinishedRow = addRow(root, root.id).root;

        expect(
            draftDiffersFromApplied(
                withUnfinishedRow,
                BUILDER_SHAPED_PAYLOAD,
                LOOKUPS,
            ),
        ).toBe(false);
    });

    it("notices an edit that would change the search", () => {
        const root = queryBuilderRootFromPayload(BUILDER_SHAPED_PAYLOAD);

        expect(
            draftDiffersFromApplied(
                toggleGroupLogic(root, root.id),
                BUILDER_SHAPED_PAYLOAD,
                LOOKUPS,
            ),
        ).toBe(true);
        expect(draftDiffersFromApplied(null, null, LOOKUPS)).toBe(false);
    });
});
