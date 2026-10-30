import { describe, expect, it } from "vitest";

import { describeAdvancedSearchQuery } from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/components/NarrationPanel/query-narrator.ts";
import {
    ClauseSubjectTypeToken,
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";

import type {
    AdvancedSearchFacet,
    GraphModel,
    GroupPayload,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";

const SAMPLE = "sample";

const GRAPHS = [{ slug: SAMPLE, name: "Sample" }] as GraphModel[];

const FACETS = {
    string: [{ operator: "LIKE", label: "is like" }],
    date: [{ operator: "BETWEEN", label: "is between" }],
    "geojson-feature-collection": [
        { operator: "GEO_INTERSECTS", label: "intersects with" },
    ],
} as unknown as Record<string, AdvancedSearchFacet[]>;

const NODE_METADATA = {
    "('sample', 'name')": {
        card_x_node_x_widget_label: "Name",
        datatype: "string",
    },
};

function interpolate(msgid: string, params?: Record<string, unknown>): string {
    return msgid.replace(/%\{(\w+)\}/g, (_match, key: string) =>
        String(params?.[key] ?? ""),
    );
}

function nameLike(
    value: string,
    quantifier: LiteralClause["quantifier"] = "ANY",
): LiteralClause {
    return {
        type: "LITERAL",
        quantifier,
        subject: {
            type: ClauseSubjectTypeToken.NODE,
            graph_slug: SAMPLE,
            node_alias: "name",
            search_models: [],
        },
        operator: "LIKE",
        operands: [{ type: "LITERAL", value }],
    };
}

function anyFieldClause(
    searchModels: string[],
    operator: string,
    values: unknown[],
): LiteralClause {
    return {
        type: "LITERAL",
        quantifier: "ANY",
        subject: {
            type: ClauseSubjectTypeToken.SEARCH_MODELS,
            graph_slug: SAMPLE,
            node_alias: "",
            search_models: searchModels,
        },
        operator,
        operands: values.map((value) => ({ type: "LITERAL", value })),
    };
}

function group(
    logic: LogicToken,
    clauses: LiteralClause[],
    groups: GroupPayload[] = [],
): GroupPayload {
    return {
        graph_slug: SAMPLE,
        scope: GraphScopeToken.RESOURCE,
        logic,
        clauses,
        groups,
        aggregations: [],
        relationship: null,
    };
}

function narrate(payload: GroupPayload): string {
    return describeAdvancedSearchQuery({
        payload,
        graphs: GRAPHS,
        datatypesToAdvancedSearchFacets: FACETS,
        gettext: interpolate,
        nodeMetadata: NODE_METADATA,
    });
}

describe("describeAdvancedSearchQuery", () => {
    it("reads NOT and every-value conditions", () => {
        expect(
            narrate(group(LogicToken.AND, [nameLike("Forbes", "NONE")])),
        ).toBe("Find all Sample instances where NOT (Name is like Forbes).");
        expect(
            narrate(group(LogicToken.AND, [nameLike("Forbes", "ALL")])),
        ).toBe(
            "Find all Sample instances where every Name value is like Forbes.",
        );
    });

    it("puts a nested group in parentheses after its label", () => {
        const either = {
            ...group(LogicToken.OR, [nameLike("Byrd"), nameLike("Smith")]),
            label: "Either",
        };

        expect(
            narrate(group(LogicToken.AND, [nameLike("Forbes")], [either])),
        ).toBe(
            "Find all Sample instances where Name is like Forbes and Either: (Name is like Byrd or Name is like Smith).",
        );
    });

    it("names any date or location and the area drawn on the map", () => {
        const drawnArea = { type: "FeatureCollection", features: [] };

        expect(
            narrate(
                group(LogicToken.AND, [
                    anyFieldClause(
                        ["DateSearch", "DateRangeSearch"],
                        "BETWEEN",
                        ["1900-01-01", "1950-12-31"],
                    ),
                    anyFieldClause(["GeometrySearch"], "GEO_INTERSECTS", [
                        drawnArea,
                    ]),
                ]),
            ),
        ).toBe(
            "Find all Sample instances where any date in Sample is between 1900-01-01 and 1950-12-31 and any location in Sample intersects with the area drawn on the map.",
        );
    });
});
