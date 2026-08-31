import { parseSearchDefinition } from "@/arches_search/SimpleSearch/utils/search-definition.ts";
import { TERM_FILTER_KEY } from "@/arches_search/SimpleSearch/types.ts";

import type { FeatureCollection } from "geojson";
import type { PendingSearch } from "@/arches_search/stores/usePendingSearchStore.ts";
import type {
    ResourceType,
    SearchDefinition,
    TermKind,
} from "@/arches_search/SimpleSearch/types.ts";

export interface PendingSearchActions {
    applySearchDefinition(definition: SearchDefinition): void;
    clearTermFilter(key: string): void;
    openMapFilter(): void;
    setGraphs(graphs: ResourceType[]): void;
    setMapFilter(featureCollection: FeatureCollection): void;
    setTermFilter(
        key: string,
        text: string,
        clear: () => void,
        options?: Record<string, unknown>,
        termKind?: TermKind,
        icon?: string,
    ): void;
}

export function applyPendingSearch(
    pendingSearch: PendingSearch,
    actions: PendingSearchActions,
): void {
    if (pendingSearch.searchDefinition !== undefined) {
        actions.applySearchDefinition(
            parseSearchDefinition(pendingSearch.searchDefinition),
        );
        return;
    }

    if (pendingSearch.term !== undefined) {
        const key = `${TERM_FILTER_KEY}:${pendingSearch.term}`;
        actions.setTermFilter(
            key,
            pendingSearch.term,
            () => actions.clearTermFilter(key),
            undefined,
            pendingSearch.termKind,
            pendingSearch.termIcon,
        );
    }

    if (pendingSearch.graphIds !== undefined) {
        actions.setGraphs(
            pendingSearch.graphIds.map((id) => ({ id, label: "", icon: "" })),
        );
    }

    if (pendingSearch.mapFilter !== undefined) {
        actions.setMapFilter(pendingSearch.mapFilter);
        actions.openMapFilter();
    }
}
