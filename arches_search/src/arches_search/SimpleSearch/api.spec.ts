import { describe, expect, it } from "vitest";

import { buildSearchApiRequestBody } from "@/arches_search/SimpleSearch/api.ts";
import { TERM_KIND_CONTROLLED_TERM } from "@/arches_search/SimpleSearch/types.ts";

describe("buildSearchApiRequestBody", () => {
    it("sends controlled terms as their own reference-datatype TEXT_MATCH", () => {
        const body = buildSearchApiRequestBody({
            terms: [
                { type: "string", text: "mission", inverted: false },
                {
                    type: TERM_KIND_CONTROLLED_TERM,
                    text: "adobe",
                    inverted: false,
                },
            ],
            graphIds: [],
            mapFilter: null,
        });

        expect(body.node_agnostic_filters).toEqual([
            { type: "TEXT_MATCH", value: ["mission"], max_hops: 2 },
            {
                type: "TEXT_MATCH",
                value: ["adobe"],
                datatype: "reference",
                max_hops: 2,
            },
        ]);
    });

    it("sends plain terms without a datatype restriction", () => {
        const body = buildSearchApiRequestBody({
            terms: [
                { type: "string", text: "mission", inverted: false },
                { type: "string", text: "church", inverted: false },
            ],
            graphIds: [],
            mapFilter: null,
        });

        expect(body.node_agnostic_filters).toEqual([
            { type: "TEXT_MATCH", value: ["mission", "church"], max_hops: 2 },
        ]);
    });

    it("sends a date range as a DATE_RANGE entry", () => {
        const body = buildSearchApiRequestBody({
            terms: [],
            graphIds: [],
            mapFilter: null,
            dateRange: { from: "1900-01-01", to: "1950-12-31" },
        });

        expect(body.node_agnostic_filters).toEqual([
            {
                type: "DATE_RANGE",
                value: { from: "1900-01-01", to: "1950-12-31" },
                max_hops: 0,
            },
        ]);
    });

    it("sends null filters when nothing is filtered", () => {
        const body = buildSearchApiRequestBody({
            terms: [],
            graphIds: [],
            mapFilter: null,
        });

        expect(body.node_agnostic_filters).toBeNull();
    });
});
