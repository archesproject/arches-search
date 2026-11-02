import { describe, expect, it } from "vitest";

import {
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import { buildNodeDateSearchClause } from "@/arches_search/AdvancedSearch/utils/advanced-search-payload-builder.ts";
import { buildSearchApiRequestBody } from "@/arches_search/SimpleSearch/utils/search-payload-builder.ts";
import { TERM_KIND_CONTROLLED_TERM } from "@/arches_search/SimpleSearch/types.ts";

import type { FeatureCollection } from "geojson";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const GRAPH_SLUGS = ["heritage_resource"];

function buildQueryForGraph(graphSlug: string): GroupPayload {
    return {
        graph_slug: graphSlug,
        scope: GraphScopeToken.RESOURCE,
        logic: LogicToken.AND,
        clauses: [
            buildNodeDateSearchClause(
                graphSlug,
                "construction_date",
                "BETWEEN",
                "1900-01-01",
                "1950-12-31",
            ),
        ],
        groups: [],
        aggregations: [],
        relationship: null,
    };
}

const DRAWN_AREA: FeatureCollection = {
    type: "FeatureCollection",
    features: [
        {
            type: "Feature",
            properties: {},
            geometry: { type: "Point", coordinates: [0, 0] },
        },
    ],
};

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

    it("sends the given max hops", () => {
        const body = buildSearchApiRequestBody({
            terms: [{ type: "string", text: "mission", inverted: false }],
            graphSlugs: GRAPH_SLUGS,
            mapFilter: null,
            maxHops: 0,
        });

        expect(body.term_search).toEqual({
            terms: ["mission"],
            max_hops: 0,
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

describe("buildSearchApiRequestBody advanced search queries", () => {
    const heritageQuery = buildQueryForGraph("heritage_resource");
    const personQuery = buildQueryForGraph("person");

    it("sends each graph's query as that graph's payload", () => {
        const body = buildSearchApiRequestBody({
            terms: [],
            queries: [heritageQuery, personQuery],
            graphSlugs: ["heritage_resource", "person"],
            mapFilter: null,
        });

        expect(body.advanced_search_queries).toEqual([
            heritageQuery,
            personQuery,
        ]);
    });

    it("nests each graph's query beside the clauses repeated per graph", () => {
        const body = buildSearchApiRequestBody({
            terms: [],
            queries: [personQuery],
            graphSlugs: ["heritage_resource", "person"],
            mapFilter: DRAWN_AREA,
        });

        const payloads = body.advanced_search_queries as GroupPayload[];
        expect(payloads.map((payload) => payload.graph_slug)).toEqual([
            "heritage_resource",
            "person",
        ]);
        expect(payloads[0].groups).toEqual([]);
        expect(payloads[1].groups).toEqual([personQuery]);
        expect(payloads[1].clauses).toHaveLength(1);
    });

    it("still takes a single query", () => {
        const body = buildSearchApiRequestBody({
            terms: [],
            query: heritageQuery,
            graphSlugs: GRAPH_SLUGS,
            mapFilter: null,
        });

        expect(body.advanced_search_queries).toEqual([heritageQuery]);
    });

    it("sends no advanced search queries when there is nothing to filter", () => {
        const body = buildSearchApiRequestBody({
            terms: [],
            queries: [],
            graphSlugs: GRAPH_SLUGS,
            mapFilter: null,
        });

        expect(body.advanced_search_queries).toBeNull();
    });
});
