import { describe, expect, it } from "vitest";

import {
    ClauseSubjectTypeToken,
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import {
    buildAttributeFilterQuery,
    formatAttributeFilterValue,
    parseAttributeFilterValue,
} from "@/arches_search/SimpleSearch/components/attribute-filters/registry.ts";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";

const GRAPH_SLUG = "reference_and_sample_collection_item";

function buildNode(datatype: string): NodeFilterConfigNode {
    return {
        node_id: "node-id",
        node_alias: "material",
        nodegroup_id: "nodegroup-id",
        label: "Material",
        datatype,
        config: null,
        sortorder: 0,
    };
}

function buildQuery(node: NodeFilterConfigNode, value: unknown): GroupPayload {
    const query = buildAttributeFilterQuery(node, value, GRAPH_SLUG);
    if (!query) {
        throw new Error("Expected the filter value to build a query.");
    }
    return query;
}

describe("parseAttributeFilterValue", () => {
    it("restores reference selections keyed by label", () => {
        const node = buildNode("reference");
        const query = buildQuery(node, [
            { id: "http://example.org/glass", label: "glass" },
            { id: "http://example.org/wood", label: "wood" },
        ]);

        expect(parseAttributeFilterValue(node, query)).toEqual([
            { id: "glass", label: "glass" },
            { id: "wood", label: "wood" },
        ]);
    });

    it("restores a reference query saved before parsing existed", () => {
        const node = buildNode("reference");
        const savedQuery: GroupPayload = {
            graph_slug: GRAPH_SLUG,
            scope: GraphScopeToken.RESOURCE,
            logic: LogicToken.AND,
            clauses: [
                {
                    type: "LITERAL",
                    quantifier: "ANY",
                    subject: {
                        type: ClauseSubjectTypeToken.NODE,
                        graph_slug: GRAPH_SLUG,
                        node_alias: "material",
                        search_models: [],
                    },
                    operator: "REFERENCES_ANY",
                    operands: [
                        { type: "LITERAL", value: ["paint, oil-based"] },
                    ],
                },
            ],
            groups: [],
            aggregations: [],
            relationship: null,
        };

        const restoredValue = parseAttributeFilterValue(node, savedQuery);

        expect(restoredValue).toEqual([
            { id: "paint, oil-based", label: "paint, oil-based" },
        ]);
        expect(formatAttributeFilterValue(node, restoredValue)).toBe(
            "paint, oil-based",
        );
    });

    it("restores numeric values and ranges, and rebuilds the same query", () => {
        const node = buildNode("number");
        const query = buildQuery(node, {
            text: "9-10, 12",
            tokens: [
                { kind: "range", min: 9, max: 10 },
                { kind: "value", value: 12 },
            ],
        });

        const restoredValue = parseAttributeFilterValue(node, query);

        expect(restoredValue).toEqual({
            text: "9-10, 12",
            tokens: [
                { kind: "range", min: 9, max: 10 },
                { kind: "value", value: 12 },
            ],
        });
        expect(buildQuery(node, restoredValue)).toEqual(query);
    });

    it("returns null for a datatype with no filter widget", () => {
        const query = buildQuery(buildNode("reference"), [
            { id: "glass", label: "glass" },
        ]);

        expect(
            parseAttributeFilterValue(buildNode("string"), query),
        ).toBeNull();
    });
});
