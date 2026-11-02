import { isEqual } from "es-toolkit";

import {
    RESULTS_SORT_A_TO_Z,
    RESULTS_SORT_NEWEST,
    RESULTS_SORT_OLDEST,
    RESULTS_SORT_RELEVANCE,
    RESULTS_SORT_Z_TO_A,
} from "@/arches_search/SimpleSearch/types.ts";

import type {
    ResultsSortValue,
    SortSpec,
} from "@/arches_search/SimpleSearch/types.ts";

const SORT_VALUES_WITH_SPECS: ResultsSortValue[] = [
    RESULTS_SORT_A_TO_Z,
    RESULTS_SORT_Z_TO_A,
    RESULTS_SORT_NEWEST,
    RESULTS_SORT_OLDEST,
];

export function sortSpecForValue(value: ResultsSortValue | null): SortSpec[] {
    switch (value) {
        case RESULTS_SORT_A_TO_Z:
            return [{ type: "primary_name", direction: "asc" }];
        case RESULTS_SORT_Z_TO_A:
            return [{ type: "primary_name", direction: "desc" }];
        case RESULTS_SORT_NEWEST:
            return [{ type: "created_time", direction: "desc" }];
        case RESULTS_SORT_OLDEST:
            return [{ type: "created_time", direction: "asc" }];
        default:
            return [];
    }
}

export function sortValueForSpecs(specs: SortSpec[]): ResultsSortValue {
    const matchingValue = SORT_VALUES_WITH_SPECS.find((candidate) =>
        isEqual(sortSpecForValue(candidate), specs),
    );
    return matchingValue ?? RESULTS_SORT_RELEVANCE;
}
