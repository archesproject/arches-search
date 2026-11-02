import { describe, expect, it, vi } from "vitest";

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

import type { ReferenceSelectNodeValue } from "@/arches_controlled_lists/datatypes/reference-select/types.ts";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";

vi.mock("arches", () => ({
    default: {
        activeLanguage: "en",
        languages: [{ code: "en", isdefault: true }],
    },
}));

const GRAPH_SLUG = "reference_and_sample_collection_item";

function referenceValue(label: string): ReferenceSelectNodeValue {
    return {
        list_id: "materials",
        uri: `http://example.org/${label}`,
        labels: [
            {
                id: `${label}-label`,
                language_id: "en",
                list_item_id: `${label}-item`,
                value: label,
                valuetype_id: "prefLabel",
            },
        ],
    };
}

const GLASS = referenceValue("glass");
const WOOD = referenceValue("wood");

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
    it("saves reference selections as list items and restores them", () => {
        const node = buildNode("reference");
        const query = buildQuery(node, [GLASS, WOOD]);

        expect(query.clauses[0].operands[0].value).toEqual([GLASS, WOOD]);
        expect(parseAttributeFilterValue(node, query)).toEqual([GLASS, WOOD]);
        expect(formatAttributeFilterValue(node, [GLASS, WOOD])).toBe(
            "glass, wood",
        );
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

        expect(restoredValue).toEqual(["paint, oil-based"]);
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
        const query = buildQuery(buildNode("reference"), [GLASS]);

        expect(
            parseAttributeFilterValue(buildNode("string"), query),
        ).toBeNull();
    });
});
