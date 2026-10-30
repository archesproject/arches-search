import { describe, expect, it } from "vitest";

import {
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import {
    buildDateSearchClause,
    buildNodeDateSearchClause,
} from "@/arches_search/AdvancedSearch/utils/advanced-search-payload-builder.ts";
import {
    buildRequestDateRange,
    buildRequestQueries,
    buildRequestQuery,
    parseSearchDefinition,
} from "@/arches_search/SimpleSearch/utils/search-definition.ts";
import { ADVANCED_QUERY_KEY } from "@/arches_search/SimpleSearch/types.ts";

import type {
    GroupPayload,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";

const GRAPH_SLUG = "heritage_resource";

function buildTimeFilterGroup(clauses: LiteralClause[]): GroupPayload {
    return {
        graph_slug: GRAPH_SLUG,
        scope: GraphScopeToken.RESOURCE,
        logic: LogicToken.OR,
        clauses,
        groups: [],
        aggregations: [],
        relationship: null,
    };
}

const allDateNodesTimeFilter = buildTimeFilterGroup([
    buildDateSearchClause(GRAPH_SLUG, "BETWEEN", "1900-01-01", "1950-12-31"),
]);
const constructionDateTimeFilter = buildTimeFilterGroup([
    buildNodeDateSearchClause(
        GRAPH_SLUG,
        "construction_date",
        "BETWEEN",
        "1900-01-01",
        "1950-12-31",
    ),
]);
const surveyDateTimeFilter = buildTimeFilterGroup([
    buildNodeDateSearchClause(
        GRAPH_SLUG,
        "survey_date",
        "BETWEEN",
        "2000-01-01",
        "2010-12-31",
    ),
]);

describe("buildRequestQuery", () => {
    it("returns undefined when there are no queries", () => {
        expect(buildRequestQuery([])).toBeUndefined();
    });

    it("leaves the all-date-nodes time filter out of the query", () => {
        expect(buildRequestQuery([allDateNodesTimeFilter])).toBeUndefined();
    });

    it("keeps a node-specific time filter in the query", () => {
        expect(buildRequestQuery([constructionDateTimeFilter])).toBe(
            constructionDateTimeFilter,
        );
    });

    it("AND-combines the remaining queries", () => {
        expect(
            buildRequestQuery([
                constructionDateTimeFilter,
                allDateNodesTimeFilter,
                surveyDateTimeFilter,
            ]),
        ).toEqual({
            graph_slug: GRAPH_SLUG,
            scope: GraphScopeToken.RESOURCE,
            logic: LogicToken.AND,
            clauses: [],
            groups: [constructionDateTimeFilter, surveyDateTimeFilter],
            aggregations: [],
            relationship: null,
        });
    });
});

describe("buildRequestDateRange", () => {
    it("returns null without an all-date-nodes time filter", () => {
        expect(buildRequestDateRange([constructionDateTimeFilter])).toBeNull();
    });

    it("extracts the range from the all-date-nodes time filter", () => {
        expect(
            buildRequestDateRange([
                constructionDateTimeFilter,
                allDateNodesTimeFilter,
            ]),
        ).toEqual({ from: "1900-01-01", to: "1950-12-31" });
    });

    it("treats a single-date filter as a one-day range", () => {
        const singleDateTimeFilter = buildTimeFilterGroup([
            buildDateSearchClause(GRAPH_SLUG, "BETWEEN", "1900-01-01"),
        ]);

        expect(buildRequestDateRange([singleDateTimeFilter])).toEqual({
            from: "1900-01-01",
            to: "1900-01-01",
        });
    });
});

describe("buildRequestQueries", () => {
    const otherGraphQuery: GroupPayload = {
        ...constructionDateTimeFilter,
        graph_slug: "person",
    };

    it("sends one AND-combined query per graph", () => {
        expect(
            buildRequestQueries(
                [
                    constructionDateTimeFilter,
                    surveyDateTimeFilter,
                    otherGraphQuery,
                ],
                [GRAPH_SLUG, "person"],
            ),
        ).toEqual([
            {
                graph_slug: GRAPH_SLUG,
                scope: GraphScopeToken.RESOURCE,
                logic: LogicToken.AND,
                clauses: [],
                groups: [constructionDateTimeFilter, surveyDateTimeFilter],
                aggregations: [],
                relationship: null,
            },
            otherGraphQuery,
        ]);
    });

    it("leaves out queries for graphs that are not being searched", () => {
        expect(
            buildRequestQueries(
                [constructionDateTimeFilter, otherGraphQuery],
                [GRAPH_SLUG],
            ),
        ).toEqual([constructionDateTimeFilter]);
    });

    it("leaves out the all-date-nodes time filter", () => {
        expect(
            buildRequestQueries([allDateNodesTimeFilter], [GRAPH_SLUG]),
        ).toEqual([]);
    });
});

describe("parseSearchDefinition", () => {
    it("reads a saved search written before sort or the advanced query existed", () => {
        const materialQuery = {
            logic: "AND",
            scope: "RESOURCE",
            groups: [],
            clauses: [
                {
                    type: "LITERAL",
                    subject: {
                        type: "NODE",
                        graph_slug: GRAPH_SLUG,
                        node_alias: "material",
                        search_models: [],
                    },
                    operands: [{ type: "LITERAL", value: ["glass"] }],
                    operator: "REFERENCES_ANY",
                    quantifier: "ANY",
                },
            ],
            graph_slug: GRAPH_SLUG,
            aggregations: [],
            relationship: null,
        };

        expect(
            parseSearchDefinition({
                terms: [],
                queries: { material: materialQuery },
                mapFilter: null,
                graphSlugs: [GRAPH_SLUG],
            }),
        ).toEqual({
            terms: [],
            queries: { material: materialQuery },
            graphSlugs: [GRAPH_SLUG],
            mapFilter: null,
            sort: [],
        });
    });

    it("keeps the advanced query beside the other queries", () => {
        const definition = parseSearchDefinition({
            terms: [],
            queries: {
                [ADVANCED_QUERY_KEY]: constructionDateTimeFilter,
                timeFilter: allDateNodesTimeFilter,
            },
            graphSlugs: [GRAPH_SLUG],
            mapFilter: null,
        });

        expect(definition.queries[ADVANCED_QUERY_KEY]).toEqual(
            constructionDateTimeFilter,
        );
        expect(definition.queries.timeFilter).toEqual(allDateNodesTimeFilter);
    });

    it("reads the saved sort and drops malformed entries", () => {
        expect(
            parseSearchDefinition({
                terms: [],
                queries: {},
                graphSlugs: [],
                mapFilter: null,
                sort: [
                    { type: "primary_name", direction: "desc" },
                    { direction: "asc" },
                    "created_time",
                ],
            }).sort,
        ).toEqual([{ type: "primary_name", direction: "desc" }]);
    });
});
