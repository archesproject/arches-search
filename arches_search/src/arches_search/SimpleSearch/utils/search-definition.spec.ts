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
    buildRequestQuery,
} from "@/arches_search/SimpleSearch/utils/search-definition.ts";

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
