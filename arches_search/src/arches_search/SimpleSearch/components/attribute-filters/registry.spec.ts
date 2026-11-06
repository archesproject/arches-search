import { describe, expect, it, vi } from "vitest";

import {
    buildAttributeFilterQuery,
    formatAttributeFilterValue,
    parseAttributeFilterValue,
} from "@/arches_search/SimpleSearch/components/attribute-filters/registry.ts";

import type { ReferenceSelectNodeValue } from "@/arches_controlled_lists/datatypes/reference-select/types.ts";
import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";

vi.mock("@/arches_vue_components/application", () => ({
    generateArchesURL: (name: string) => `/${name}`,
}));
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

const REFERENCE_NODE: NodeFilterConfigNode = {
    node_id: "node-id",
    node_alias: "material",
    nodegroup_id: "nodegroup-id",
    label: "Material",
    datatype: "reference",
    config: null,
    sortorder: 0,
    filterable: true,
    sortable: false,
};

describe("attribute filter values", () => {
    it("saves reference selections as list items and restores them", () => {
        const query = buildAttributeFilterQuery(
            REFERENCE_NODE,
            [GLASS, WOOD],
            GRAPH_SLUG,
        );
        if (!query) {
            throw new Error("Expected the selection to build a query.");
        }

        expect(query.clauses[0].operands[0].value).toEqual([GLASS, WOOD]);
        expect(parseAttributeFilterValue(REFERENCE_NODE, query)).toEqual([
            GLASS,
            WOOD,
        ]);
        expect(formatAttributeFilterValue(REFERENCE_NODE, [GLASS, WOOD])).toBe(
            "glass, wood",
        );
    });
});
