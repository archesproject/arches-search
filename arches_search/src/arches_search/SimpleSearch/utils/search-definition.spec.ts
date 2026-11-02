import { describe, expect, it } from "vitest";

import {
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import { buildTimeFilterClause } from "@/arches_search/SimpleSearch/components/TimeFilter/time-filter-clauses.ts";
import {
    buildAdvancedSearchDefinition,
    buildRequestDateRange,
    buildRequestQueries,
    buildRequestQuery,
    foldQueriesIntoAdvancedQuery,
    parseSearchDefinition,
} from "@/arches_search/SimpleSearch/utils/search-definition.ts";
import { ADVANCED_QUERY_KEY } from "@/arches_search/SimpleSearch/types.ts";

import type {
    GroupPayload,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";
import type { SortSpec } from "@/arches_search/SimpleSearch/types.ts";

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
    buildTimeFilterClause(GRAPH_SLUG, null, "1900-01-01", "1950-12-31"),
]);
const constructionDateTimeFilter = buildTimeFilterGroup([
    buildTimeFilterClause(
        GRAPH_SLUG,
        "construction_date",
        "1900-01-01",
        "1950-12-31",
    ),
]);
const surveyDateTimeFilter = buildTimeFilterGroup([
    buildTimeFilterClause(
        GRAPH_SLUG,
        "survey_date",
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
        const rangeClause = buildTimeFilterClause(
            GRAPH_SLUG,
            null,
            "1900-01-01",
            "1900-01-01",
        );
        const singleDateTimeFilter = buildTimeFilterGroup([
            { ...rangeClause, operands: rangeClause.operands.slice(0, 1) },
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
                null,
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

    it("sends an advanced query of one any-field clause", () => {
        expect(
            buildRequestQueries([], allDateNodesTimeFilter, [GRAPH_SLUG]),
        ).toEqual([allDateNodesTimeFilter]);
    });
});

describe("foldQueriesIntoAdvancedQuery", () => {
    const sampleQuery: GroupPayload = {
        ...constructionDateTimeFilter,
        graph_slug: "sample",
    };

    it("ANDs the queries into the advanced query and says which keys moved", () => {
        const folded = foldQueriesIntoAdvancedQuery(
            constructionDateTimeFilter,
            new Map([
                ["survey", surveyDateTimeFilter],
                ["sample", sampleQuery],
            ]),
        );

        expect(folded).toEqual({
            advancedQuery: {
                graph_slug: GRAPH_SLUG,
                scope: GraphScopeToken.RESOURCE,
                logic: LogicToken.AND,
                clauses: [],
                groups: [constructionDateTimeFilter, surveyDateTimeFilter],
                aggregations: [],
                relationship: null,
            },
            foldedKeys: ["survey"],
        });
    });
});

describe("buildAdvancedSearchDefinition", () => {
    it("saves the advanced query alone and reads back unchanged", () => {
        const sort: SortSpec[] = [{ type: "primary_name", direction: "desc" }];
        const definition = buildAdvancedSearchDefinition(
            GRAPH_SLUG,
            constructionDateTimeFilter,
            sort,
        );

        expect(definition).toEqual({
            terms: [],
            queries: { [ADVANCED_QUERY_KEY]: constructionDateTimeFilter },
            graphSlugs: [GRAPH_SLUG],
            mapFilter: null,
            sort,
            includeRelated: false,
        });
        expect(parseSearchDefinition({ ...definition })).toEqual(definition);
    });
});

describe("parseSearchDefinition", () => {
    it("reads a saved search written before sort, related resources or the advanced query existed", () => {
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
            includeRelated: true,
        });
    });
});
