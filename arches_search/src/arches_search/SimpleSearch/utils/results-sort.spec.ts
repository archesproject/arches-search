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
    RESULTS_SORT_RELEVANCE,
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

    it("sorts on a node within the given resource model", () => {
        expect(
            sortSpecForField(
                `${RESULTS_SORT_NODE_PREFIX}name`,
                "desc",
                "person",
            ),
        ).toEqual([
            {
                type: "NODE",
                graph_slug: "person",
                node_alias: "name",
                direction: "desc",
            },
        ]);
    });

    it("drops a node sort when no resource model is given", () => {
        expect(
            sortSpecForField(`${RESULTS_SORT_NODE_PREFIX}name`, "asc", null),
        ).toEqual([]);
    });

    it("treats no sort spec as relevance", () => {
        expect(sortSpecForField(RESULTS_SORT_RELEVANCE, "asc", null)).toEqual(
            [],
        );
        expect(sortSpecForField(null, "asc", null)).toEqual([]);
        expect(sortFieldForSpecs([])).toBe(RESULTS_SORT_RELEVANCE);
        expect(sortDirectionForSpecs([])).toBe("asc");
    });
});
