import { describe, expect, it } from "vitest";

import {
    sortDirectionForSpecs,
    sortFieldForSpecs,
    sortSpecForField,
} from "@/arches_search/SimpleSearch/utils/results-sort.ts";
import {
    RESULTS_SORT_CREATED_TIME,
    RESULTS_SORT_NAME,
    RESULTS_SORT_NODE_PREFIX,
} from "@/arches_search/SimpleSearch/types.ts";

import type {
    ResultsSortDirection,
    ResultsSortField,
} from "@/arches_search/SimpleSearch/types.ts";

describe("results sort", () => {
    it("maps each sort field and direction to its sort spec and back", () => {
        const sortFields: ResultsSortField[] = [
            RESULTS_SORT_NAME,
            RESULTS_SORT_CREATED_TIME,
            `${RESULTS_SORT_NODE_PREFIX}name`,
        ];
        const sortDirections: ResultsSortDirection[] = ["asc", "desc"];
        for (const field of sortFields) {
            for (const direction of sortDirections) {
                const specs = sortSpecForField(field, direction, "person");
                expect(sortFieldForSpecs(specs)).toBe(field);
                expect(sortDirectionForSpecs(specs)).toBe(direction);
            }
        }
    });
});
