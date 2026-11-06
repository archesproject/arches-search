import { parseSearchDefinition } from "@/arches_search/SimpleSearch/utils/search-definition.ts";
import { TERM_FILTER_KEY } from "@/arches_search/SimpleSearch/types.ts";

import type { FeatureCollection } from "geojson";
import type { PendingSearch } from "@/arches_search/stores/usePendingSearchStore.ts";
import type {
    SearchDefinition,
    SerializedTerm,
} from "@/arches_search/SimpleSearch/types.ts";

export interface PendingSearchActions {
    applySearchDefinition(
        definition: SearchDefinition,
        searchName: string | null,
    ): void;
    clearAll(): void;
    openMapFilter(): void;
    setGraphsBySlug(graphSlugs: string[]): void;
    setMapFilter(featureCollection: FeatureCollection): void;
    setTermFilter(term: SerializedTerm): void;
}

// A pending search is a fresh start, so whatever was searched before goes.
export function applyPendingSearch(
    pendingSearch: PendingSearch,
    actions: PendingSearchActions,
): void {
    if (pendingSearch.searchDefinition !== undefined) {
        actions.applySearchDefinition(
            parseSearchDefinition(pendingSearch.searchDefinition),
            pendingSearch.searchName ?? null,
        );
        return;
    }

    actions.clearAll();

    if (pendingSearch.term !== undefined) {
        const term: SerializedTerm = {
            id: `${TERM_FILTER_KEY}:${pendingSearch.term}`,
            text: pendingSearch.term,
            inverted: false,
        };
        if (pendingSearch.termKind) {
            term.termKind = pendingSearch.termKind;
        }
        if (pendingSearch.termIcon) {
            term.icon = pendingSearch.termIcon;
        }
        actions.setTermFilter(term);
    }

    if (pendingSearch.graphSlugs !== undefined) {
        actions.setGraphsBySlug(pendingSearch.graphSlugs);
    }

    if (pendingSearch.mapFilter !== undefined) {
        actions.setMapFilter(pendingSearch.mapFilter);
        actions.openMapFilter();
    }
}
