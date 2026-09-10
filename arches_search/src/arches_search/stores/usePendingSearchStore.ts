import { cloneDeep } from "es-toolkit";
import { defineStore } from "pinia";

import type { FeatureCollection } from "geojson";
import type { TermKind } from "@/arches_search/SimpleSearch/types.ts";

export interface PendingSearch {
    searchDefinition?: Record<string, unknown>;
    term?: string;
    termKind?: TermKind;
    termIcon?: string;
    graphIds?: string[];
    mapFilter?: FeatureCollection;
}

export const usePendingSearchStore = defineStore(
    "arches_search:pendingSearch",
    () => {
        let pendingSearch: PendingSearch | null = null;

        function set(next: PendingSearch): void {
            pendingSearch = cloneDeep(next);
        }

        function consume(): PendingSearch | null {
            const current = pendingSearch;
            pendingSearch = null;
            return current;
        }

        function clear(): void {
            pendingSearch = null;
        }

        return { set, consume, clear };
    },
);
