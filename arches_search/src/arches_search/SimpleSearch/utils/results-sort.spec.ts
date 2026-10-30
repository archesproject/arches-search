import { describe, expect, it } from "vitest";

import {
    sortSpecForValue,
    sortSpecsMatch,
    sortValueForSpecs,
} from "@/arches_search/SimpleSearch/utils/results-sort.ts";
import {
    RESULTS_SORT_A_TO_Z,
    RESULTS_SORT_NEWEST,
    RESULTS_SORT_OLDEST,
    RESULTS_SORT_RELEVANCE,
    RESULTS_SORT_Z_TO_A,
} from "@/arches_search/SimpleSearch/types.ts";

import type { ResultsSortValue } from "@/arches_search/SimpleSearch/types.ts";

describe("results sort", () => {
    it("maps each sort choice to its sort spec and back", () => {
        const sortValues: ResultsSortValue[] = [
            RESULTS_SORT_A_TO_Z,
            RESULTS_SORT_Z_TO_A,
            RESULTS_SORT_NEWEST,
            RESULTS_SORT_OLDEST,
        ];
        for (const value of sortValues) {
            expect(sortValueForSpecs(sortSpecForValue(value))).toBe(value);
        }
    });

    it("treats no sort spec as relevance", () => {
        expect(sortSpecForValue(RESULTS_SORT_RELEVANCE)).toEqual([]);
        expect(sortSpecForValue(null)).toEqual([]);
        expect(sortValueForSpecs([])).toBe(RESULTS_SORT_RELEVANCE);
    });

    it("treats a sort spec it does not offer as relevance", () => {
        expect(
            sortValueForSpecs([
                {
                    type: "NODE",
                    graph_slug: "person",
                    node_alias: "name",
                    direction: "asc",
                },
            ]),
        ).toBe(RESULTS_SORT_RELEVANCE);
    });

    it("compares sort specs by value", () => {
        expect(
            sortSpecsMatch(sortSpecForValue(RESULTS_SORT_A_TO_Z), [
                { type: "primary_name", direction: "asc" },
            ]),
        ).toBe(true);
        expect(
            sortSpecsMatch(
                sortSpecForValue(RESULTS_SORT_A_TO_Z),
                sortSpecForValue(RESULTS_SORT_Z_TO_A),
            ),
        ).toBe(false);
    });
});
