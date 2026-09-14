import { describe, expect, it } from "vitest";

import { buildSearchApiRequestBody } from "@/arches_search/SimpleSearch/utils/search-payload-builder.ts";
import { TERM_KIND_CONTROLLED_TERM } from "@/arches_search/SimpleSearch/types.ts";

const GRAPH_SLUGS = ["heritage_resource"];

describe("buildSearchApiRequestBody", () => {
    it("restricts controlled terms to reference-datatype values", () => {
        const body = buildSearchApiRequestBody({
            terms: [
                { type: "string", text: "mission", inverted: false },
                {
                    type: TERM_KIND_CONTROLLED_TERM,
                    text: "adobe",
                    inverted: false,
                },
            ],
            graphSlugs: GRAPH_SLUGS,
            mapFilter: null,
        });

        expect(body.term_search).toEqual({
            terms: ["mission", { text: "adobe", datatype: "reference" }],
            max_hops: 2,
        });
    });

    it("sends plain terms as strings", () => {
        const body = buildSearchApiRequestBody({
            terms: [
                { type: "string", text: "mission", inverted: false },
                { type: "string", text: "church", inverted: false },
            ],
            graphSlugs: GRAPH_SLUGS,
            mapFilter: null,
        });

        expect(body.term_search).toEqual({
            terms: ["mission", "church"],
            max_hops: 2,
        });
    });

    it("sends no term search when there are no terms", () => {
        const body = buildSearchApiRequestBody({
            terms: [],
            graphSlugs: GRAPH_SLUGS,
            mapFilter: null,
        });

        expect(body.term_search).toBeNull();
    });
});
