import { describe, expect, it, vi } from "vitest";

import {
    isLabelList,
    referenceValuesForLabels,
} from "@/arches_search/AdvancedSearch/utils/reference-labels.ts";

function option(uri: string, label: string, children: object[] = []) {
    return {
        uri,
        list_item_values: [
            {
                id: `${label}-label`,
                language_id: "en",
                list_item_id: `${label}-item`,
                value: label,
                valuetype_id: "prefLabel",
            },
        ],
        children,
    };
}

const STONE = option("http://example.com/stone", "stone");
const MARBLE = option("http://example.com/marble", "marble");
const GLASS = option("http://example.com/glass", "glass", [MARBLE]);

vi.mock(
    "@/arches_controlled_lists/stores/useReferenceSelectOptionsStore.ts",
    () => ({
        useReferenceSelectOptionsStore: () => ({
            fetchWidgetOptions: async () => [STONE, GLASS],
        }),
    }),
);

describe("referenceValuesForLabels", () => {
    it("finds each label in the list, nested items included", async () => {
        expect(
            await referenceValuesForLabels("sample", "material", "materials", [
                "marble",
                "stone",
                "not in the list",
            ]),
        ).toEqual([
            {
                list_id: "materials",
                uri: MARBLE.uri,
                labels: MARBLE.list_item_values,
            },
            {
                list_id: "materials",
                uri: STONE.uri,
                labels: STONE.list_item_values,
            },
        ]);
    });
});

describe("isLabelList", () => {
    it("is true only for a non-empty list of strings", () => {
        expect(isLabelList(["glass"])).toBe(true);
        expect(isLabelList([])).toBe(false);
        expect(isLabelList([{ labels: [] }])).toBe(false);
        expect(isLabelList("glass")).toBe(false);
    });
});
